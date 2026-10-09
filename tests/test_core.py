import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import allowed_hosts, create_app
from quest import codex_teacher, grader, providers, service
from quest.curriculum import CURRICULUM, LESSONS, STAGES, STAGES_PER_WORLD, WORLDS, source_fits_stage
from quest.store import Store


REFERENCE = "n = int(input())\nprint(n * 2)\n"
TESTS = [{"input": f"{number}\n", "expected": f"{number * 2}\n"} for number in range(1, 7)]
GENERATED = {
    "title": "Dobla la energía", "story": "Una nave necesita energía.",
    "objective": "Lee un número y duplica su energía.",
    "input_format": "Una línea con un entero.",
    "output_format": "Una línea con el doble del número.",
    "rules": ["No añadas texto extra."],
    "hint": "Usa int(input()).", "preference_summary": "", "reference_solution": REFERENCE, "tests": TESTS,
}
REVIEW = {"note": "Revisa la multiplicación.", "improvement": "Usa una variable clara.", "weakness": "operadores"}


class QuestTests(unittest.TestCase):
    def test_recent_missions_distinguish_active_and_archived_challenges(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            state = store.load()
            for index in range(7):
                state["challenges"][str(index)] = {"id": str(index), "world_id": "fundamentos",
                                                  "title": f"Misión {index}"}
            state["campaign"]["runs"]["fundamentos"]["active_id"] = "6"
            store.save(state)
            client = create_app(directory).test_client()
            recent = client.get("/api/progress").json["recent"]
            self.assertEqual([item["id"] for item in recent], ["6", "5", "4", "3", "2"])
            self.assertEqual([item["can_submit"] for item in recent], [True, False, False, False, False])
            service.reset_world(store, "fundamentos")
            self.assertFalse(any(item["can_submit"] for item in client.get("/api/progress").json["recent"]))

    def test_ollama_and_openrouter_connections_models_and_answers(self):
        for provider, expected_endpoint in (("ollama", "https://ollama.com/v1"),
                                            ("openrouter", "https://openrouter.ai/api/v1")):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as directory, patch(
                    "quest.providers.keyring.set_password") as save_secret, patch(
                    "quest.providers.keyring.get_password", return_value="test-secret"), patch(
                    "quest.providers.http_json") as http:
                client = create_app(directory).test_client()
                client.environ_base["HTTP_X_PYTHON_QUEST"] = "1"
                response = client.post("/api/ai/connections", json={
                    "provider": provider, "token": "test-secret", "endpoint": "http://127.0.0.1/ignored"})
                self.assertEqual(response.status_code, 201)
                item = response.json["connections"][-1]
                self.assertEqual(item["endpoint"], expected_endpoint)
                save_secret.assert_called_once_with(providers.KEYRING_SERVICE, item["id"], "test-secret")
                self.assertNotIn("test-secret", Path(directory, "state.json").read_text())
                http.return_value = {"data": [{"id": "paid-model"}, {"id": "vendor/test:free"},
                                               {"id": "openrouter/free"}, {"id": "vendor/test:free"}, {}]}
                models = client.get(f"/api/ai/connections/{item['id']}/models")
                self.assertEqual(models.status_code, 200)
                self.assertEqual(models.json["models"], ["openrouter/free", "vendor/test:free"] if provider == "openrouter"
                                 else ["openrouter/free", "paid-model", "vendor/test:free"])
                self.assertEqual(http.call_args.args, (expected_endpoint + "/models", "test-secret", provider))
                selected = models.json["models"][0]
                self.assertEqual(client.put("/api/ai/selection", json={"id": item["id"], "model": selected}).status_code, 200)
                ai = Store(directory).load()["ai"]
                http.return_value = {"choices": [{"message": {"content": json.dumps(REVIEW)}}],
                                     "usage": {"prompt_tokens": 20, "completion_tokens": 5}}
                self.assertEqual(providers.ask("Revisa el intento", "review.json", ai), REVIEW)
                url, token, kind, payload = http.call_args.args
                self.assertEqual((url, token, kind), (expected_endpoint + "/chat/completions", "test-secret", provider))
                self.assertEqual(payload["model"], selected)
                self.assertIn('"required"', payload["messages"][0]["content"])
                self.assertEqual("response_format" in payload, provider != "ollama")
                self.assertEqual(ai["usage"]["input_tokens"], 20)
                for invalid in ({"choices": []}, {"choices": [{"message": {"content": "invalid JSON"}}]}):
                    http.return_value = invalid
                    with self.assertRaises(providers.ProviderError):
                        providers.ask("Revisa", "review.json", ai)

    def test_cli_model_discovery_protocols_and_failures(self):
        script = '''
import json, sys, time
provider, mode = sys.argv[1:]
if mode == "timeout":
    time.sleep(10)
for line in sys.stdin:
    request = json.loads(line)
    if provider == "claude":
        assert request["request"] == {"subtype": "initialize"}
        response = {"type": "control_response", "response": {
            "request_id": request["request_id"], "subtype": "success",
            "response": {"models": [{"value": "sonnet"}, {"value": "opus"}]}}}
    elif request["method"] == "initialize":
        response = {"id": request["id"], "result": {}}
    elif request["method"] == "initialized":
        continue
    else:
        assert request["method"] == "model/list"
        first = request["params"]["cursor"] is None
        response = {"id": request["id"], "result": {
            "data": [{"model": "first" if first else "second"},
                     {"model": "hidden", "hidden": True}, {"model": "first"}],
            "nextCursor": "page2" if first else None}}
    if mode == "error":
        response = ({"id": request["id"], "error": {"message": "Not authenticated"}}
                    if provider == "codex" else {"type": "control_response", "response": {
                        "request_id": request["request_id"], "subtype": "error"}})
    print(json.dumps({"type": "notification"}), flush=True)
    print(json.dumps(response), flush=True)
'''
        popen, timer = subprocess.Popen, providers.threading.Timer
        for name in ("codex", "claude"):
            for mode in ("success", "error", "timeout", "malformed"):
                with self.subTest(provider=name, mode=mode):
                    processes = []
                    def start(command, **kwargs):
                        self.assertEqual(command[:2], ["codex", "app-server"] if name == "codex" else ["claude", "-p"])
                        source = 'print("invalid JSON", flush=True)' if mode == "malformed" else script
                        process = popen([sys.executable, "-u", "-c", source, name, mode], **kwargs)
                        processes.append(process)
                        return process
                    with patch("quest.providers.cli_path", side_effect=lambda name: name), patch("quest.providers.subprocess.Popen", side_effect=start), patch(
                            "quest.providers.threading.Timer", side_effect=lambda delay, callback: timer(0.3, callback)):
                        if mode == "success":
                            self.assertEqual(providers.models({"connections": []}, name),
                                             ["first", "second"] if name == "codex" else ["sonnet", "opus"])
                        else:
                            with self.assertRaises(providers.ProviderError):
                                providers.models({"connections": []}, name)
                    self.assertIsNotNone(processes[0].poll())

    def test_cli_detection_without_login_shell_path(self):
        with tempfile.TemporaryDirectory() as directory, patch("quest.providers.Path.home", return_value=Path(directory)), patch("quest.providers.shutil.which", return_value=None):
            self.assertIsNone(providers.cli_path("claude"))
            binary = Path(directory, ".local/bin/claude")
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\n")
            binary.chmod(0o700)
            self.assertEqual(providers.cli_path("claude"), str(binary))

    def test_tailscale_host_is_allowed_without_opening_other_hosts(self):
        status = {"BackendState": "Running", "Self": {"TailscaleIPs": ["100.99.0.78"],
                  "DNSName": "mac.example.ts.net."}}
        with patch("app.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(status)
            self.assertIn("mac.example.ts.net", allowed_hosts())
        with tempfile.TemporaryDirectory() as directory, patch("app.allowed_hosts", return_value={"localhost", "127.0.0.1", "100.99.0.78", "mac.example.ts.net"}):
            client = create_app(directory).test_client()
            self.assertEqual(client.get("/", headers={"Host": "100.99.0.78:5000"}).status_code, 200)
            self.assertEqual(client.get("/", headers={"Host": "mac.example.ts.net:5000"}).status_code, 200)
            self.assertEqual(client.get("/", headers={"Host": "evil.example"}).status_code, 403)
        with tempfile.TemporaryDirectory() as directory, patch("app.allowed_hosts", side_effect=[
            {"localhost", "127.0.0.1"}, {"localhost", "127.0.0.1", "100.99.0.78"},
        ]):
            client = create_app(directory).test_client()
            self.assertEqual(client.get("/", headers={"Host": "100.99.0.78:5000"}).status_code, 200)

    def test_ai_selection_and_secret_storage(self):
        with tempfile.TemporaryDirectory() as directory, patch("quest.providers.keyring.set_password") as save_secret:
            client = create_app(directory).test_client()
            client.environ_base["HTTP_X_PYTHON_QUEST"] = "1"
            response = client.post("/api/ai/connections", json={"provider": "openai", "token": "secret-value"})
            self.assertEqual(response.status_code, 201)
            connection = response.json["connections"][-1]
            save_secret.assert_called_once_with("python-quest", connection["id"], "secret-value")
            self.assertNotIn("secret-value", Path(directory, "state.json").read_text())
            self.assertEqual(client.put("/api/ai/selection", json={"id": connection["id"], "model": "gpt-4o"}).status_code, 200)
            self.assertEqual(client.get("/api/ai").json["selection"]["model"], "gpt-4o")
            with patch("quest.providers.keyring.delete_password"):
                self.assertEqual(client.delete(f"/api/ai/connections/{connection['id']}").status_code, 200)
            self.assertEqual(client.get("/api/ai").json["selection"]["id"], "codex")

    def test_provider_dispatch_and_endpoint_validation(self):
        ai = {"connections": [], "selection": {"id": "claude", "model": "sonnet"}}
        response = json.dumps({"structured_output": {"note": "Bien", "improvement": "Sigue", "weakness": "ninguna"}})
        with patch("quest.providers.shutil.which", return_value="/usr/bin/claude"), patch("quest.providers.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = response
            self.assertEqual(providers.ask("Evalúa", "review.json", ai)["note"], "Bien")
            self.assertIn("--tools", run.call_args.args[0])
        for endpoint in ("http://example.com/v1", "https://localhost/v1", "https://127.0.0.1/v1"):
            with self.assertRaises(ValueError):
                providers.validate_endpoint(endpoint)

    def test_codex_uses_medium_and_records_reported_tokens(self):
        ai = {"connections": [], "selection": {"id": "codex", "model": "gpt-6-luna"}}
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(REVIEW)}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 40,
                                                 "output_tokens": 12, "reasoning_output_tokens": 0}},
        ]
        with patch("quest.providers.shutil.which", return_value="/usr/bin/codex"), patch("quest.providers.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "\n".join(json.dumps(event) for event in events)
            self.assertEqual(providers.ask("Revisa", "review.json", ai), REVIEW)
        self.assertIn("model_reasoning_effort=medium", run.call_args.args[0])
        self.assertIn("--json", run.call_args.args[0])
        self.assertEqual(ai["usage"], {"input_tokens": 100, "output_tokens": 12,
                                       "cached_input_tokens": 40, "calls": 1})

    def test_lesson_examples_match_their_output(self):
        for world in WORLDS:
            self.assertEqual(set(LESSONS[world["id"]]), set(range(1, len(STAGES[world["id"]]) + 1)))
        for world, stages in LESSONS.items():
            for stage, lesson in stages.items():
                with self.subTest(world=world, stage=stage):
                    for case in [lesson, *lesson.get("cases", [])]:
                        result = grader.run_one(lesson["code"], case["input"])
                        self.assertEqual(result["error"], "")
                        self.assertEqual(result["actual"], case["output"])
                    self.assertTrue(source_fits_stage(lesson["code"], world, stage))
        self.assertIn("range", LESSONS["bucles"][1]["code"])
        self.assertIn("while", LESSONS["bucles"][3]["code"])

    def test_curriculum_guards_and_expansion_migrate_existing_campaign(self):
        self.assertFalse(source_fits_stage("x = int(input())\nif x > 0: print(x)\nelse: print(0)", "condicionales", 1))
        self.assertFalse(source_fits_stage("d = {'sol': 1}\na = d\na[input()] = 2\nprint(d)", "diccionarios", 1))
        self.assertFalse(source_fits_stage("print(input().upper())", "fundamentos", 1))
        self.assertFalse(source_fits_stage("def f(x): return print(x)\nf(int(input()))", "funciones", 3))
        self.assertIn("fstring", CURRICULUM["fundamentos"][2]["introduced"])
        self.assertIn("values", CURRICULUM["diccionarios"][2]["introduced"])
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            state = store.load()
            state["campaign"]["runs"] = {world["id"]: {"completed": 5, "active_id": None} for world in WORLDS[:6]}
            state["campaign"]["unlocked"] = [world["id"] for world in WORLDS[:6]]
            state["campaign"]["awarded_stages"] = [f"{world['id']}:{stage}" for world in WORLDS[:6] for stage in range(1, 6)]
            state["campaign"].update(coins=15, xp_earned=900)
            state["hero"].update(owned=["aura"], equipped={"back": "aura"})
            store.save(state)
            upgraded = store.load()
            self.assertEqual(len(upgraded["campaign"]["runs"]), 9)
            self.assertIn("taller", upgraded["campaign"]["unlocked"])
            self.assertNotIn("rutas", upgraded["campaign"]["unlocked"])
            self.assertEqual(upgraded["campaign"]["coins"], 15)
            self.assertEqual(upgraded["hero"]["equipped"]["back"], "aura")
            self.assertEqual(store.progress()["completed"], 30)
            self.assertEqual(store.progress()["total_missions"], 45)
            self.assertFalse(store.progress()["campaign_complete"])
            store.save(upgraded)
            self.assertEqual(store.load()["campaign"], upgraded["campaign"])

    def test_grader_reports_correct_wrong_and_timeout(self):
        self.assertTrue(all(item["passed"] for item in grader.grade(REFERENCE, TESTS)))
        self.assertFalse(grader.grade("print(0)", TESTS)[0]["passed"])
        self.assertIn("Tiempo agotado", grader.run_one("while True: pass", "")["error"])
        self.assertIn("Salida demasiado extensa", grader.run_one("print('x' * 40000)", "")["error"])

    def test_manual_run_uses_no_ai_and_changes_no_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            client = create_app(directory).test_client()
            client.environ_base["HTTP_X_PYTHON_QUEST"] = "1"
            with patch("quest.codex_teacher.generate") as generate, patch("quest.codex_teacher.review") as review:
                response = client.post("/api/run", json={"source": REFERENCE, "stdin": "7\n"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["stdout"], "14\n")
            self.assertEqual(response.json["error"], "")
            generate.assert_not_called()
            review.assert_not_called()
            self.assertEqual(Store(directory).load()["attempts"], [])
            self.assertEqual(client.get("/api/progress").json["progress"]["xp"], 0)
            syntax = client.post("/api/run", json={"source": "if True\n    print(1)"})
            self.assertIn("Línea 1", syntax.json["error"])
            self.assertEqual(client.post("/api/run", json={"source": REFERENCE, "stdin": "a" * 2001}).status_code, 400)
            self.assertEqual(client.post("/api/run", json={"source": REFERENCE}, headers={"Host": "evil.test"}).status_code, 403)
            client.environ_base.pop("HTTP_X_PYTHON_QUEST")
            self.assertEqual(client.post("/api/run", json={"source": REFERENCE}).status_code, 403)

    def test_feedback_is_compacted_with_next_mission(self):
        with tempfile.TemporaryDirectory() as directory:
            client = create_app(directory).test_client()
            client.environ_base["HTTP_X_PYTHON_QUEST"] = "1"
            self.assertEqual(client.post("/api/preferences", json={"note": "Ejemplos más cortos"}).status_code, 200)
            self.assertEqual(client.post("/api/preferences", json={"note": "Prefiero ejemplos breves"}).status_code, 200)
            self.assertEqual(len(client.get("/api/preferences").json["pending"]), 2)
            generated = {**GENERATED, "preference_summary": "Usa ejemplos breves."}
            with patch("quest.codex_teacher.generate", return_value=generated) as generate:
                response = client.post("/api/challenges", json={"world_id": "fundamentos"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(generate.call_args.args[-3]["pending"]), 2)
            self.assertNotIn("preference_summary", response.json)
            self.assertEqual(client.get("/api/preferences").json,
                             {"summary": "Usa ejemplos breves.", "pending": []})
            self.assertNotIn("preference_summary", next(iter(Store(directory).load()["challenges"].values())))

    def test_challenge_submission_memory_and_rewards(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            with patch("quest.codex_teacher.generate", return_value=GENERATED), patch("quest.codex_teacher.review", return_value=REVIEW):
                challenge = service.make_challenge(store, "fundamentos")
                self.assertNotIn("reference_solution", challenge)
                self.assertNotIn("starter_code", challenge)
                self.assertEqual(len(challenge["examples"]), 2)
                self.assertEqual(challenge["stage"], 1)
                self.assertEqual(challenge["lesson"], LESSONS["fundamentos"][1])
                self.assertEqual(service.make_challenge(store, "fundamentos")["id"], challenge["id"])
                wrong = service.submit(store, challenge["id"], "print(0)")
                self.assertFalse(wrong["passed"])
                self.assertEqual(wrong["results"][0]["input"], TESTS[0]["input"])
                self.assertEqual(wrong["results"][0]["expected"], TESTS[0]["expected"])
                self.assertEqual(wrong["results"][0]["actual"], "0")
                self.assertEqual(wrong["results"][2]["input"], TESTS[2]["input"])
                self.assertEqual(wrong["results"][2]["expected"], TESTS[2]["expected"])
                self.assertEqual(wrong["results"][2]["actual"], "0")
                self.assertEqual(store.recent_errors("fundamentos")[0]["weakness"], "operadores")
                right = service.submit(store, challenge["id"], REFERENCE)
                self.assertTrue(right["passed"])
                self.assertEqual(right["coins_gained"], 10)
                self.assertEqual(store.load()["campaign"]["coins"], 10)
                self.assertEqual(service.public_challenge(store.load()["challenges"][challenge["id"]], store.load())["last_mistake"], REVIEW["note"])
                self.assertEqual(right["xp_gained"], 30)
                self.assertEqual(right["next_world_id"], "fundamentos")
                self.assertEqual(store.progress()["world_progress"]["fundamentos"]["stage"], 2)
                with self.assertRaisesRegex(ValueError, "ya no está activa"):
                    service.submit(store, challenge["id"], REFERENCE)
                service.reset_world(store, "fundamentos")
                self.assertEqual(store.progress()["xp"], 30)
                self.assertEqual(store.recent_errors("fundamentos")[0]["weakness"], "operadores")

    def test_syntax_error_skips_tests_and_ai(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            with patch("quest.codex_teacher.generate", return_value=GENERATED):
                challenge = service.make_challenge(store, "fundamentos")
            with patch("quest.codex_teacher.review") as review, patch("quest.service.grader.grade") as grade:
                result = service.submit(store, challenge["id"], "if True\n    print(1)")
            review.assert_not_called()
            grade.assert_not_called()
            self.assertTrue(result["syntax_error"])
            self.assertFalse(result["passed"])
            self.assertEqual(result["results"], [])
            self.assertIn("línea 1", result["review"]["note"])
            self.assertEqual(store.recent_errors("fundamentos")[0]["weakness"], "sintaxis")
            self.assertEqual(store.progress()["world_progress"]["fundamentos"]["active_id"], challenge["id"])
            with patch("quest.codex_teacher.review") as review, patch("quest.service.grader.grade") as grade:
                result = service.submit(store, challenge["id"], "return 1")
            review.assert_not_called()
            grade.assert_not_called()
            self.assertIn("outside function", result["review"]["note"])

    def test_rejects_inconsistent_generated_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            inconsistent = {**GENERATED, "tests": [{**TESTS[0], "expected": "999"}, *TESTS[1:]]}
            with patch("quest.codex_teacher.generate", return_value=inconsistent):
                with self.assertRaisesRegex(Exception, "consistente"):
                    service.make_challenge(Store(directory), "fundamentos")

    def test_replay_rejects_exact_duplicate_exercise(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            with patch("quest.codex_teacher.generate", return_value=GENERATED):
                service.make_challenge(store, "fundamentos")
            service.reset_world(store, "fundamentos")
            duplicate = {**GENERATED, "title": "Otro título"}
            with patch("quest.codex_teacher.generate", return_value=duplicate) as generate:
                with self.assertRaisesRegex(codex_teacher.TeacherError, "consistente"):
                    service.make_challenge(store, "fundamentos")
                self.assertEqual(generate.call_count, 3)
            self.assertIsNone(store.progress()["world_progress"]["fundamentos"]["active_id"])

    def test_replay_rejects_reused_public_example(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            with patch("quest.codex_teacher.generate", return_value=GENERATED):
                service.make_challenge(store, "fundamentos")
            service.reset_world(store, "fundamentos")
            repeated = {**GENERATED, "title": "Otra misión", "objective": "Calcula un resultado nuevo.",
                        "input_format": "Un valor de energía.", "output_format": "Su energía duplicada.",
                        "tests": [TESTS[0], *({"input": f"{n}\n", "expected": f"{n * 2}\n"} for n in range(7, 12))]}
            with patch("quest.codex_teacher.generate", return_value=repeated):
                with self.assertRaisesRegex(codex_teacher.TeacherError, "consistente"):
                    service.make_challenge(store, "fundamentos")

    def test_replay_rejects_same_input_and_output_format(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            with patch("quest.codex_teacher.generate", return_value=GENERATED):
                service.make_challenge(store, "fundamentos")
            service.reset_world(store, "fundamentos")
            repeated = {**GENERATED, "title": "Otra historia", "objective": "Calcula otra cosa.",
                        "tests": [{**test, "input": test["input"] + "\n"} for test in TESTS]}
            with patch("quest.codex_teacher.generate", return_value=repeated):
                with self.assertRaisesRegex(codex_teacher.TeacherError, "consistente"):
                    service.make_challenge(store, "fundamentos")

    def test_rejects_paraphrased_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            first = {**GENERATED, "input_format": "N L P por paso", "output_format": "Peso acumulado Piedras pesadas"}
            with patch("quest.codex_teacher.generate", return_value=first):
                service.make_challenge(store, "fundamentos")
            service.reset_world(store, "fundamentos")
            repeated = {**GENERATED, "title": "Otra misión", "objective": "Otro objetivo",
                        "input_format": "N L P por piedra", "output_format": "Carga aceptada Piedras aceptadas",
                        "tests": [{**test, "input": test["input"] + "\n"} for test in TESTS]}
            with patch("quest.codex_teacher.generate", return_value=repeated):
                with self.assertRaisesRegex(codex_teacher.TeacherError, "consistente"):
                    service.make_challenge(store, "fundamentos")

    def test_world_focus_and_private_tests(self):
        self.assertFalse(service.fits_world("def f(): return 1\nprint(f())", "fundamentos"))
        self.assertTrue(service.fits_world(REFERENCE, "fundamentos"))
        self.assertFalse(service.fits_world("print(sum([2, 3]))", "fundamentos", 4))
        self.assertTrue(service.fits_world("print(sum([2, 3]), len([2, 3]))", "fundamentos", 5))
        self.assertFalse(service.fits_world("print([2, 3][0])", "fundamentos", 5))
        self.assertTrue(service.fits_world("valores = input().split()\nprint(len(valores))", "listas", 5))
        self.assertTrue(service.fits_world("a = input().split()\nb = input().split()\nprint(a + b)", "listas", 5))
        self.assertFalse(service.fits_world("datos = {}\nfor _ in range(2):\n    clave = input()\n    datos[clave] = 1\nprint(datos[input()])", "diccionarios", 1))
        self.assertTrue(service.fits_world("datos = {'sol': 1}\nprint(datos[input()])", "diccionarios", 1))
        self.assertFalse(service.fits_world("print(1)", "funciones"))
        self.assertFalse(service.fits_world("import os\nos.system('echo x')", "fundamentos"))
        self.assertFalse(service.fits_world("a = int(input())\nif a > 1 and a < 4: print(a)", "condicionales", 4))
        self.assertTrue(service.fits_world("a = int(input())\nif (a > 1 and a < 4) or a == 7: print(a)", "condicionales", 4))
        self.assertFalse(service.fits_world("for _ in range(3):\n    x = int(input())\n    if x > 5: print(x)", "bucles", 4))
        self.assertTrue(service.fits_world("for _ in range(3):\n    x = int(input())\n    y = int(input())\n    if x > y: print(x)", "bucles", 4))
        with tempfile.TemporaryDirectory() as directory, patch("quest.codex_teacher.generate", return_value=GENERATED):
            client = create_app(directory).test_client()
            client.environ_base["HTTP_X_PYTHON_QUEST"] = "1"
            self.assertEqual(client.post("/api/challenges", json={"world_id": "condicionales"}).status_code, 400)
            response = client.post("/api/challenges", json={"world_id": "fundamentos"})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("reference_solution", response.json)
            self.assertNotIn("starter_code", response.json)
            self.assertNotIn("tests", response.json)
            self.assertEqual(len(response.json["examples"]), 2)
            self.assertEqual(client.get(f"/api/challenges/{response.json['id']}").json["objective"], GENERATED["objective"])
            reset = client.post("/api/worlds/fundamentos/reset")
            self.assertEqual(reset.status_code, 200)
            self.assertIsNone(reset.json["progress"]["world_progress"]["fundamentos"]["active_id"])

    def test_reviewer_receives_automatic_verdict(self):
        challenge = {**GENERATED, "tests": TESTS}
        with patch("quest.codex_teacher.ask_codex", return_value={}) as ask:
            codex_teacher.review(challenge, REFERENCE, grader.grade(REFERENCE, TESTS))
        prompt = ask.call_args.args[0]
        self.assertIn("CORRECTO: todas las pruebas pasaron", prompt)
        self.assertIn("Pruebas fallidas (las demás pasaron): []", prompt)
        self.assertIn(GENERATED["input_format"], prompt)
        self.assertIn("variable u operación", prompt)
        self.assertIn("sin Markdown, backticks", prompt)
        self.assertIn("Háblale de tú", prompt)

    def test_reviewer_uses_previous_failure_when_solution_passes(self):
        with patch("quest.codex_teacher.ask_codex", return_value={}) as ask:
            codex_teacher.review(GENERATED, REFERENCE, grader.grade(REFERENCE, TESTS), "Se intercambiaron gasto y saldo.")
        self.assertIn("Se intercambiaron gasto y saldo", ask.call_args.args[0])

    def test_next_mission_prompt_raises_difficulty_and_reinforces_error(self):
        previous = [{"stage": 3, "title": "El puente de los faroles", "objective": "Calcula el peso total",
                     "input_format": "Dos enteros", "output_format": "Dos líneas"}]
        errors = [{"title": "El puente de los faroles", "weakness": "salida", "note": "Faltó la unidad."}]
        with patch("quest.codex_teacher.ask_codex", return_value=GENERATED) as ask:
            codex_teacher.generate("fundamentos", 4, previous, errors,
                                   {"summary": "Ejemplos breves", "pending": ["Menos historia"]})
        prompt = ask.call_args.args[0]
        self.assertIn("división entera y resto", prompt)
        self.assertIn("Lección que verá el alumno", prompt)
        self.assertIn("No exijas métodos, funciones ni estructuras nuevos", prompt)
        self.assertIn("El puente de los faroles", prompt)
        self.assertIn("Faltó la unidad", prompt)
        self.assertIn("editor vacío", prompt)
        for key in ("allowed", "forbidden", "prerequisites", "common_mistakes", "input_spec", "hidden_must_include"):
            self.assertIn(key, prompt)
        self.assertIn("Ejemplos breves", prompt)
        self.assertIn("Menos historia", prompt)
        self.assertIn("preference_summary", prompt)

    def test_repeated_mechanic_is_rejected_then_revised(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            with patch("quest.codex_teacher.generate", return_value=GENERATED), patch("quest.codex_teacher.review", return_value=REVIEW):
                first = service.make_challenge(store, "fundamentos")
                service.submit(store, first["id"], REFERENCE)
            repeated = {**GENERATED, "title": "Otra fuente de energía", "objective": "Calcula el doble de otra cantidad.",
                        "input_format": "Una línea: energía disponible.", "output_format": "Una línea: energía resultante.",
                        "tests": [{**test, "input": test["input"] + "\n"} for test in TESTS]}
            addition_tests = [{"input": f"{n}\n{n + 1}\n", "expected": f"{2 * n + 1}\n"} for n in range(1, 7)]
            revised = {**GENERATED, "title": "Suma de dos reservas", "objective": "Suma dos reservas de energía.",
                       "input_format": "Línea 1: primera reserva. Línea 2: segunda reserva.",
                       "output_format": "Línea 1: suma de ambas reservas.",
                       "reference_solution": "a = int(input())\nb = int(input())\nprint(a + b)\n", "tests": addition_tests}
            verdicts = [{"novel": False, "reason": "Solo vuelve a duplicar un número; añade otra operación."},
                        {"novel": True, "reason": "Ahora suma dos entradas."}]
            with patch("quest.codex_teacher.generate", side_effect=[repeated, revised]) as generate, \
                 patch("quest.codex_teacher.check_novelty", side_effect=verdicts) as check:
                challenge = service.make_challenge(store, "fundamentos")
            self.assertEqual(challenge["title"], revised["title"])
            self.assertEqual(generate.call_count, 2)
            self.assertIn("Solo vuelve a duplicar", generate.call_args_list[1].args[-1])
            self.assertEqual(check.call_count, 2)
            self.assertEqual(check.call_args_list[0].args[0][0]["reference_solution"], REFERENCE)
            self.assertEqual(len(store.load()["challenges"]), 2)

    def test_campaign_unlock_reset_and_unique_rewards(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            total = len(WORLDS) * STAGES_PER_WORLD
            serial = iter(range(total + 1))
            def generate(_world, _stage, _titles, _errors, _preferences, _ai, _feedback):
                number = next(serial)
                prefix = f"{number}\n"
                tests = [{**test, "input": prefix + test["input"]} for test in TESTS]
                return {**GENERATED, "title": f"Misión {number}", "objective": f"{GENERATED['objective']} Etapa {number}.",
                        "input_format": chr(33 + number) * 100, "tests": tests}
            passed = [{"passed": True, "actual": "", "error": ""} for _ in TESTS]
            with patch("quest.codex_teacher.generate", side_effect=generate), patch("quest.codex_teacher.check_novelty", return_value={"novel": True, "reason": "Nueva operación."}), patch("quest.codex_teacher.review", return_value=REVIEW), patch("quest.service.fits_world", return_value=True), patch("quest.service.grader.grade", return_value=passed):
                for index, world in enumerate(WORLDS):
                    if index + 1 < len(WORLDS):
                        with self.assertRaisesRegex(ValueError, "desbloquear"):
                            service.make_challenge(store, WORLDS[index + 1]["id"])
                    for stage in range(1, 6):
                        challenge = service.make_challenge(store, world["id"])
                        self.assertEqual(challenge["stage"], stage)
                        result = service.submit(store, challenge["id"], REFERENCE)
                        self.assertEqual(result["xp_gained"], 30)
                        if stage == 5 and index + 1 < len(WORLDS):
                            self.assertEqual(result["next_world_id"], WORLDS[index + 1]["id"])
                self.assertTrue(store.progress()["campaign_complete"])
                self.assertEqual(store.progress()["completed"], total)
                self.assertEqual(store.progress()["xp"], total * 30)
                self.assertIsNone(result["next_world_id"])
                trophies_before_reset = store.progress()["trophies"]
                overview = service.reset_world(store, "fundamentos")
                self.assertEqual(overview["progress"]["world_progress"]["fundamentos"]["completed"], 0)
                self.assertTrue(overview["progress"]["world_progress"]["diccionarios"]["unlocked"])
                self.assertEqual(overview["progress"]["xp"], total * 30)
                self.assertEqual(overview["progress"]["completed"], total - 5)
                self.assertEqual(overview["progress"]["trophies"], trophies_before_reset)
                replay = service.make_challenge(store, "fundamentos")
                replay_result = service.submit(store, replay["id"], REFERENCE)
                self.assertEqual(replay_result["xp_gained"], 0)
                self.assertEqual(replay_result["coins_gained"], 0)
                self.assertEqual(store.progress()["xp"], total * 30)
                self.assertEqual(store.load()["campaign"]["coins"], total * 10)

    def test_hero_migration_purchase_equipment_and_name(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            state = store.load()
            state["campaign"]["awarded_stages"] = ["fundamentos:1", "fundamentos:2"]
            state["campaign"]["xp_earned"] = 60
            del state["campaign"]["coins"]
            del state["hero"]
            store.save(state)
            client = create_app(directory).test_client()
            client.environ_base["HTTP_X_PYTHON_QUEST"] = "1"
            overview = client.get("/api/progress").json
            self.assertEqual(overview["hero"]["coins"], 20)
            self.assertEqual(overview["hero"]["name"], "Aventurero")
            self.assertEqual(overview["hero"]["appearance"], "Rogue")
            self.assertEqual(overview["progress"]["xp"], 60)
            self.assertEqual(client.post("/api/hero/purchase", json={"item_id": "tunica"}).status_code, 400)
            bought = client.post("/api/hero/purchase", json={"item_id": "capucha"}).json
            self.assertEqual(bought["hero"]["coins"], 10)
            self.assertEqual(bought["hero"]["equipped"]["head"], "capucha")
            self.assertEqual(client.post("/api/hero/purchase", json={"item_id": "capucha"}).status_code, 400)
            self.assertEqual(client.post("/api/hero/purchase", json={"item_id": "capa"}).status_code, 400)
            self.assertEqual(client.put("/api/hero/equipment", json={"slot": "hand", "item_id": "capucha"}).status_code, 400)
            self.assertEqual(client.put("/api/hero/equipment", json={"slot": [], "item_id": None}).status_code, 400)
            unequipped = client.put("/api/hero/equipment", json={"slot": "head", "item_id": None}).json
            self.assertIsNone(unequipped["hero"]["equipped"]["head"])
            self.assertEqual(client.put("/api/hero/name", json={"name": "  Lía  "}).json["hero"]["name"], "Lía")
            self.assertEqual(client.put("/api/hero/appearance", json={"appearance": "Mage"}).json["hero"]["appearance"], "Mage")
            self.assertEqual(client.put("/api/hero/appearance", json={"appearance": "Dragon"}).status_code, 400)
            self.assertEqual(client.put("/api/hero/name", json={"name": " "}).status_code, 400)
            self.assertEqual(client.post("/api/worlds/fundamentos/reset").json["hero"]["coins"], 10)
            self.assertEqual(client.get("/api/progress").json["hero"]["name"], "Lía")
            self.assertEqual(client.get("/api/progress").json["hero"]["appearance"], "Mage")
            self.assertEqual(client.get("/api/progress").json["hero"]["coins"], 10)

    def test_legendary_and_mythic_require_their_milestones(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            state = store.load()
            state["campaign"]["coins"] = 300
            state["campaign"]["awarded_stages"] = [f"{world['id']}:{stage}"
                for world in WORLDS[:5] for stage in range(1, 6)]
            store.save(state)
            client = create_app(directory).test_client()
            client.environ_base["HTTP_X_PYTHON_QUEST"] = "1"
            self.assertEqual(client.post("/api/hero/purchase", json={"item_id": "corona"}).json["hero"]["coins"], 240)
            self.assertEqual(client.post("/api/hero/purchase", json={"item_id": "aura"}).status_code, 400)
            state = store.load()
            state["campaign"]["awarded_stages"].extend(f"{world['id']}:{stage}" for world in WORLDS[5:] for stage in range(1, 6))
            store.save(state)
            self.assertEqual(client.post("/api/hero/purchase", json={"item_id": "aura"}).json["hero"]["coins"], 160)

    def test_legacy_progress_keeps_first_victory(self):
        with tempfile.TemporaryDirectory() as directory:
            old_challenge = {key: value for key, value in GENERATED.items()
                             if key not in {"objective", "input_format", "output_format", "rules"}}
            old_challenge["starter_code"] = "# Código anterior\n"
            legacy = {"challenges": {"old": {**old_challenge, "id": "old", "world_id": "fundamentos", "task": "Enunciado original"}},
                      "attempts": [{"challenge_id": "old", "topic": "fundamentos", "title": "Reto anterior", "passed": True}]}
            Path(directory, "state.json").write_text(json.dumps(legacy), encoding="utf-8")
            store = Store(directory)
            progress = store.progress()
            self.assertEqual(progress["xp"], 30)
            self.assertEqual(progress["world_progress"]["fundamentos"]["stage"], 2)
            self.assertEqual(service.public_challenge(store.load()["challenges"]["old"], store.load())["objective"], "Enunciado original")
            self.assertFalse(service.public_challenge(store.load()["challenges"]["old"], store.load())["can_submit"])
            self.assertNotIn("starter_code", service.public_challenge(store.load()["challenges"]["old"], store.load()))
            with patch("quest.codex_teacher.generate", return_value={**GENERATED, "title": "Nuevo reto", "tests": [{**test, "input": test["input"] + "\n"} for test in TESTS]}), patch("quest.codex_teacher.check_novelty", return_value={"novel": True, "reason": "Nueva operación."}):
                self.assertEqual(service.make_challenge(store, "fundamentos")["stage"], 2)


if __name__ == "__main__":
    unittest.main()
