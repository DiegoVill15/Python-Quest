import ast
from difflib import SequenceMatcher
from datetime import datetime, timezone
from uuid import uuid4

from . import codex_teacher, grader, hero
from .curriculum import CURRICULUM, STAGES_PER_WORLD, WORLD_BY_ID, WORLDS, source_fits_stage, source_features


def fits_world(source, world_id, stage=None):
    try:
        nodes = list(ast.walk(grader.validate_source(source)))
    except (SyntaxError, ValueError, RecursionError):
        return False
    # La solución de referencia viene de la IA y se ejecuta para validar sus pruebas.
    if any(isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)) for node in nodes):
        return False
    if any(isinstance(node, ast.Name) and (node.id.startswith("__") or node.id in {"open", "eval", "exec", "compile", "getattr", "setattr", "delattr"}) for node in nodes):
        return False
    if any(isinstance(node, ast.Attribute) and node.attr.startswith("_") for node in nodes):
        return False
    if stage is not None:
        return source_fits_stage(source, world_id, stage)
    kinds = {type(node) for node in nodes}
    if world_id in {"fundamentos", "condicionales", "bucles", "listas"} and kinds & {ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda}:
        return False
    if world_id == "fundamentos" and kinds & {ast.If, ast.For, ast.While, ast.Dict, ast.ListComp}:
        return False
    if world_id == "funciones" and ast.FunctionDef not in kinds:
        return False
    return True


def public_challenge(challenge, state):
    run = state["campaign"]["runs"][challenge["world_id"]]
    mistakes = [attempt["note"] for attempt in state["attempts"]
                if attempt["challenge_id"] == challenge["id"] and not attempt["passed"]]
    return {
        "id": challenge["id"], "world_id": challenge["world_id"],
        "title": challenge["title"], "story": challenge["story"],
        "objective": challenge.get("objective", challenge.get("task", "")),
        "input_format": challenge.get("input_format", ""),
        "output_format": challenge.get("output_format", ""),
        "rules": challenge.get("rules", []),
        "hint": challenge["hint"],
        "examples": challenge["tests"][:2], "stage": challenge.get("stage", 1),
        "focus": CURRICULUM[challenge["world_id"]][challenge.get("stage", 1) - 1]["focus"],
        "lesson": CURRICULUM[challenge["world_id"]][challenge.get("stage", 1) - 1]["lesson"],
        "total_stages": STAGES_PER_WORLD, "can_submit": run["active_id"] == challenge["id"],
        "last_mistake": mistakes[-1] if mistakes and run["active_id"] != challenge["id"] else "",
    }


def make_challenge(store, world_id):
    if world_id not in WORLD_BY_ID:
        raise ValueError("Ese mundo no existe.")
    state = store.load()
    campaign = state["campaign"]
    if world_id not in campaign["unlocked"]:
        raise ValueError("Completa el mundo anterior para desbloquear este.")
    run = campaign["runs"][world_id]
    if run["completed"] >= STAGES_PER_WORLD:
        raise ValueError("Este mundo está completo. Puedes reiniciarlo para jugar otra vez.")
    if run["active_id"]:
        return public_challenge(state["challenges"][run["active_id"]], state)
    stage = run["completed"] + 1
    mastery = CURRICULUM[world_id][stage - 1]["mastery"]
    history = [item for item in state["challenges"].values() if item["world_id"] == world_id]
    previous_titles = [item["title"] for item in history]
    previous_formats = [" ".join(f"{item.get('input_format', '')} {item.get('output_format', '')}".casefold().split())
                        for item in history]
    previous_missions = [
        {"stage": item.get("stage", 1), "title": item["title"],
         "objective": item.get("objective", item.get("task", ""))[:300],
         "input_format": item.get("input_format", "")[:150],
         "output_format": item.get("output_format", "")[:150],
         "rules": item.get("rules", []),
         "reference_solution": item.get("reference_solution", "")[:4000]}
        for item in history[-5:]
    ]
    errors = store.recent_errors(world_id)
    rejection_feedback = ""
    for _ in range(3):
        preferences = {"summary": state["preferences"]["summary"],
                       "pending": list(state["preferences"]["pending"])}
        try:
            generated = codex_teacher.generate(world_id, stage, previous_missions, errors,
                                                preferences, state["ai"], rejection_feedback)
        finally:
            store.save(state)
        if (not isinstance(generated, dict)
                or any(not isinstance(generated.get(key), str) for key in
                       ("title", "story", "objective", "input_format", "output_format", "hint", "preference_summary", "reference_solution"))
                or not isinstance(generated.get("tests"), list)
                or not all(isinstance(test, dict) for test in generated["tests"])):
            rejection_feedback = "Devuelve todos los campos con los tipos indicados en el esquema JSON."
            continue
        generated = dict(generated)
        tests = generated["tests"]
        generated_format = " ".join(f"{generated.get('input_format', '')} {generated.get('output_format', '')}".casefold().split())
        if (
            len(tests) != mastery["public_tests"] + mastery["hidden_tests"] or not all(isinstance(test.get("input"), str) and isinstance(test.get("expected"), str) for test in tests)
            or any(len(test["input"]) > 2000 or len(test["expected"]) > 1000 for test in tests)
            or generated.get("title", "").casefold() in {title.casefold() for title in previous_titles}
            or any(generated.get("objective", "").strip().casefold() == item.get("objective", item.get("task", "")).strip().casefold()
                   or generated.get("tests") == item["tests"] for item in history)
            or any(test in item["tests"] for test in tests[:2] for item in history)
            or any(SequenceMatcher(None, generated_format, previous).ratio() >= 0.6
                   for previous in previous_formats if previous)
            or any(not isinstance(generated.get(key), str) or not generated[key].strip()
                   for key in ("title", "story", "objective", "input_format", "output_format", "hint"))
            or not isinstance(generated.get("rules"), list)
            or not all(isinstance(rule, str) for rule in generated["rules"])
            or not isinstance(generated.get("preference_summary"), str)
            or len(generated["preference_summary"]) > 600
            or len(generated.get("reference_solution", "")) > 20_000
            or not fits_world(generated.get("reference_solution", ""), world_id, stage)
        ):
            rejection_feedback = "El intento anterior no pasó las comprobaciones de originalidad o consistencia. Cambia la operación o decisión y revisa enunciado y pruebas."
            try:
                used = source_features(generated.get("reference_solution", ""))
                entry = CURRICULUM[world_id][stage - 1]
                unavailable = used - set(entry["allowed"])
                missing = set(entry["required"]) - used
                if unavailable or missing:
                    rejection_feedback = (f"La solución usa construcciones aún no permitidas: {sorted(unavailable)}; "
                                          f"faltan las obligatorias: {sorted(missing)}. Respeta el plan de la etapa.")
            except (SyntaxError, ValueError, RecursionError):
                rejection_feedback = "La solución de referencia tiene un error de sintaxis. Corrígelo antes de generar las pruebas."
            continue
        if not all(result["passed"] for result in grader.grade(generated["reference_solution"], tests)):
            rejection_feedback = "La solución de referencia no pasó todas las pruebas. Corrige el enunciado, la solución y las pruebas."
            continue
        if previous_missions:
            try:
                verdict = codex_teacher.check_novelty(previous_missions, generated, state["ai"])
            finally:
                store.save(state)
            if verdict.get("novel") is not True:
                rejection_feedback = verdict.get("reason") or "El reto repite una mecánica anterior."
                continue
        summary = generated.pop("preference_summary")
        if state["preferences"]["pending"]:
            state["preferences"]["summary"] = summary
        state["preferences"]["pending"] = []
        challenge = {**generated, "id": uuid4().hex, "world_id": world_id, "stage": stage}
        state["challenges"][challenge["id"]] = challenge
        run["active_id"] = challenge["id"]
        store.save(state)
        return public_challenge(challenge, state)
    raise codex_teacher.TeacherError("No pude crear un reto consistente. Inténtalo de nuevo.")


def submit(store, challenge_id, source):
    if not isinstance(source, str) or not source.strip() or len(source) > 20_000:
        raise ValueError("Escribe una solución de hasta 20 000 caracteres.")
    state = store.load()
    challenge = state["challenges"].get(challenge_id)
    if not challenge:
        raise ValueError("Ese reto no existe. Crea uno nuevo.")
    campaign = state["campaign"]
    run = campaign["runs"][challenge["world_id"]]
    if run["active_id"] != challenge_id:
        raise ValueError("Esta misión ya no está activa. Continúa desde el mapa.")
    try:
        compile(source, "solucion.py", "exec")
    except SyntaxError as error:
        results = []
        passed = False
        message = error.msg
        if "expected ':'" in message:
            hint = "Revisa si falta : al final de un if, elif, else, for o while."
        elif "expected an indented block" in message:
            hint = "La línea anterior necesita un bloque con sangría debajo."
        elif message == "unexpected indent":
            hint = "Hay espacios de más al comienzo de esta línea."
        else:
            hint = "Revisa esa línea y la anterior; después vuelve a enviarlo."
        review = {"note": f"Python se detuvo en la línea {error.lineno}: {message}.",
                  "improvement": hint, "weakness": "sintaxis"}
    else:
        results = grader.grade(source, challenge["tests"])
        passed = all(result["passed"] for result in results)
        previous_feedback = next((item["note"] for item in reversed(state["attempts"])
                                  if item["challenge_id"] == challenge_id and not item["passed"]), "")
        try:
            review = codex_teacher.review(challenge, source, results, previous_feedback, state["ai"])
            if not isinstance(review, dict) or any(not isinstance(review.get(key), str) or not review[key].strip()
                                                   for key in ("note", "improvement", "weakness")):
                raise codex_teacher.TeacherError("La revisión no tiene el formato esperado.")
        except codex_teacher.TeacherError:
            review = {
                "note": "Pasaste todas las pruebas." if passed else "Algunas pruebas fallaron. Abajo puedes ver los datos, la respuesta esperada y lo que mostró tu programa.",
                "improvement": "Sigue practicando con la próxima misión." if passed else "Empieza por la primera prueba fallida y sigue tus condiciones con esos valores.",
                "weakness": "ninguna" if passed else challenge["world_id"],
            }
    award_key = f"{challenge['world_id']}:{challenge['stage']}"
    first_completion = passed and award_key not in campaign["awarded_stages"]
    state["attempts"].append({
        "challenge_id": challenge_id, "title": challenge["title"], "topic": challenge["world_id"],
        "passed": passed, "weakness": review["weakness"], "note": review["note"],
        "at": datetime.now(timezone.utc).isoformat(),
    })
    if passed:
        run["completed"] = challenge["stage"]
        run["active_id"] = None
        if first_completion:
            campaign["awarded_stages"].append(award_key)
            campaign["xp_earned"] += 30
            campaign["coins"] += 10
        if run["completed"] == STAGES_PER_WORLD:
            index = [world["id"] for world in WORLDS].index(challenge["world_id"])
            if index + 1 < len(WORLDS):
                next_world = WORLDS[index + 1]["id"]
                if next_world not in campaign["unlocked"]:
                    campaign["unlocked"].append(next_world)
    store.save(state)
    visible_results = [
        {"number": index + 1, "passed": result["passed"],
         "input": test["input"] if not result["passed"] else "",
         "expected": test["expected"] if not result["passed"] else "",
         "actual": result["actual"] if not result["passed"] else "",
         "error": result["error"] if not result["passed"] else ""}
        for index, (test, result) in enumerate(zip(challenge["tests"], results))
    ]
    return {
        "passed": passed, "results": visible_results, "review": review,
        "syntax_error": not results,
        "xp_gained": 30 if first_completion else 0, "coins_gained": 10 if first_completion else 0,
        "progress": store.progress(),
        "next_world_id": (WORLDS[[world["id"] for world in WORLDS].index(challenge["world_id"]) + 1]["id"]
                          if passed and run["completed"] == STAGES_PER_WORLD and challenge["world_id"] != WORLDS[-1]["id"]
                          else challenge["world_id"] if passed and run["completed"] < STAGES_PER_WORLD else None),
    }


def reset_world(store, world_id):
    if world_id not in WORLD_BY_ID:
        raise ValueError("Ese mundo no existe.")
    state = store.load()
    if world_id not in state["campaign"]["unlocked"]:
        raise ValueError("Ese mundo sigue bloqueado.")
    state["campaign"]["runs"][world_id] = {"completed": 0, "active_id": None}
    store.save(state)
    return overview(store)


def overview(store):
    state = store.load()
    return {"worlds": WORLDS, "progress": store.progress(),
            "hero": hero.public_hero(state),
            "ai_usage": state["ai"]["usage"],
            "recent": [{"id": item["id"], "world_id": item["world_id"], "title": item["title"],
                        "can_submit": state["campaign"]["runs"][item["world_id"]]["active_id"] == item["id"]}
                       for item in list(state["challenges"].values())[-5:][::-1]]}
