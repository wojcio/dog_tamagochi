"""
Expansive 2D World with 8 Biomes (Garden, Forest, River, Park, Dog Park,
Street, Beach, Agility), Day/Night Cycle, Interactive Props, Obstacles,
River Swimming and Street Traffic.

ZONES is the single source of truth for biome layout: every gameplay rule
(zone HUD label, ground style, agility gates, splash zones, traffic) reads
from it instead of hardcoded x-ranges.
"""

import math
import random
from game.engine import Colors
from game.audio import audio

class Platform:
    def __init__(self, x, y, width, style=Colors.BROWN, label="", dx=0.0):
        self.x = x
        self.y = y
        self.width = width
        self.style = style
        self.label = label
        self.dx = dx  # horizontal drift per tick (ridable moving log)

class Item:
    def __init__(self, item_type, x, y, value=35.0):
        self.item_type = item_type # 'bone', 'bowl', 'steak', 'treat', 'fish'
        self.x = x
        self.y = y
        self.value = value
        self.collected = False
        self.respawn_timer = 0

class ToyBall:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True
        self.kick_cd = 0

    def update(self, world):
        if not self.on_ground:
            self.vy += 0.4
            if self.vy > 1.5:
                self.vy = 1.5

        self.x += self.vx
        if self.x < 1:
            self.x = 1
            self.vx = -self.vx * 0.6
        elif self.x > world.width - 2:
            self.x = world.width - 2
            self.vx = -self.vx * 0.6

        ground_y = world.get_ground_y(self.x, self.x + 1, self.y + 1)
        if self.y + 1 >= ground_y:
            self.y = ground_y - 1
            if abs(self.vy) > 0.6:
                self.vy = -self.vy * 0.5 # bounce!
            else:
                self.vy = 0
                self.on_ground = True
        else:
            self.on_ground = False

        # Never sink into river water: float on the surface instead.
        if world.is_water(self.x) and self.y + 1 >= world.ground_base_y:
            self.y = world.ground_base_y - 1
            self.vy = 0
            self.on_ground = True

        self.vx *= 0.88
        if abs(self.vx) < 0.05:
            self.vx = 0

class SceneryProp:
    def __init__(self, prop_type, x, y, width=5, height=5, label=""):
        self.prop_type = prop_type # 'tree', 'pine', 'log', 'mushroom', 'fern', 'reed', 'rock',
                                  # 'hydrant', 'doghouse', 'bench', 'lamp', 'shop', 'fountain',
                                  # 'umbrella', 'slalom', 'hurdle', 'hoop', 'start_gate',
                                  # 'finish_gate', 'fence', 'park_sign', 'ballpit', 'tunnel',
                                  # 'bike', 'traffic_light'
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.marked = False # Marked by pee

# ---------------------------------------------------------------------------
# ZONE TABLE — single source of truth for the 8-biome world layout (840 cols).
# ---------------------------------------------------------------------------
ZONES = [
    {"id": "garden",  "start":   0, "end": 105, "name": "Ogród & Dom",    "emoji": "🏡", "color": Colors.BRIGHT_GREEN,   "ground": "garden"},
    {"id": "forest",  "start": 105, "end": 210, "name": "Las",            "emoji": "🌲", "color": Colors.DARK_GREEN,     "ground": "forest"},
    {"id": "river",   "start": 210, "end": 315, "name": "Rzeka",          "emoji": "🌊", "color": Colors.BRIGHT_CYAN,    "ground": "river"},
    {"id": "park",    "start": 315, "end": 420, "name": "Park Miejski",   "emoji": "🌳", "color": Colors.GREEN,          "ground": "park"},
    {"id": "dogpark", "start": 420, "end": 525, "name": "Psi Park",       "emoji": "🎾", "color": Colors.BRIGHT_MAGENTA, "ground": "dogpark"},
    {"id": "street",  "start": 525, "end": 630, "name": "Ulica",          "emoji": "🚗", "color": Colors.BRIGHT_YELLOW,  "ground": "street"},
    {"id": "beach",   "start": 630, "end": 735, "name": "Plaża dla Psów", "emoji": "🏖️", "color": Colors.GOLD,           "ground": "beach"},
    {"id": "agility", "start": 735, "end": 840, "name": "Tor Agility",    "emoji": "🏆", "color": Colors.BRIGHT_CYAN,    "ground": "turf"},
]

BY_ID = {z["id"]: z for z in ZONES}

# River open-water band (inside the river zone; banks are walkable ground).
WATER_MIN = 228
WATER_MAX = 300

# Street geometry (zebra crossing + where cars stop when the dog has green).
STREET = BY_ID["street"]
ZEBRA_MIN = 568
ZEBRA_MAX = 584
CAR_STOP_X = 588

# Agility course anchors, derived from the agility zone start.
_AG = BY_ID["agility"]["start"]
AGILITY_GATE_X    = _AG + 5     # start gate prop
AGILITY_START_MIN = _AG + 3     # race start detection band
AGILITY_START_MAX = _AG + 9
AGILITY_ABORT_X   = _AG + 1     # retreating past this aborts the run
AGILITY_FINISH_MIN = _AG + 88   # finish gate detection band
AGILITY_FINISH_MAX = _AG + 94

# Park stream under the wooden footbridge (the old 143-165, now inside park).
PARK_STREAM_MIN = BY_ID["park"]["start"] + 38   # 353
PARK_STREAM_MAX = BY_ID["park"]["start"] + 60   # 375


def zone_at(x):
    """Zone dict containing world column x (clamped at the edges)."""
    for z in ZONES:
        if z["start"] <= x < z["end"]:
            return z
    return ZONES[0] if x < ZONES[0]["start"] else ZONES[-1]


def is_water(x):
    return WATER_MIN <= x <= WATER_MAX


class World:
    def __init__(self, width=840, height=22):
        self.width = width
        self.height = height
        self.ground_base_y = 19
        
        self.platforms = []
        self.props = []
        self.items = []
        self.balls = [ToyBall(45, 18), ToyBall(490, 18)]
        self.ball = self.balls[0]  # legacy alias (garden ball)
        self.clouds = []
        self.stars = []
        self.time_tick = 0
        
        # Day/Night Cycle (0.0 to 1.0)
        self.day_time = 0.25 # starts at bright day noon
        self.day_speed = 0.00035 # ~1.5 min full cycle
        
        # Agility Course Race Tracker
        self.agility_active = False
        self.agility_start_tick = 0
        self.agility_best_time = None

        # Street traffic
        self.cars = []          # {"x","vx","style","hit"}
        self.car_timer = 90
        self.signal_tick = 0    # pedestrian signal cycle
        self.signal_green = False  # True = dog may cross, cars stopped
        self.cross_state = None # {"from","zebra","safe"} while crossing the street

        # Dog park Hydrant Alley bonus
        self.alley_bonus_done = False

        # Drifting river log (ridable)
        self.drift_log = None

        self._generate_world()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def zone_at(self, x):
        return zone_at(x)

    def is_water(self, x):
        return is_water(x)

    def get_zone_info(self, x):
        """Returns (zone_name, zone_emoji, zone_color)."""
        z = zone_at(x)
        return (z["name"], z["emoji"], z["color"])

    # ------------------------------------------------------------------
    def _generate_world(self):
        # Generate clouds
        for i in range(16):
            cx = random.randint(5, self.width - 20)
            cy = random.randint(1, 4)
            self.clouds.append({"x": float(cx), "y": cy, "speed": random.uniform(0.02, 0.05), "type": i % 3})

        # Generate stars for night sky
        for _ in range(70):
            sx = random.randint(2, self.width - 5)
            sy = random.randint(1, 5)
            char = random.choice(['✦', '★', '·', '°', '*'])
            self.stars.append((sx, sy, char))

        # =========================================================================
        # ZONE 1: OGRÓD I DOM (x: 0 - 105)
        # =========================================================================
        # Doghouse with jumpable roof
        self.props.append(SceneryProp('doghouse', 6, 15, width=9, height=4))
        self.platforms.append(Platform(5, 14, 11, Colors.RED, "Doghouse Roof"))
        self.items.append(Item('bone', 9, 12, value=30.0)) # on doghouse roof!
        
        self.items.append(Item('bowl', 17, 18, value=45.0))
        self.props.append(SceneryProp('hydrant', 28, 17, width=3, height=2))
        
        # Garden Tree with low and high climbable branch platforms
        self.props.append(SceneryProp('tree', 36, 9, width=7, height=10))
        self.platforms.append(Platform(32, 14, 15, Colors.BROWN, "Lower Branch"))
        self.platforms.append(Platform(34, 11, 11, Colors.GRASS_GREEN, "High Branch"))
        self.items.append(Item('steak', 39, 9, value=50.0)) # High steak in tree crown!
        
        # Shop stand of Gardener with jumpable counter/canopy
        self.props.append(SceneryProp('shop', 54, 15, width=12, height=4, label="SKLEP"))
        self.platforms.append(Platform(54, 14, 12, Colors.GOLD, "Shop Canopy"))
        self.items.append(Item('treat', 59, 12, value=35.0))
        
        # Garden bench & platform leading to high lamp
        self.platforms.append(Platform(75, 16, 10, Colors.LIGHT_BROWN, "Garden Bench"))
        self.props.append(SceneryProp('bench', 75, 16, width=10, height=3))
        self.platforms.append(Platform(93, 12, 7, Colors.DARK_GRAY, "Lamp Post Platform"))
        self.items.append(Item('bone', 95, 10, value=30.0))
        self.props.append(SceneryProp('lamp', 95, 11, width=3, height=8))

        # =========================================================================
        # ZONE 2: LAS (x: 105 - 210)
        # =========================================================================
        # Pine forest with a continuous canopy parkour chain across the treetops
        self.props.append(SceneryProp('pine', 112, 8, width=7, height=11))
        self.platforms.append(Platform(115, 12, 9, Colors.DARK_GREEN, "Canopy 1"))
        self.props.append(SceneryProp('pine', 138, 7, width=7, height=12))
        self.platforms.append(Platform(131, 10, 9, Colors.DARK_GREEN, "Canopy 2"))
        self.props.append(SceneryProp('pine', 164, 8, width=7, height=11))
        self.platforms.append(Platform(150, 12, 9, Colors.DARK_GREEN, "Canopy 3"))
        self.props.append(SceneryProp('pine', 190, 6, width=7, height=13))
        self.platforms.append(Platform(168, 10, 9, Colors.DARK_GREEN, "Canopy 4"))
        self.platforms.append(Platform(185, 12, 9, Colors.DARK_GREEN, "Canopy 5"))
        self.platforms.append(Platform(196, 8, 8, Colors.DARK_GREEN, "Tallest Treetop"))
        self.items.append(Item('steak', 198, 6, value=50.0)) # top of the tallest pine!

        # Fallen logs (low hop platforms) with bones cached in the bark
        for lx in (126, 155, 182):
            self.props.append(SceneryProp('log', lx, 17, width=6, height=2))
            self.platforms.append(Platform(lx, 17, 6, Colors.LIGHT_BROWN, "Fallen Log"))
        self.items.append(Item('bone', 156, 15, value=25.0))
        self.items.append(Item('bone', 184, 15, value=25.0))

        # Forest floor decor: mushrooms & ferns
        for mx in (120, 133, 147, 172, 196):
            self.props.append(SceneryProp('mushroom', mx, 18, width=2, height=1))
        for fx in (117, 143, 159, 178, 203):
            self.props.append(SceneryProp('fern', fx, 18, width=3, height=1))

        # =========================================================================
        # ZONE 3: RZEKA (x: 210 - 315) — banks walkable, WATER_MIN..WATER_MAX swimmable
        # =========================================================================
        # Bank trees & rocks
        self.props.append(SceneryProp('tree', 214, 9, width=7, height=10))
        self.props.append(SceneryProp('rock', 224, 18, width=3, height=1))
        self.props.append(SceneryProp('reed', 226, 17, width=2, height=2))
        self.props.append(SceneryProp('reed', 301, 17, width=2, height=2))
        self.props.append(SceneryProp('rock', 305, 18, width=3, height=1))
        self.props.append(SceneryProp('pine', 308, 8, width=7, height=11))

        # Stepping stones & lily pads: the dry parkour route across
        self.platforms.append(Platform(240, 16, 3, Colors.GRAY, "Stepping Stone"))
        self.platforms.append(Platform(258, 15, 3, Colors.GRAY, "Stepping Stone"))
        self.platforms.append(Platform(276, 16, 3, Colors.GRAY, "Stepping Stone"))
        self.platforms.append(Platform(250, 17, 3, Colors.GRASS_GREEN, "Lily Pad"))
        self.platforms.append(Platform(285, 17, 3, Colors.GRASS_GREEN, "Lily Pad"))

        # Drifting log raft — moves on its own, carries the dog
        self.drift_log = Platform(262, 17, 6, Colors.BROWN, "Drifting Log", dx=0.25)
        self.platforms.append(self.drift_log)

        # Fish on the mid-river rock & bone on the east bank
        self.items.append(Item('fish', 259, 13, value=45.0))
        self.items.append(Item('bone', 306, 17, value=25.0))

        # =========================================================================
        # ZONE 4: PARK MIEJSKI I MOSTEK (x: 315 - 420)
        # =========================================================================
        # Big Park Tree with stepping branches
        self.props.append(SceneryProp('tree', 322, 9, width=7, height=10))
        self.platforms.append(Platform(318, 14, 15, Colors.BROWN, "Tree Branch"))
        self.platforms.append(Platform(320, 11, 11, Colors.GRASS_GREEN, "Upper Foliage"))
        self.items.append(Item('steak', 325, 9, value=50.0)) # High steak!

        self.props.append(SceneryProp('fountain', 338, 15, width=9, height=4))
        self.platforms.append(Platform(338, 16, 9, Colors.GRAY, "Fountain Ledge"))
        self.items.append(Item('treat', 342, 18, value=30.0))

        # High Wooden Bridge over the little park stream (353-375)
        self.platforms.append(Platform(355, 13, 18, Colors.BROWN, "Wooden Bridge"))
        self.items.append(Item('steak', 363, 11, value=50.0))
        
        # Park Tree connecting from bridge
        self.props.append(SceneryProp('tree', 382, 9, width=7, height=10))
        self.platforms.append(Platform(378, 11, 15, Colors.BROWN, "Bridge-to-Tree Branch"))
        self.platforms.append(Platform(380, 8, 11, Colors.GRASS_GREEN, "Top Canopy"))
        self.items.append(Item('bone', 385, 6, value=40.0)) # Sky bone!

        self.platforms.append(Platform(395, 15, 12, Colors.LIGHT_BROWN, "Picnic Table"))
        self.props.append(SceneryProp('bench', 395, 15, width=12, height=4))
        self.items.append(Item('bone', 400, 13, value=25.0))
        self.props.append(SceneryProp('hydrant', 412, 17, width=3, height=2))
        self.props.append(SceneryProp('lamp', 418, 11, width=3, height=8))

        # =========================================================================
        # ZONE 5: PSI PARK / WYBIEG DLA PSÓW (x: 420 - 525)
        # =========================================================================
        # Fence with a gate gap at 470-478
        self.props.append(SceneryProp('fence', 420, 16, width=50, height=3, label="PLOT"))
        self.props.append(SceneryProp('fence', 478, 16, width=47, height=3, label="PLOT"))
        self.props.append(SceneryProp('park_sign', 471, 15, width=7, height=4, label="PSI PARK"))

        # Hydrant Alley: mark all six for a bonus!
        for hx in (430, 437, 444, 451, 458, 465):
            self.props.append(SceneryProp('hydrant', hx, 17, width=3, height=2))

        # Ball pit with a real kickable ball & treats buried in it
        self.props.append(SceneryProp('ballpit', 482, 17, width=10, height=2))
        self.items.append(Item('treat', 486, 16, value=35.0))

        # Agility-lite tunnel (jump on top for a bone)
        self.props.append(SceneryProp('tunnel', 502, 16, width=8, height=3))
        self.platforms.append(Platform(502, 16, 8, Colors.BRIGHT_BLUE, "Tunnel Top"))
        self.items.append(Item('bone', 505, 14, value=25.0))

        # =========================================================================
        # ZONE 6: ULICA (x: 525 - 630)
        # =========================================================================
        self.props.append(SceneryProp('lamp', 532, 11, width=3, height=8))
        self.props.append(SceneryProp('bike', 542, 17, width=5, height=2))
        self.props.append(SceneryProp('traffic_light', 565, 14, width=3, height=5))
        self.props.append(SceneryProp('traffic_light', 587, 14, width=3, height=5))
        self.platforms.append(Platform(600, 15, 14, Colors.LIGHT_BROWN, "Street Bench"))
        self.props.append(SceneryProp('bench', 600, 15, width=14, height=4))
        self.props.append(SceneryProp('lamp', 622, 11, width=3, height=8))
        self.items.append(Item('treat', 606, 13, value=35.0)) # on the bench

        # =========================================================================
        # ZONE 7: SŁONECZNA PLAŻA DLA PSÓW (x: 630 - 735)
        # =========================================================================
        # Umbrellas with jumpable tops
        self.props.append(SceneryProp('umbrella', 645, 14, width=7, height=5))
        self.platforms.append(Platform(644, 14, 9, Colors.PINK, "Beach Umbrella"))
        self.items.append(Item('bone', 648, 12, value=25.0))

        self.items.append(Item('bone', 658, 18, value=25.0))
        
        self.props.append(SceneryProp('umbrella', 675, 14, width=7, height=5))
        self.platforms.append(Platform(674, 14, 9, Colors.PINK, "Beach Umbrella"))
        self.items.append(Item('steak', 678, 12, value=50.0))

        self.items.append(Item('steak', 690, 18, value=50.0))
        
        self.props.append(SceneryProp('umbrella', 708, 14, width=7, height=5))
        self.platforms.append(Platform(707, 14, 9, Colors.PINK, "Beach Umbrella"))
        self.items.append(Item('treat', 711, 12, value=35.0))
        
        self.props.append(SceneryProp('lamp', 728, 11, width=3, height=8))

        # =========================================================================
        # ZONE 8: TOR PRZESZKÓD AGILITY (x: 735 - 840)
        # =========================================================================
        self.props.append(SceneryProp('start_gate', AGILITY_GATE_X, 14, width=8, height=5, label="START"))
        
        # Hurdle 1
        self.platforms.append(Platform(755, 16, 5, Colors.BRIGHT_YELLOW, "Hurdle"))
        self.props.append(SceneryProp('hurdle', 755, 16, width=5, height=3))
        
        # Slalom Poles
        self.props.append(SceneryProp('slalom', 768, 15, width=9, height=4))
        
        # Elevated Agility Catwalk
        self.platforms.append(Platform(785, 12, 15, Colors.BRIGHT_RED, "Agility Catwalk"))
        self.items.append(Item('treat', 792, 10, value=35.0))
        
        # Agility Jump Ring / Hoop
        self.props.append(SceneryProp('hoop', 808, 13, width=6, height=6))
        self.platforms.append(Platform(807, 14, 8, Colors.BRIGHT_CYAN, "Hoop Platform"))
        self.items.append(Item('steak', 810, 12, value=50.0))
        
        # Finish Gate
        self.props.append(SceneryProp('finish_gate', 825, 14, width=8, height=5, label="META"))

    # ------------------------------------------------------------------
    def update(self, dog=None):
        self.time_tick += 1
        
        # Advance Day/Night cycle
        self.day_time = (self.day_time + self.day_speed) % 1.0

        # Update clouds
        for c in self.clouds:
            c["x"] += c["speed"]
            if c["x"] > self.width + 10:
                c["x"] = -15
                c["y"] = random.randint(1, 4)

        # Update toy balls
        for b in self.balls:
            if b.kick_cd > 0:
                b.kick_cd -= 1
            b.update(self)

        # Drifting river log (ping-pong raft the dog can ride)
        if self.drift_log:
            self.drift_log.x += self.drift_log.dx
            if self.drift_log.x < 246 or self.drift_log.x + self.drift_log.width > 296:
                self.drift_log.dx = -self.drift_log.dx

        # Pedestrian signal cycle: 200 ticks green (cars stopped), 280 red
        self.signal_tick = (self.signal_tick + 1) % 480
        self.signal_green = self.signal_tick < 200

        # Street traffic (only simulated while the dog is near the street)
        self._update_traffic(dog)

        # Respawn food items
        for it in self.items:
            if it.collected:
                it.respawn_timer -= 1
                if it.respawn_timer <= 0:
                    it.collected = False

        if dog:
            self._update_agility(dog)
            self._update_crossing(dog)
            self._update_hydrant_alley(dog)

            # Beach water splash
            beach = BY_ID["beach"]
            if beach["start"] + 10 <= dog.x <= beach["end"] - 5 and dog.on_ground and random.random() < 0.03:
                audio.play('splash')

            # Bark near the river makes a big splash
            if dog.bark_active_ticks == 14 and is_water(dog.x + dog.width / 2):
                audio.play('splash')

    # ------------------------------------------------------------------
    def _update_agility(self, dog):
        # Check Start Gate (starts when running right into the course)
        if AGILITY_START_MIN <= dog.x <= AGILITY_START_MAX and not self.agility_active:
            if dog.vx > 0 or dog.facing == "right":
                self.agility_active = True
                self.agility_start_tick = self.time_tick
                dog.say("🏁 START TORU AGILITY! BIEGNIJ!", Colors.GOLD + Colors.BOLD, 30)
                audio.play('menu_select')

        # Check if dog retreated back behind the start line (abort & reset timer)
        elif self.agility_active and dog.x < AGILITY_ABORT_X:
            self.agility_active = False
            dog.say("⏹️ Wyjście z toru – stoper zresetowany!", Colors.BRIGHT_YELLOW, 25)
            audio.play('menu_move')

        # Check Finish Gate
        elif AGILITY_FINISH_MIN <= dog.x <= AGILITY_FINISH_MAX and self.agility_active:
            self.agility_active = False
            race_ticks = self.time_tick - self.agility_start_tick
            race_sec = race_ticks / 30.0
            dog.add_xp(60.0)
            dog.bones_currency += 3
            dog.happiness = min(100.0, dog.happiness + 30.0)
            audio.play('cheer')
            if self.agility_best_time is None or race_sec < self.agility_best_time:
                self.agility_best_time = race_sec
                dog.say(f"🏆 REKORD TORU! {race_sec:.1f}s (+3 🦴 / +60 XP)", Colors.BRIGHT_GREEN + Colors.BOLD, 50)
            else:
                dog.say(f"🥇 META TORU! Czas: {race_sec:.1f}s (+3 🦴)", Colors.GOLD + Colors.BOLD, 45)

    # ------------------------------------------------------------------
    def _update_traffic(self, dog):
        s = STREET
        near_street = dog and (s["start"] - 30) <= dog.x <= (s["end"] + 25)

        if near_street:
            self.car_timer -= 1
            if self.car_timer <= 0 and len(self.cars) < 3:
                style = random.choice(['🚗', '🚙', '🚕', '🚓'])
                self.cars.append({"x": float(s["end"] + 12),
                                  "vx": -(0.9 + random.random() * 0.7),
                                  "style": style, "hit": False})
                self.car_timer = random.randint(70, 160)

        for car in self.cars:
            # Stop before the zebra crossing while the dog has green
            if self.signal_green and car["x"] > CAR_STOP_X:
                continue
            car["x"] += car["vx"]

        self.cars = [c for c in self.cars if c["x"] > s["start"] - 25]

        # Friendly scare: car brushing the dog on the road
        if dog and dog.car_grace == 0:
            dcx = dog.x + dog.width / 2
            for car in self.cars:
                if car["hit"]:
                    continue
                if abs(dcx - (car["x"] + 2)) < 3.0 and dog.y + dog.height >= self.ground_base_y - 1:
                    car["hit"] = True
                    dog.car_grace = 45
                    dog.happiness = max(0.0, dog.happiness - 5.0)
                    dog.vy = -1.3
                    dog.vx = 0.9 if dcx < car["x"] else -0.9
                    dog.on_ground = False
                    dog.say("📢 BZZZ! Uważaj na jezdni!", Colors.BRIGHT_RED + Colors.BOLD, 35)
                    audio.play('alert')
                    if self.cross_state:
                        self.cross_state["safe"] = False

    # ------------------------------------------------------------------
    def _update_crossing(self, dog):
        """Safe street crossings: use the zebra while cars are stopped."""
        s = STREET
        dcx = dog.x + dog.width / 2
        in_street = s["start"] < dcx < s["end"]

        if not in_street:
            if self.cross_state:  # exited the street
                cs = self.cross_state
                if cs["safe"] and cs.get("zebra") and cs["from"] != ("west" if dcx < s["start"] else "east"):
                    dog.crossings_safe += 1
                    dog.add_xp(5.0)
                    dog.say("🚸 Bezpieczne przejście przez ulicę! +5 XP", Colors.BRIGHT_GREEN + Colors.BOLD, 30)
                    audio.play('menu_select')
            self.cross_state = None
            return

        side = "west" if dcx < (s["start"] + s["end"]) / 2 else "east"
        if self.cross_state is None:
            self.cross_state = {"from": side, "zebra": False, "safe": True}

        if ZEBRA_MIN <= dcx <= ZEBRA_MAX:
            self.cross_state["zebra"] = True
            if not self.signal_green:
                # Jaywalking hint while cars roll through the crossing
                if random.random() < 0.02:
                    dog.say("⚠️ Uważaj, jedzie samochód! 🚗", Colors.BRIGHT_YELLOW, 20)

    # ------------------------------------------------------------------
    def _update_hydrant_alley(self, dog):
        if self.alley_bonus_done:
            return
        dp = BY_ID["dogpark"]
        alley = [p for p in self.props
                 if p.prop_type == 'hydrant' and dp["start"] <= p.x < 470]
        if alley and all(p.marked for p in alley):
            self.alley_bonus_done = True
            dog.bones_currency += 5
            dog.add_xp(20.0)
            dog.happiness = min(100.0, dog.happiness + 15.0)
            dog.say("🏆 cała Aleja Hydrantów zaznaczona! +5 🦴 +20 XP", Colors.BRIGHT_CYAN + Colors.BOLD, 60)
            audio.play('cheer')

    # ------------------------------------------------------------------
    def get_ground_y(self, x1, x2, current_bottom_y):
        """Returns highest ground/platform beneath the entity."""
        best_ground = float(self.ground_base_y)
        
        for plat in self.platforms:
            if x2 > plat.x and x1 < plat.x + plat.width:
                if current_bottom_y <= plat.y + 1.2:
                    if plat.y < best_ground:
                        best_ground = float(plat.y)
        return best_ground

    def check_item_pickup(self, dog):
        dog_center_x = dog.x + dog.width / 2
        dog_center_y = dog.y + dog.height / 2

        for item in self.items:
            if not item.collected:
                if abs(dog_center_x - item.x) < 3.0 and abs(dog_center_y - item.y) < 2.5:
                    item.collected = True
                    item.respawn_timer = 250
                    dog.eat_food(item.value)
                    return item
        return None

    def check_ball_interaction(self, dog):
        dog_center_x = dog.x + dog.width / 2
        for ball in self.balls:
            if ball.kick_cd > 0:
                continue
            if abs(dog_center_x - ball.x) < 3.0 and abs(dog.y + dog.height - (ball.y + 1)) < 2.5:
                push = 1.2 if dog.facing == "right" else -1.2
                ball.vx = push + dog.vx * 0.8
                ball.vy = -0.7
                ball.on_ground = False
                dog.happiness = min(100.0, dog.happiness + 2.0)
                dog.add_xp(2.0)
                dog.ball_fetches = getattr(dog, "ball_fetches", 0) + 1
                # Cooldown prevents standing on the ball from farming XP/happiness every frame.
                ball.kick_cd = 30
                if random.random() < 0.2:
                    dog.say("*kic! Piłeczka!* ⚽", Colors.BRIGHT_YELLOW, 18)
                break

    def check_mark_prop(self, dog):
        dog_center_x = dog.x + dog.width / 2
        for prop in self.props:
            if prop.prop_type in ['tree', 'pine', 'hydrant', 'lamp', 'umbrella', 'slalom']:
                if abs(dog_center_x - (prop.x + prop.width / 2)) < 3.5:
                    prop.marked = True
                    return prop
        return None

    def get_time_of_day_info(self):
        """Returns (phase_name, sky_color, is_night, sun_or_moon_icon)"""
        t = self.day_time
        if 0.0 <= t < 0.20:
            return ("🌅 Świt", Colors.fg256(215), False, "☀️")
        elif 0.20 <= t < 0.55:
            return ("☀️ Słoneczny Dzień", Colors.SKY_BLUE, False, "☀️")
        elif 0.55 <= t < 0.70:
            return ("🌇 Zachód Słońca", Colors.fg256(209), False, "🌅")
        else:
            return ("🌙 Gwiaździsta Noc", Colors.fg256(17), True, "🌙")
