"""
Save / Load system with offline time-based Tamagotchi decay.

Persists the dog, world progression and adoption metadata to
~/.dog_tamagotchi/save.json. When a save is resumed, needs decay by real
elapsed time (the dog got hungry / missed you while the game was closed),
but every stat is floored/capped so the dog always survives a long absence.

This module is intentionally dependency-free (it only duck-types the `dog`
and `world` objects) so it can be unit-tested in isolation.
"""

import os
import json
import time
import tempfile

SAVE_DIR = os.path.join(os.path.expanduser("~"), ".dog_tamagotchi")
SAVE_PATH = os.path.join(SAVE_DIR, "save.json")
VERSION = 1

DAY_SECONDS = 86400.0

# Real-time decay rates applied per elapsed MINUTE while the game is closed.
OFFLINE_RATE = {
    "hunger":    -0.45,   # fullness drops (dog gets hungry)
    "bladder":   +0.35,   # bladder fills up
    "happiness": -0.30,   # dog misses you
    "energy":     0.20,   # drifts toward a rested baseline (see _drift)
}
# Hard safety floors/ceilers so a week away never kills the dog.
OFFLINE_CLAMP = {
    "hunger":    (5.0, 100.0),
    "bladder":   (0.0, 90.0),
    "happiness": (15.0, 100.0),
    "energy":    (20.0, 100.0),
}
# Cap how much real time counts toward decay (a month away == 12h of need).
OFFLINE_DECAY_CAP_MIN = 720.0


def exists():
    return os.path.isfile(SAVE_PATH)


def _atomic_write(path, obj):
    """Write JSON atomically so a crash mid-save can't corrupt the file."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    try:
        os.chmod(SAVE_DIR, 0o700)
    except OSError:
        pass
    fd, tmp = tempfile.mkstemp(dir=SAVE_DIR, prefix="save_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on POSIX
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def new_meta(name=""):
    now = time.time()
    return {
        "name": name,
        "created_at": now,
        "adoption_count": 1,
    }


def build_state(dog, world, meta, quests=None):
    """Serialize dog + world + meta into a JSON-safe dict."""
    return {
        "version": VERSION,
        "saved_at": time.time(),
        "meta": {
            "name": getattr(dog, "name", "") or meta.get("name", ""),
            "created_at": meta.get("created_at", time.time()),
            "adoption_count": meta.get("adoption_count", 1),
        },
        "dog": {
            "breed_key": dog.breed_key,
            "hunger": dog.hunger,
            "happiness": dog.happiness,
            "bladder": dog.bladder,
            "energy": dog.energy,
            "xp": dog.xp,
            "level": dog.level,
            "bones_currency": dog.bones_currency,
            "equipped_item": dog.equipped_item,
            "inventory": list(dog.inventory),
            "bones_eaten": dog.bones_eaten,
            "times_petted": dog.times_petted,
            "peeled_spots": dog.peeled_spots,
            "tricks_performed": dog.tricks_performed,
            "ball_fetches": getattr(dog, "ball_fetches", 0),
            "walk_distance": dog.walk_distance,
        },
        "world": {
            "agility_best_time": getattr(world, "agility_best_time", None),
            "day_time": getattr(world, "day_time", 0.25),
        },
        "quests": quests if isinstance(quests, dict) else None,
    }


def save_game(dog, world, meta, quests=None):
    """Persist current state. Returns the saved dict; raises on write failure."""
    state = build_state(dog, world, meta, quests)
    _atomic_write(SAVE_PATH, state)
    return state


def load_raw():
    """Load the raw save dict, or None if missing/corrupt/incompatible."""
    if not exists():
        return None
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        if int(data.get("version", 0)) > VERSION:
            # Newer save than this build understands; ignore rather than crash.
            return None
        if "dog" not in data or "meta" not in data:
            return None
        return data
    except (OSError, ValueError, TypeError):
        # Corrupt file: quarantine it so we can start fresh without losing data.
        try:
            os.replace(SAVE_PATH, SAVE_PATH + ".corrupt." + str(int(time.time())))
        except OSError:
            pass
        return None


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def apply_to_dog(data, dog):
    """Copy persisted stats onto a freshly constructed Dog (with validation)."""
    d = data.get("dog", {})
    def num(key, default, lo, hi):
        try:
            return _clamp(float(d.get(key, default)), lo, hi)
        except (TypeError, ValueError):
            return _clamp(float(default), lo, hi)

    dog.hunger = num("hunger", 85.0, 0.0, 100.0)
    dog.happiness = num("happiness", 90.0, 0.0, 100.0)
    dog.bladder = num("bladder", 20.0, 0.0, 100.0)
    dog.energy = num("energy", 100.0, 0.0, 100.0)
    dog.xp = num("xp", 0.0, 0.0, 1e9)
    dog.level = int(num("level", 1, 1, 999))
    dog.bones_currency = int(num("bones_currency", 3, 0, 1_000_000))

    inv = d.get("inventory", [])
    dog.inventory = [k for k in inv if isinstance(k, str)] if isinstance(inv, list) else []
    eq = d.get("equipped_item")
    dog.equipped_item = eq if isinstance(eq, str) and eq in dog.inventory else None

    for key in ("bones_eaten", "times_petted", "peeled_spots", "tricks_performed",
                "ball_fetches"):
        try:
            setattr(dog, key, max(0, int(float(d.get(key, 0) or 0))))
        except (TypeError, ValueError):
            setattr(dog, key, 0)
    dog.walk_distance = num("walk_distance", 0.0, 0.0, 1e9)
    return dog


def apply_to_world(data, world):
    w = data.get("world", {})
    bt = w.get("agility_best_time")
    world.agility_best_time = (
        float(bt) if isinstance(bt, (int, float)) and not isinstance(bt, bool) else None
    )
    try:
        world.day_time = _clamp(float(w.get("day_time", 0.25)), 0.0, 1.0)
    except (TypeError, ValueError):
        world.day_time = 0.25
    return world


def days_together(meta, now=None):
    created = meta.get("created_at", time.time())
    return int(max(0, (now or time.time()) - created) // DAY_SECONDS)


def apply_offline_decay(dog, saved_at, meta=None, now=None):
    """
    Advance the dog's needs by real elapsed time and return a greeting string
    describing what happened while the player was away. Stats are clamped so
    the dog always survives. Returns (greeting_text, days).
    """
    now = now or time.time()
    elapsed = max(0.0, now - float(saved_at))
    minutes = min(elapsed / 60.0, OFFLINE_DECAY_CAP_MIN)
    days = days_together(meta or {}, now)

    if minutes < 0.5:
        # Barely gone — no decay, keep it friendly.
        return (None, days)

    # Energy drifts toward a comfortable baseline rather than only decaying.
    if dog.energy < 60.0:
        dog.energy = _clamp(dog.energy + OFFLINE_RATE["energy"] * minutes, *OFFLINE_CLAMP["energy"])
    else:
        dog.energy = _clamp(dog.energy - 0.05 * minutes, *OFFLINE_CLAMP["energy"])

    for stat in ("hunger", "bladder", "happiness"):
        cur = getattr(dog, stat) + OFFLINE_RATE[stat] * minutes
        setattr(dog, stat, _clamp(cur, *OFFLINE_CLAMP[stat]))

    name = (meta or {}).get("name") or "Piesek"
    if elapsed < 3600:
        greet = f"{name} tęsknił i jest głodny! 🦴"
    elif elapsed < DAY_SECONDS:
        greet = f"{name} czekał i bardzo tęsknił! 💔"
    else:
        greet = f"{name} czekał cierpliwie {days} dn. 💔 Nareszcie wróciłeś!"
    return (greet, days)
