"""Local AI connections. API tokens live only in the operating system keychain."""

import ipaddress
import http.client
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import ssl
from pathlib import Path
from urllib import error, parse, request

import keyring


SCHEMAS = Path(__file__).parent / "schemas"
KEYRING_SERVICE = "python-quest"
CLI = {"codex": "Codex CLI", "claude": "Claude CLI", "opencode": "OpenCode CLI"}
API = {"openai": ("OpenAI API", "https://api.openai.com/v1"),
       "anthropic": ("Anthropic API", "https://api.anthropic.com/v1"),
       "ollama": ("Ollama Cloud", "https://ollama.com/v1"),
       "openrouter": ("OpenRouter", "https://openrouter.ai/api/v1")}
RESPONSE_LIMIT = 2 * 1024 * 1024
REQUEST_TIMEOUT = 120


class ProviderError(RuntimeError):
    pass


def settings(state):
    ai = state.setdefault("ai", {"connections": [], "selection": {"id": "codex", "model": "gpt-6-luna"}})
    ai.setdefault("usage", {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0, "calls": 0})
    return ai


def record_usage(ai, usage):
    if not isinstance(usage, dict):
        return
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
    if not all(type(value) is int and value >= 0 for value in (input_tokens, output_tokens)):
        return
    details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
    cached = usage.get("cached_input_tokens", usage.get("cache_read_input_tokens", details.get("cached_tokens", 0)))
    cached = cached if type(cached) is int and 0 <= cached <= input_tokens else 0
    totals = ai.setdefault("usage", {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0, "calls": 0})
    totals["input_tokens"] += input_tokens
    totals["output_tokens"] += output_tokens
    totals["cached_input_tokens"] += cached
    totals["calls"] += 1


def validate_model(model):
    if not isinstance(model, str) or not 1 <= len(model) <= 100 or model.startswith("-") or any(ord(c) < 33 or ord(c) > 126 for c in model):
        raise ValueError("Escribe un identificador de modelo válido.")
    return model


def validate_endpoint(value):
    if not isinstance(value, str) or len(value) > 250:
        raise ValueError("Escribe una URL HTTPS válida.")
    url = parse.urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment or url.port not in (None, 443):
        raise ValueError("La URL debe usar HTTPS público, sin usuario, parámetros ni puerto especial.")
    host = url.hostname.rstrip(".")
    if host == "localhost" or host.endswith(".localhost") or "." not in host:
        raise ValueError("El servidor debe ser público.")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("El servidor debe usar direcciones públicas.")
    except OSError as exc:
        raise ValueError("No se pudo verificar el servidor.") from exc
    return value.rstrip("/")


def save_token(connection_id, token):
    if not isinstance(token, str) or not token.strip() or len(token) > 1000:
        raise ValueError("Escribe una clave API válida.")
    try:
        keyring.set_password(KEYRING_SERVICE, connection_id, token.strip())
    except Exception as exc:
        raise ProviderError("No se pudo guardar la clave en el llavero del sistema.") from exc


def token_for(connection_id):
    try:
        token = keyring.get_password(KEYRING_SERVICE, connection_id)
    except Exception as exc:
        raise ProviderError("No se pudo abrir el llavero del sistema.") from exc
    if not token:
        raise ProviderError("Falta la clave API en el llavero. Vuelve a conectar el proveedor.")
    return token


def connection(ai, connection_id):
    if connection_id in CLI:
        return {"id": connection_id, "kind": "cli", "label": CLI[connection_id]}
    return next((item for item in ai["connections"] if item["id"] == connection_id), None)


def cli_path(name):
    installed = shutil.which(name)
    if installed:
        return installed
    for directory in (Path.home() / ".local/bin", Path.home() / ".opencode/bin"):
        path = directory / name
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def public_settings(ai):
    return {"selection": ai["selection"], "connections": [
        *({"id": name, "kind": "cli", "label": label, "available": bool(cli_path(name))}
          for name, label in CLI.items()), *ai["connections"]]}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError("El servidor intentó redirigir la petición.")


class PublicHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        timeout = self.timeout if isinstance(self.timeout, (int, float)) else REQUEST_TIMEOUT
        deadline = getattr(self, 'deadline', time.monotonic() + timeout)
        if time.monotonic() >= deadline:
            raise TimeoutError('Tiempo de conexión agotado.')
        addresses = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ProviderError("El servidor debe usar direcciones públicas.")

        def pinned_connection(address, timeout, source_address=None):
            # Use the validated sockaddr directly; never resolve the hostname a second time.
            for family, kind, protocol, _, sockaddr in addresses:
                if time.monotonic() >= deadline:
                    raise TimeoutError('Tiempo de conexión agotado.')
                transport = socket.socket(family, kind, protocol)
                transport.settimeout(max(0.001, deadline - time.monotonic()))
                self.transport = transport
                try:
                    transport.connect(sockaddr)
                    transport.settimeout(max(0.001, deadline - time.monotonic()))
                    return transport
                except OSError as exc:
                    transport.close()
                    failure = exc
                    if time.monotonic() >= deadline:
                        break
            raise failure

        self._create_connection = pinned_connection
        super().connect()
        self.transport = self.sock


class PublicHTTPSHandler(request.HTTPSHandler):
    def __init__(self, connections):
        super().__init__(context=ssl.create_default_context())
        self.connections = connections
        self.deadline = time.monotonic() + REQUEST_TIMEOUT

    def https_open(self, req):
        def connection(host, **kwargs):
            value = PublicHTTPSConnection(host, **kwargs)
            value.deadline = self.deadline
            self.connections.append(value)
            return value
        return self.do_open(connection, req, context=self._context)


def http_json(url, token, provider, payload=None):
    try:
        validate_endpoint(url)
    except ValueError as exc:
        raise ProviderError(str(exc)) from exc
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if provider == "anthropic":
        headers.update({"x-api-key": token, "anthropic-version": "2023-06-01"})
    else:
        headers["Authorization"] = f"Bearer {token}"
    call = request.Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    connections = []
    expired = threading.Event()

    def stop_connection():
        expired.set()
        for connection in connections:
            transport = getattr(connection, "transport", None)
            if transport is not None:
                try:
                    transport.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                transport.close()

    timer = threading.Timer(REQUEST_TIMEOUT, stop_connection)
    try:
        # Proxies can resolve names independently, so do not use environment proxy settings.
        opener = request.build_opener(request.ProxyHandler({}), PublicHTTPSHandler(connections), NoRedirect)
        timer.start()
        with opener.open(call, timeout=REQUEST_TIMEOUT) as response:
            body = response.read(RESPONSE_LIMIT + 1)
            if expired.is_set():
                raise ProviderError("La IA tardó demasiado. Inténtalo de nuevo.")
            if len(body) > RESPONSE_LIMIT:
                raise ProviderError("La respuesta del proveedor supera el tamaño permitido.")
            return json.loads(body)
    except error.HTTPError as exc:
        raise ProviderError(f"El proveedor rechazó la petición (HTTP {exc.code}). Revisa la clave y el modelo.") from exc
    except (OSError, ValueError, RecursionError, http.client.HTTPException) as exc:
        raise ProviderError("No se pudo conectar o leer la respuesta del proveedor.") from exc
    finally:
        timer.cancel()


def run_cli(command, *, input=None, timeout=REQUEST_TIMEOUT, **kwargs):
    """Bound provider output on disk before loading it into memory."""
    if kwargs.get('text'):
        kwargs.setdefault('encoding', 'utf-8')
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        with subprocess.Popen(command, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                              stdout=stdout, stderr=stderr, **kwargs) as process:
            finished = threading.Event()
            oversized = threading.Event()

            def limit_output():
                while not finished.wait(0.02):
                    if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > RESPONSE_LIMIT:
                        oversized.set()
                        process.kill()
                        return

            watcher = threading.Thread(target=limit_output, daemon=True)
            watcher.start()
            try:
                process.communicate(input=input, timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise
            finally:
                finished.set()
                watcher.join()
            if oversized.is_set() or os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > RESPONSE_LIMIT:
                raise ProviderError("La respuesta del proveedor supera el tamaño permitido.")
            stdout.seek(0)
            return subprocess.CompletedProcess(command, process.returncode, stdout.read(RESPONSE_LIMIT).decode('utf-8'))


def cli_models(name):
    command = (["codex", "app-server"] if name == "codex" else
               ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json",
                "--verbose", "--no-session-persistence", "--tools", ""])
    failure = f"No se pudo consultar los modelos de {CLI[name]}. Revisa su sesión o actualiza la CLI; también puedes escribir el ID manualmente."
    command[0] = cli_path(name)
    if not command[0]:
        raise ProviderError(failure)
    try:
        with tempfile.TemporaryDirectory() as directory, subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, encoding="utf-8", cwd=directory) as process:
            timer = threading.Timer(20, process.kill)
            timer.start()
            try:
                def send(message):
                    process.stdin.write(json.dumps(message) + "\n")
                    process.stdin.flush()

                def receive(request_id):
                    total = 0
                    while True:
                        line = process.stdout.readline(RESPONSE_LIMIT + 1)
                        if not line:
                            break
                        total += len(line.encode('utf-8'))
                        if total > RESPONSE_LIMIT:
                            raise ProviderError("La respuesta del proveedor supera el tamaño permitido.")
                        message = json.loads(line)
                        if name == "codex" and message.get("id") == request_id:
                            if "error" in message:
                                raise ProviderError(failure)
                            return message["result"]
                        if name == "claude" and message.get("type") == "control_response":
                            response = message["response"]
                            if response.get("request_id") == request_id:
                                if response.get("subtype") != "success":
                                    raise ProviderError(failure)
                                return response["response"]
                    raise ProviderError(failure)

                if name == "claude":
                    send({"type": "control_request", "request_id": "models",
                          "request": {"subtype": "initialize"}})
                    entries = receive("models")["models"]
                    identifiers = [entry["value"] for entry in entries]
                else:
                    send({"id": 1, "method": "initialize", "params": {
                        "clientInfo": {"name": "python_quest", "version": "1.0"}}})
                    receive(1)
                    send({"method": "initialized"})
                    identifiers, cursor, request_id = [], None, 2
                    while len(identifiers) < 500:
                        send({"id": request_id, "method": "model/list", "params": {
                            "limit": 100, "includeHidden": False, "cursor": cursor}})
                        page = receive(request_id)
                        identifiers.extend(entry["model"] for entry in page["data"] if not entry.get("hidden"))
                        next_cursor = page.get("nextCursor")
                        if not next_cursor:
                            break
                        if next_cursor == cursor:
                            raise ProviderError(failure)
                        cursor, request_id = next_cursor, request_id + 1
                return list(dict.fromkeys(validate_model(value) for value in identifiers))[:500]
            finally:
                timer.cancel()
                if process.poll() is None:
                    process.kill()
                process.wait()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ProviderError(failure) from exc


def models(ai, connection_id):
    item = connection(ai, connection_id)
    if not item:
        raise ValueError("La conexión no existe.")
    if item["kind"] == "cli":
        if connection_id in ("codex", "claude"):
            return cli_models(connection_id)
        try:
            result = run_cli([cli_path("opencode") or "opencode", "models"], text=True, timeout=20)
            return result.stdout.splitlines()[:200] if result.returncode == 0 else []
        except (OSError, subprocess.TimeoutExpired):
            return []
    if item["provider"] == "compatible":
        validate_endpoint(item["endpoint"])
    data = http_json(item["endpoint"] + "/models", token_for(connection_id), item["provider"])
    identifiers = {model["id"] for model in data.get("data", []) if isinstance(model, dict) and isinstance(model.get("id"), str)}
    if item["provider"] == "openrouter":
        identifiers = {value for value in identifiers if value.endswith(":free") or value == "openrouter/free"}
    return sorted(identifiers, key=lambda value: (value != "openrouter/free", value))[:500]


def ask(prompt, schema_name, ai):
    selected = ai["selection"]
    item = connection(ai, selected["id"])
    if not item:
        raise ProviderError("Selecciona una conexión de IA válida.")
    model = validate_model(selected["model"])
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    if item["kind"] == "cli":
        executable = cli_path(item["id"])
        if not executable:
            raise ProviderError(f"No encuentro {item['label']}. Instala e inicia sesión en su CLI.")
        if item["id"] == "codex":
            command = ["codex", "exec", "--json", "-m", model, "-c", "model_reasoning_effort=medium", "--sandbox", "read-only", "--ephemeral",
                       "--skip-git-repo-check", "--output-schema", str(SCHEMAS / schema_name), "-"]
        elif item["id"] == "claude":
            command = ["claude", "-p", "--no-session-persistence", "--tools", "", "--json-schema",
                       json.dumps(schema), "--output-format", "json", "--model", model]
        else:
            command = ["opencode", "run", "--pure", "--format", "json", "--model", model,
                       "--title", "Python Quest"]
        env = os.environ.copy()
        command[0] = executable
        if item["id"] == "opencode":
            env["OPENCODE_CONFIG_CONTENT"] = json.dumps({"permission": "deny", "share": "disabled"})
        try:
            with tempfile.TemporaryDirectory() as directory:
                result = run_cli(command, input=prompt, text=True,
                                        cwd=directory, timeout=120, env=env)
        except subprocess.TimeoutExpired as exc:
            raise ProviderError("La IA tardó demasiado. Inténtalo de nuevo.") from exc
        if result.returncode:
            raise ProviderError(f"{item['label']} no pudo responder. Revisa su sesión, conexión y modelo.")
        try:
            if item["id"] == "claude":
                data = json.loads(result.stdout)
                answer = data.get("structured_output") or json.loads(data["result"])
            elif item["id"] == "opencode":
                parts = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
                answer = json.loads("".join(part.get("part", {}).get("text", "") for part in parts if part.get("type") == "text"))
            else:
                events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
                completed = next((event for event in reversed(events) if event.get("type") == "turn.completed"), {})
                message = next(event["item"]["text"] for event in reversed(events)
                               if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message")
                answer = json.loads(message)
                record_usage(ai, completed.get("usage"))
        except (ValueError, KeyError, TypeError, StopIteration) as exc:
            raise ProviderError("La IA devolvió una respuesta inválida. Inténtalo de nuevo.") from exc
    else:
        token = token_for(item["id"])
        if item["provider"] == "compatible":
            try:
                validate_endpoint(item["endpoint"])
            except ValueError as exc:
                raise ProviderError(str(exc)) from exc
        if item["provider"] == "openai":
            data = http_json(item["endpoint"] + "/responses", token, "openai", {
                "model": model, "input": prompt, "store": False,
                "text": {"format": {"type": "json_schema", "name": "python_quest", "strict": True, "schema": schema}}})
            content = "".join(block.get("text", "") for output in data.get("output", [])
                              for block in output.get("content", []) if block.get("type") == "output_text")
        elif item["provider"] == "anthropic":
            data = http_json(item["endpoint"] + "/messages", token, "anthropic", {
                "model": model, "max_tokens": 8192, "messages": [{"role": "user", "content": prompt}]})
            content = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        else:
            payload = {"model": model, "messages": [
                {"role": "system", "content": "Devuelve solo un objeto JSON válido, sin markdown, que cumpla este esquema: " + json.dumps(schema)},
                {"role": "user", "content": prompt}]}
            # Ollama Cloud no admite salidas estructuradas; el esquema se incluye en el prompt.
            if item["provider"] != "ollama":
                payload["response_format"] = {"type": "json_object"}
            data = http_json(item["endpoint"] + "/chat/completions", token, item["provider"], payload)
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise ProviderError("La API devolvió una respuesta inválida. Inténtalo de nuevo.") from exc
        try:
            answer = json.loads(content)
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError("La API devolvió una respuesta inválida. Inténtalo de nuevo.") from exc
        record_usage(ai, data.get("usage"))
    if not isinstance(answer, dict):
        raise ProviderError("La IA devolvió un formato inesperado.")
    return answer
