import json
import os
import tempfile
from pathlib import Path

from .curriculum import WORLDS, STAGES_PER_WORLD
from .providers import settings


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "state.json"
        self.directory.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            state = {"challenges": {}, "attempts": []}
            self.ensure_campaign(state)
            self.ensure_hero(state)
            self.ensure_preferences(state)
            settings(state)
            return state
        with self.path.open(encoding="utf-8") as file:
            state = json.load(file)
        self.ensure_campaign(state)
        self.ensure_hero(state)
        self.ensure_preferences(state)
        settings(state)
        return state

    @staticmethod
    def ensure_preferences(state):
        state.setdefault("preferences", {"summary": "", "pending": []})

    @staticmethod
    def ensure_campaign(state):
        if "campaign" in state:
            state["campaign"].setdefault("coins", 10 * len(state["campaign"]["awarded_stages"]))
            campaign = state["campaign"]
            for index, world in enumerate(WORLDS):
                campaign["runs"].setdefault(world["id"], {"completed": 0, "active_id": None})
                if index and (campaign["runs"][WORLDS[index - 1]["id"]]["completed"] == STAGES_PER_WORLD
                              or f"{WORLDS[index - 1]['id']}:{STAGES_PER_WORLD}" in campaign["awarded_stages"]):
                    if world["id"] not in campaign["unlocked"]:
                        campaign["unlocked"].append(world["id"])
            return
        passed = {item["challenge_id"] for item in state["attempts"] if item["passed"]}
        counts = {world["id"]: 0 for world in WORLDS}
        for challenge_id in passed:
            challenge = state["challenges"].get(challenge_id)
            if challenge and challenge["world_id"] in counts:
                counts[challenge["world_id"]] += 1
        runs = {world_id: {"completed": min(count, STAGES_PER_WORLD), "active_id": None}
                for world_id, count in counts.items()}
        unlocked = [WORLDS[0]["id"]]
        for index, world in enumerate(WORLDS[:-1]):
            if runs[world["id"]]["completed"] == STAGES_PER_WORLD:
                unlocked.append(WORLDS[index + 1]["id"])
        awards = [f"{world_id}:{stage}" for world_id, count in counts.items()
                  for stage in range(1, min(count, STAGES_PER_WORLD) + 1)]
        state["campaign"] = {"runs": runs, "unlocked": unlocked,
                             "awarded_stages": awards, "xp_earned": len(passed) * 30,
                             "coins": len(awards) * 10}

    @staticmethod
    def ensure_hero(state):
        state.setdefault("hero", {"name": "Aventurero", "owned": [], "equipped": {}})
        state["hero"].setdefault("appearance", "Rogue")

    def save(self, state):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.directory, delete=False) as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
            temporary = file.name
        os.replace(temporary, self.path)

    def recent_errors(self, topic, limit=3):
        attempts = self.load()["attempts"]
        return [
            {"title": item["title"], "weakness": item.get("weakness", ""), "note": item.get("note", "")}
            for item in reversed(attempts)
            if item["topic"] == topic and not item["passed"]
        ][:limit]

    def progress(self):
        state = self.load()
        campaign = state["campaign"]
        counts = {world_id: run["completed"] for world_id, run in campaign["runs"].items()}
        total = sum(counts.values())
        earned = len(campaign["awarded_stages"])
        trophies = []
        if earned:
            trophies.append({"name": "Primer paso", "icon": "✦", "detail": "Completa tu primer reto"})
        if earned >= 5:
            trophies.append({"name": "Explorador", "icon": "★", "detail": "Completa 5 retos"})
        for world in WORLDS:
            if f"{world['id']}:5" in campaign["awarded_stages"]:
                trophies.append({"name": f"Guardián de {world['name']}", "icon": "♛", "detail": "Completa sus cinco misiones"})
        if len(campaign["awarded_stages"]) == len(WORLDS) * STAGES_PER_WORLD:
            trophies.append({"name": "Leyenda de Python", "icon": "★", "detail": "Completa toda la campaña"})
        world_progress = {world["id"]: {"completed": counts[world["id"]], "total": STAGES_PER_WORLD,
                        "stage": min(counts[world["id"]] + 1, STAGES_PER_WORLD),
                        "unlocked": world["id"] in campaign["unlocked"],
                        "finished": counts[world["id"]] == STAGES_PER_WORLD,
                        "active_id": campaign["runs"][world["id"]]["active_id"]}
                          for world in WORLDS}
        return {"xp": campaign["xp_earned"], "level": campaign["xp_earned"] // 90 + 1,
                "completed": total, "total_missions": len(WORLDS) * STAGES_PER_WORLD, "world_counts": counts, "world_progress": world_progress,
                "campaign_complete": all(item["finished"] for item in world_progress.values()), "trophies": trophies}
