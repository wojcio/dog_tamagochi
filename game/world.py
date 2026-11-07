"""
Expansive 2D World with 4 Biomes (Garden, Park, Beach, Agility),
Day/Night Cycle, Interactive Props, and Obstacles.
"""

import math
import random
from game.engine import Colors
from game.audio import audio

class Platform:
    def __init__(self, x, y, width, style=Colors.BROWN, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.style = style
        self.label = label

class Item:
    def __init__(self, item_type, x, y, value=35.0):
        self.item_type = item_type # 'bone', 'bowl', 'steak', 'treat', 'water'
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

        self.vx *= 0.88
        if abs(self.vx) < 0.05:
            self.vx = 0

class SceneryProp:
    def __init__(self, prop_type, x, y, width=5, height=5, label=""):
        self.prop_type = prop_type # 'tree', 'hydrant', 'doghouse', 'bench', 'lamp', 'shop', 'fountain', 'umbrella', 'slalom', 'hurdle', 'hoop', 'start_gate', 'finish_gate'
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.marked = False # Marked by pee

class World:
    def __init__(self, width=420, height=22):
        self.width = width
        self.height = height
        self.ground_base_y = 19
        
        self.platforms = []
        self.props = []
        self.items = []
        self.ball = ToyBall(45, 18)
        self.ball_kick_cooldown = 0
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

        self._generate_world()

    def _generate_world(self):
        # Generate clouds
        for i in range(12):
            cx = random.randint(5, self.width - 20)
            cy = random.randint(1, 4)
            self.clouds.append({"x": float(cx), "y": cy, "speed": random.uniform(0.02, 0.05), "type": i % 3})

        # Generate stars for night sky
        for _ in range(40):
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
        # ZONE 2: PARK MIEJSKI I MOSTEK (x: 105 - 210)
        # =========================================================================
        # Big Park Tree with stepping branches
        self.props.append(SceneryProp('tree', 112, 9, width=7, height=10))
        self.platforms.append(Platform(108, 14, 15, Colors.BROWN, "Tree Branch"))
        self.platforms.append(Platform(110, 11, 11, Colors.GRASS_GREEN, "Upper Foliage"))
        self.items.append(Item('steak', 115, 9, value=50.0)) # High steak!

        self.props.append(SceneryProp('fountain', 128, 15, width=9, height=4))
        self.platforms.append(Platform(128, 16, 9, Colors.GRAY, "Fountain Ledge"))
        self.items.append(Item('treat', 132, 18, value=30.0))

        # High Wooden Bridge Platform
        self.platforms.append(Platform(145, 13, 18, Colors.BROWN, "Wooden Bridge"))
        self.items.append(Item('steak', 153, 11, value=50.0))
        
        # Park Tree connecting from bridge
        self.props.append(SceneryProp('tree', 172, 9, width=7, height=10))
        self.platforms.append(Platform(168, 11, 15, Colors.BROWN, "Bridge-to-Tree Branch"))
        self.platforms.append(Platform(170, 8, 11, Colors.GRASS_GREEN, "Top Canopy"))
        self.items.append(Item('bone', 175, 6, value=40.0)) # Sky bone!

        self.platforms.append(Platform(185, 15, 12, Colors.LIGHT_BROWN, "Picnic Table"))
        self.props.append(SceneryProp('bench', 185, 15, width=12, height=4))
        self.items.append(Item('bone', 190, 13, value=25.0))
        self.props.append(SceneryProp('hydrant', 202, 17, width=3, height=2))
        self.props.append(SceneryProp('lamp', 208, 11, width=3, height=8))

        # =========================================================================
        # ZONE 3: SŁONECZNA PLAŻA DLA PSÓW (x: 210 - 315)
        # =========================================================================
        # Umbrellas with jumpable tops
        self.props.append(SceneryProp('umbrella', 225, 14, width=7, height=5))
        self.platforms.append(Platform(224, 14, 9, Colors.PINK, "Beach Umbrella"))
        self.items.append(Item('bone', 228, 12, value=25.0))

        self.items.append(Item('bone', 238, 18, value=25.0))
        
        self.props.append(SceneryProp('umbrella', 255, 14, width=7, height=5))
        self.platforms.append(Platform(254, 14, 9, Colors.PINK, "Beach Umbrella"))
        self.items.append(Item('steak', 258, 12, value=50.0))

        self.items.append(Item('steak', 270, 18, value=50.0))
        
        self.props.append(SceneryProp('umbrella', 288, 14, width=7, height=5))
        self.platforms.append(Platform(287, 14, 9, Colors.PINK, "Beach Umbrella"))
        self.items.append(Item('treat', 291, 12, value=35.0))
        
        self.props.append(SceneryProp('lamp', 308, 11, width=3, height=8))

        # =========================================================================
        # ZONE 4: TOR PRZESZKÓD AGILITY (x: 315 - 420)
        # =========================================================================
        self.props.append(SceneryProp('start_gate', 320, 14, width=8, height=5, label="START"))
        
        # Hurdle 1
        self.platforms.append(Platform(335, 16, 5, Colors.BRIGHT_YELLOW, "Hurdle"))
        self.props.append(SceneryProp('hurdle', 335, 16, width=5, height=3))
        
        # Slalom Poles
        self.props.append(SceneryProp('slalom', 348, 15, width=9, height=4))
        
        # Elevated Agility Catwalk
        self.platforms.append(Platform(365, 12, 15, Colors.BRIGHT_RED, "Agility Catwalk"))
        self.items.append(Item('treat', 372, 10, value=35.0))
        
        # Agility Jump Ring / Hoop
        self.props.append(SceneryProp('hoop', 388, 13, width=6, height=6))
        self.platforms.append(Platform(387, 14, 8, Colors.BRIGHT_CYAN, "Hoop Platform"))
        self.items.append(Item('steak', 390, 12, value=50.0))
        
        # Finish Gate
        self.props.append(SceneryProp('finish_gate', 405, 14, width=8, height=5, label="META"))

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

        # Update toy ball
        self.ball.update(self)

        # Respawn food items
        for it in self.items:
            if it.collected:
                it.respawn_timer -= 1
                if it.respawn_timer <= 0:
                    it.collected = False

        # Agility Course Race Logic
        if dog:
            # Check Start Gate (starts when running right into the course)
            if 318 <= dog.x <= 324 and not self.agility_active:
                if dog.vx > 0 or dog.facing == "right":
                    self.agility_active = True
                    self.agility_start_tick = self.time_tick
                    dog.say("🏁 START TORU AGILITY! BIEGNIJ!", Colors.GOLD + Colors.BOLD, 30)
                    audio.play('menu_select')

            # Check if dog retreated back behind the start line (abort & reset timer)
            elif self.agility_active and dog.x < 316:
                self.agility_active = False
                dog.say("⏹️ Wyjście z toru – stoper zresetowany!", Colors.BRIGHT_YELLOW, 25)
                audio.play('menu_move')

            # Check Finish Gate
            elif 403 <= dog.x <= 409 and self.agility_active:
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

            # Beach water splash
            if 220 <= dog.x <= 310 and dog.on_ground and random.random() < 0.03:
                audio.play('splash')

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
        if self.ball_kick_cooldown > 0:
            self.ball_kick_cooldown -= 1
            return

        dog_center_x = dog.x + dog.width / 2
        if abs(dog_center_x - self.ball.x) < 3.0 and abs(dog.y + dog.height - (self.ball.y + 1)) < 2.5:
            push = 1.2 if dog.facing == "right" else -1.2
            self.ball.vx = push + dog.vx * 0.8
            self.ball.vy = -0.7
            self.ball.on_ground = False
            dog.happiness = min(100.0, dog.happiness + 2.0)
            dog.add_xp(2.0)
            dog.ball_fetches = getattr(dog, "ball_fetches", 0) + 1
            # Cooldown prevents standing on the ball from farming XP/happiness every frame.
            self.ball_kick_cooldown = 30
            if random.random() < 0.2:
                dog.say("*kic! Piłeczka!* ⚽", Colors.BRIGHT_YELLOW, 18)

    def check_mark_prop(self, dog):
        dog_center_x = dog.x + dog.width / 2
        for prop in self.props:
            if prop.prop_type in ['tree', 'hydrant', 'lamp', 'umbrella', 'slalom']:
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

    def get_zone_info(self, x):
        """Returns (zone_name, zone_emoji, zone_color)"""
        if x < 105:
            return ("Ogród & Dom", "🏡", Colors.BRIGHT_GREEN)
        elif x < 210:
            return ("Park Miejski", "🌳", Colors.GREEN)
        elif x < 315:
            return ("Plaża dla Psów", "🏖️", Colors.GOLD)
        else:
            return ("Tor Agility", "🏆", Colors.BRIGHT_CYAN)
