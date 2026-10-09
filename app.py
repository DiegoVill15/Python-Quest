import os
import json
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, jsonify, render_template, request

from quest import grader, hero, service
from quest import providers
from quest.codex_teacher import TeacherError
from quest.store import Store


ROOT = Path(__file__).resolve().parent


def allowed_hosts():
    hosts = {"127.0.0.1", "localhost"}
    try:
        result = subprocess.run(["tailscale", "status", "--json"], capture_output=True,
                                text=True, timeout=2)
        if result.returncode == 0:
            status = json.loads(result.stdout)
            if status.get("BackendState") == "Running":
                hosts.update(status.get("Self", {}).get("TailscaleIPs", []))
                hosts.add(status.get("Self", {}).get("DNSName", "").rstrip(".").lower())
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return hosts


def create_app(data_directory=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    store = Store(data_directory or ROOT / "data")
    hosts = allowed_hosts()

    @app.before_request
    def local_requests_only():
        host = (urlsplit("//" + request.host).hostname or "").lower().rstrip(".")
        if host not in hosts:
            hosts.update(allowed_hosts())
        if host not in hosts:
            return jsonify({"error": "Python Quest solo acepta conexiones locales o de tu Tailscale."}), 403
        if request.method in {"POST", "PUT", "DELETE"} and request.headers.get("X-Python-Quest") != "1":
            return jsonify({"error": "Petición no permitida."}), 403

    @app.after_request
    def private_responses(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/progress")
    def progress():
        return jsonify(service.overview(store))

    @app.put("/api/hero/name")
    def hero_name():
        payload = request.get_json(silent=True)
        try:
            hero.rename(store, payload.get("name") if isinstance(payload, dict) else None)
            return jsonify(service.overview(store))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.put("/api/hero/appearance")
    def hero_appearance():
        payload = request.get_json(silent=True)
        try:
            hero.change_appearance(store, payload.get("appearance") if isinstance(payload, dict) else None)
            return jsonify(service.overview(store))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.post("/api/hero/purchase")
    def hero_purchase():
        payload = request.get_json(silent=True)
        try:
            hero.purchase(store, payload.get("item_id") if isinstance(payload, dict) else None)
            return jsonify(service.overview(store))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.put("/api/hero/equipment")
    def hero_equipment():
        payload = request.get_json(silent=True)
        try:
            hero.equip(store, payload.get("slot") if isinstance(payload, dict) else None,
                       payload.get("item_id") if isinstance(payload, dict) else None)
            return jsonify(service.overview(store))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/preferences", methods=["GET", "POST", "DELETE"])
    def preferences():
        state = store.load()
        memory = state["preferences"]
        if request.method == "POST":
            payload = request.get_json(silent=True)
            note = payload.get("note") if isinstance(payload, dict) else None
            if not isinstance(note, str) or not note.strip() or len(note) > 500:
                return jsonify({"error": "Escribe un comentario de hasta 500 caracteres."}), 400
            if sum(len(item) for item in memory["pending"]) + len(note) > 2_000:
                return jsonify({"error": "Hay comentarios pendientes. Se resumirán al crear la siguiente misión."}), 400
            memory["pending"].append(note.strip())
            store.save(state)
        elif request.method == "DELETE":
            memory.update({"summary": "", "pending": []})
            store.save(state)
        return jsonify(memory)

    @app.get("/api/ai")
    def ai_settings():
        return jsonify(providers.public_settings(store.load()["ai"]))

    @app.post("/api/ai/connections")
    def add_connection():
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Envía una conexión en formato JSON."}), 400
        kind = payload.get("provider")
        if kind not in {*providers.API, "compatible"}:
            return jsonify({"error": "Proveedor desconocido."}), 400
        try:
            endpoint = providers.API[kind][1] if kind in providers.API else providers.validate_endpoint(payload.get("endpoint"))
            label = payload.get("label") or (providers.API[kind][0] if kind in providers.API else "API compatible")
            if not isinstance(label, str) or not 1 <= len(label.strip()) <= 60:
                raise ValueError("Escribe un nombre de hasta 60 caracteres.")
            state = store.load()
            if len(state["ai"]["connections"]) >= 10:
                raise ValueError("Ya tienes diez conexiones. Elimina una antes de añadir otra.")
            from uuid import uuid4
            connection_id = uuid4().hex
            providers.save_token(connection_id, payload.get("token"))
            state["ai"]["connections"].append({"id": connection_id, "kind": "api", "provider": kind,
                                               "label": label.strip(), "endpoint": endpoint})
            store.save(state)
            return jsonify(providers.public_settings(state["ai"])), 201
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except providers.ProviderError as error:
            return jsonify({"error": str(error)}), 503

    @app.delete("/api/ai/connections/<connection_id>")
    def delete_connection(connection_id):
        state = store.load()
        ai = state["ai"]
        item = next((item for item in ai["connections"] if item["id"] == connection_id), None)
        if not item:
            return jsonify({"error": "Conexión no encontrada."}), 404
        try:
            providers.keyring.delete_password(providers.KEYRING_SERVICE, connection_id)
        except providers.keyring.errors.PasswordDeleteError:
            pass
        except Exception:
            return jsonify({"error": "No se pudo borrar la clave del llavero."}), 503
        ai["connections"].remove(item)
        if ai["selection"]["id"] == connection_id:
            ai["selection"] = {"id": "codex", "model": "gpt-6-luna"}
        store.save(state)
        return jsonify(providers.public_settings(ai))

    @app.get("/api/ai/connections/<connection_id>/models")
    def ai_models(connection_id):
        try:
            return jsonify({"models": providers.models(store.load()["ai"], connection_id)})
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except providers.ProviderError as error:
            return jsonify({"error": str(error)}), 503

    @app.put("/api/ai/selection")
    def select_ai():
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Envía una selección en formato JSON."}), 400
        state = store.load()
        if not providers.connection(state["ai"], payload.get("id")):
            return jsonify({"error": "Selecciona una conexión válida."}), 400
        try:
            model = providers.validate_model(payload.get("model"))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        state["ai"]["selection"] = {"id": payload["id"], "model": model}
        store.save(state)
        return jsonify(providers.public_settings(state["ai"]))

    @app.post("/api/challenges")
    def challenge():
        payload = request.get_json(silent=True) or {}
        try:
            return jsonify(service.make_challenge(store, payload.get("world_id")))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except TeacherError as error:
            return jsonify({"error": str(error)}), 503

    @app.get("/api/challenges/<challenge_id>")
    def get_challenge(challenge_id):
        state = store.load()
        item = state["challenges"].get(challenge_id)
        if not item:
            return jsonify({"error": "Reto no encontrado"}), 404
        return jsonify(service.public_challenge(item, state))

    @app.post("/api/worlds/<world_id>/reset")
    def reset_world(world_id):
        try:
            return jsonify(service.reset_world(store, world_id))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.post("/api/challenges/<challenge_id>/submit")
    def submit(challenge_id):
        payload = request.get_json(silent=True) or {}
        try:
            return jsonify(service.submit(store, challenge_id, payload.get("source")))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.post("/api/run")
    def run_code():
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Envía código y entrada en formato JSON."}), 400
        source, stdin = payload.get("source"), payload.get("stdin", "")
        if not isinstance(source, str) or not source.strip() or len(source) > 20_000:
            return jsonify({"error": "Escribe código de hasta 20 000 caracteres."}), 400
        if not isinstance(stdin, str) or len(stdin) > 2_000:
            return jsonify({"error": "La entrada debe tener hasta 2 000 caracteres."}), 400
        try:
            compile(source, "solucion.py", "exec")
        except SyntaxError as error:
            return jsonify({"stdout": "", "error": f"Línea {error.lineno}: {error.msg}", "timed_out": False})
        return jsonify(grader.run_one(source, stdin))

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    create_app().run(host="127.0.0.1", port=port, debug=False, threaded=False)
