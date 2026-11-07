"""
Daily quests: three small goals per calendar day with bone & XP rewards.

Quests track the dog's own lifetime counters (bones_eaten, times_petted, ...)
against a per-day BASELINE captured at roll time, so yesterday's progress can
never complete today's goals. The set for a day is chosen deterministically
from (date + dog name), so resuming the same save on the same day always
shows the same quests, but tomorrow brings a fresh batch.

Duck-types `dog`; dependency-free and unit-testable in isolation.
"""

import random

QUESTS_PER_DAY = 3

# counter: attribute on Dog tracked cumulatively.
QUEST_POOL = [
    {"id": "feed",  "counter": "bones_eaten",      "targets": (2, 3, 4),      "bones": 5, "xp": 25,
     "text": "Nakarm pieska {n} razy 🍖"},
    {"id": "pet",   "counter": "times_petted",      "targets": (3, 4, 5),      "bones": 4, "xp": 20,
     "text": "Pogłaszcz pieska {n} razy 🥰"},
    {"id": "trick", "counter": "tricks_performed",  "targets": (3, 5, 8),      "bones": 6, "xp": 35,
     "text": "Wykonaj {n} sztuczek 🎪"},
    {"id": "fetch", "counter": "ball_fetches",      "targets": (2, 3, 5),      "bones": 5, "xp": 30,
     "text": "Kopnij piłkę {n} razy ⚽"},
    {"id": "walk",  "counter": "walk_distance",     "targets": (60, 100, 150), "bones": 7, "xp": 30,
     "text": "Przebiegnij razem {n} m 🐾"},
    {"id": "pee",   "counter": "peeled_spots",      "targets": (2, 3),         "bones": 4, "xp": 15,
     "text": "Zrób siku {n} razy 💦"},
]

_BY_ID = {q["id"]: q for q in QUEST_POOL}


def today_str(now=None):
    import time
    if now is None:
        return time.strftime("%Y-%m-%d")
    return time.strftime("%Y-%m-%d", time.localtime(now))


def roll(day_str, dog):
    """Deterministic quest set for a day. `base` snapshots current counters."""
    rng = random.Random(f"{day_str}|{getattr(dog, 'name', '')}")
    picks = rng.sample(QUEST_POOL, QUESTS_PER_DAY)
    quests = []
    for q in picks:
        target = rng.choice(q["targets"])
        quests.append({
            "id": q["id"],
            "counter": q["counter"],
            "target": target,
            "base": float(getattr(dog, q["counter"], 0) or 0),
            "bones": q["bones"],
            "xp": q["xp"],
            "text": q["text"].format(n=target),
            "done": False,
        })
    return {"date": day_str, "quests": quests}


def ensure_today(state, day_str, dog):
    """Return (state, rolled_new_day). Rolls a fresh set when the day changed."""
    if isinstance(state, dict) and state.get("date") == day_str \
            and isinstance(state.get("quests"), list):
        return state, False
    return roll(day_str, dog), True


def progress_of(quest, dog):
    cur = float(getattr(dog, quest["counter"], 0) or 0)
    return max(0.0, cur - float(quest.get("base", 0)))


def check_completions(state, dog):
    """Mark finished quests and award rewards. Returns list of event dicts."""
    events = []
    if not isinstance(state, dict):
        return events
    for q in state.get("quests", []):
        if q.get("done"):
            continue
        if progress_of(q, dog) >= q["target"]:
            q["done"] = True
            dog.bones_currency = int(getattr(dog, "bones_currency", 0)) + q["bones"]
            if hasattr(dog, "add_xp"):
                dog.add_xp(q["xp"])
            events.append({"text": q["text"], "bones": q["bones"], "xp": q["xp"]})
    return events


def done_count(state):
    if not isinstance(state, dict):
        return 0
    return sum(1 for q in state.get("quests", []) if q.get("done"))


def total_count(state):
    if not isinstance(state, dict):
        return 0
    return len(state.get("quests", []))


def sanitize(raw):
    """Validate a quest state loaded from disk. Returns a safe dict or None."""
    if not isinstance(raw, dict):
        return None
    day = raw.get("date")
    if not isinstance(day, str) or not raw.get("quests"):
        return None
    quests = []
    for q in raw.get("quests", []):
        if not isinstance(q, dict) or q.get("id") not in _BY_ID:
            continue
        try:
            target = int(float(q.get("target", 1)))
            if target < 1:
                continue
            quests.append({
                "id": q["id"],
                "counter": _BY_ID[q["id"]]["counter"],  # trust the pool, not disk
                "target": target,
                "base": max(0.0, float(q.get("base", 0))),
                "bones": max(0, min(int(float(q.get("bones", 0))), 10_000)),
                "xp": max(0, min(int(float(q.get("xp", 0))), 1_000_000)),
                "text": str(_BY_ID[q["id"]]["text"].format(n=target)),
                "done": bool(q.get("done")),
            })
        except (TypeError, ValueError):
            continue
    if not quests:
        return None
    return {"date": day, "quests": quests}
