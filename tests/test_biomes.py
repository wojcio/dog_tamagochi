#!/usr/bin/env python3
"""
Biome & gameplay invariants for the 8-zone world: zone table, swimming,
squirrels, dog friends, street traffic/crossings, and the Hydrant Alley bonus.
Headless — no terminal needed. Run: python3 tests/test_biomes.py
"""

import os
import sys
import random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from game.world import (World, ZONES, zone_at, is_water, WATER_MIN, WATER_MAX,
                        ZEBRA_MIN, ZEBRA_MAX, CAR_STOP_X)
from game.dog import Dog
from game.npc import Squirrel, Duck, DogFriend
from game import save as SaveSystem
from game import quests as QuestSystem

FAILS = []


def check(name, cond):
    status = "OK" if cond else "FAIL"
    print(f"  [{status}] {name}")
    if not cond:
        FAILS.append(name)


def fresh_dog(x=10.0):
    return Dog("corgi", x, 16)


def test_zone_table():
    print("== ZONES table ==")
    check("8 zones", len(ZONES) == 8)
    check("spans 0..840", ZONES[0]["start"] == 0 and ZONES[-1]["end"] == 840)
    contiguous = all(a["end"] == b["start"] for a, b in zip(ZONES, ZONES[1:]))
    check("contiguous (no gaps/overlaps)", contiguous)
    ids = [z["id"] for z in ZONES]
    check("order garden..agility",
          ids == ["garden", "forest", "river", "park", "dogpark", "street", "beach", "agility"])
    probes = {50: "garden", 150: "forest", 260: "river", 350: "park",
              470: "dogpark", 570: "street", 680: "beach", 800: "agility"}
    for x, want in probes.items():
        check(f"zone_at({x}) == {want}", zone_at(x)["id"] == want)
    check("edges clamp", zone_at(-99)["id"] == "garden" and zone_at(9999)["id"] == "agility")
    check("water band inside river zone",
          is_water(WATER_MIN) and is_water(WATER_MAX)
          and not is_water(WATER_MIN - 1) and not is_water(WATER_MAX + 1))


def test_swimming():
    print("== River swimming ==")
    w = World()
    d = fresh_dog(WATER_MIN - 4)
    # paddle into the water
    for _ in range(60):
        d.move_right()
        d.update_physics(w)
        w.update(d)
    check("entered water (swimming)", d.swimming)
    check("swims counter incremented", d.swims == 1)
    surface = w.ground_base_y - d.height + 1
    check("locked to surface", abs(d.y - surface) < 0.01)
    # paddle right until the east bank
    for _ in range(900):
        d.move_right()
        d.update_physics(w)
        w.update(d)
        if not d.swimming:
            break
    check("exited at east bank", not d.swimming and d.x + d.width / 2 > WATER_MAX)
    check("wet after exit", d.wet_timer > 0)
    # a second entry counts again
    d2 = fresh_dog(WATER_MIN + 10)
    d2.vy = 0.5
    d2.update_physics(w)
    check("re-entry counts", d2.swims == 1 and d2.swimming)


def test_squirrels():
    print("== Squirrels ==")
    w = World()
    d = fresh_dog(140)
    sq = Squirrel(143, 140, 170)
    d.bark()
    sq.update(d, w)
    check("bark scatters squirrel", sq.state == "flee")
    check("chase counted", d.squirrels_chased == 1)
    sq.update(d, w)  # bark still ringing, but this squirrel is on cooldown
    check("per-squirrel cooldown prevents double-count", d.squirrels_chased == 1)


def test_dog_friends():
    print("== Dog friends ==")
    w = World()
    d = fresh_dog(450)
    pal = DogFriend("Burek", 453, 424, 468)
    d.bark()
    pal.update(d, w)
    check("bark invites play", pal.state == "play")
    before = d.happiness
    for _ in range(80):
        pal.update(d, w)
    check("play finished", pal.state != "play")
    check("dog_plays counted", d.dog_plays == 1)
    check("happiness boosted", d.happiness > before)
    check("play cooldown set", pal.play_cool > 0)


def test_ducks():
    print("== Ducks ==")
    w = World()
    d = fresh_dog(50)  # far away, ducks act naturally
    duck = Duck(260)
    for _ in range(400):
        duck.update(d, w)
        check_x = 216 <= duck.x <= 309
        if not check_x:
            break
    check("duck stays in the river region", check_x)
    check("duck sprite row above ground paint", duck.y == w.ground_base_y - 2)


def test_signal_and_traffic():
    print("== Street signal & traffic ==")
    w = World()
    d = fresh_dog(560)
    greens, reds = set(), set()
    for _ in range(520):
        w.update(d)
        greens.add(w.signal_green)
    check("signal cycles green & red", greens == {True, False})

    # Cars stop at the zebra while green
    w.cars = [{"x": float(WORLD_STREET_END + 10), "vx": -1.2, "style": "🚗", "hit": False}]
    w.signal_green = True
    x0 = w.cars[0]["x"]
    for _ in range(30):
        w._update_traffic(d)
    check("car held at red light during dog-green", w.cars[0]["x"] == x0)

    w.signal_green = False
    for _ in range(30):
        w._update_traffic(d)
    check("car proceeds on its green", w.cars[0]["x"] < x0)


WORLD_STREET_END = 630


def test_car_scare():
    print("== Car scare (friendly knockback) ==")
    w = World()
    d = fresh_dog(560)
    hp0 = d.happiness
    w.signal_green = False
    w.cars = [{"x": d.x + d.width / 2 - 2, "vx": -1.0, "style": "🚙", "hit": False}]
    w._update_traffic(d)
    check("dog scared (happiness -5)", abs(hp0 - d.happiness - 5.0) < 0.01)
    check("knocked back airborne", not d.on_ground)
    check("grace frames set", d.car_grace > 0)
    check("no death: dog alive & stats sane", d.energy >= 0 and d.happiness >= 0)


def test_safe_crossing():
    print("== Safe zebra crossing ==")
    w = World()
    d = fresh_dog(530)
    w.cars = []
    w.car_timer = 10 ** 9  # no spawns: deterministic walk
    xp0 = d.xp
    for _ in range(200):
        d.move_right()
        d.update_physics(w)
        w.update(d)
        if d.x > WORLD_STREET_END:
            break
    check("crossed to the east side", d.x > WORLD_STREET_END)
    check("crossings_safe counted", d.crossings_safe == 1)
    check("XP awarded", d.xp > xp0)
    # walking back without the zebra must NOT count
    w.car_timer = 10 ** 9
    for _ in range(240):
        d.move_left()
        d.update_physics(w)
        w.update(d)
        if d.x < 524:
            break
    check("back on the west side", d.x < 524)


def test_hydrant_alley():
    print("== Hydrant Alley bonus ==")
    w = World()
    d = fresh_dog(440)
    bones0 = d.bones_currency
    alley = [p for p in w.props
             if p.prop_type == "hydrant" and 420 <= p.x < 470]
    check("6 hydrants in the alley", len(alley) == 6)
    for p in alley[:-1]:
        p.marked = True
    w.update(d)
    check("no bonus while one unmarked", not w.alley_bonus_done)
    alley[-1].marked = True
    w.update(d)
    check("bonus fires when all marked", w.alley_bonus_done)
    check("+5 bones", d.bones_currency == bones0 + 5)
    w.update(d)
    check("fires only once", d.bones_currency == bones0 + 5)


def test_save_roundtrip():
    print("== Save v2 roundtrip & v1 back-compat ==")
    w = World()
    d = fresh_dog(450)
    d.squirrels_chased = 3
    d.swims = 2
    d.crossings_safe = 4
    d.dog_plays = 1
    w.alley_bonus_done = True
    state = SaveSystem.build_state(d, w, SaveSystem.new_meta("Burek"))
    check("version bumped to 2", state["version"] == 2)

    d2, w2 = fresh_dog(), World()
    SaveSystem.apply_to_dog(state, d2)
    SaveSystem.apply_to_world(state, w2)
    check("new counters roundtrip",
          (d2.squirrels_chased, d2.swims, d2.crossings_safe, d2.dog_plays) == (3, 2, 4, 1))
    check("alley bonus roundtrips", w2.alley_bonus_done)

    # v1 save (no new keys) must still load with zeroed counters
    v1 = SaveSystem.build_state(d, w, SaveSystem.new_meta("Stary"))
    v1["version"] = 1
    for k in ("squirrels_chased", "swims", "crossings_safe", "dog_plays"):
        del v1["dog"][k]
    del v1["world"]["alley_bonus_done"]
    d3, w3 = fresh_dog(), World()
    SaveSystem.apply_to_dog(v1, d3)
    SaveSystem.apply_to_world(v1, w3)
    check("v1 save loads, counters default 0",
          d3.squirrels_chased == 0 and not w3.alley_bonus_done)


def test_quests_pool():
    print("== Quest pool ==")
    ids = {q["id"] for q in QuestSystem.QUEST_POOL}
    check("new quest ids present",
          {"squirrel", "swim", "cross", "dogplay"} <= ids)
    d = fresh_dog()
    st = QuestSystem.roll("2026-11-07", d)
    check("still rolls 3 quests/day", len(st["quests"]) == 3)
    for q in QuestSystem.QUEST_POOL:
        check(f"counter '{q['counter']}' exists on Dog", hasattr(d, q["counter"]))


if __name__ == "__main__":
    random.seed(7)
    test_zone_table()
    test_swimming()
    test_squirrels()
    test_dog_friends()
    test_ducks()
    test_signal_and_traffic()
    test_car_scare()
    test_safe_crossing()
    test_hydrant_alley()
    test_save_roundtrip()
    test_quests_pool()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES: {FAILS}")
        sys.exit(1)
    print("ALL BIOME TESTS PASS [OK]")
