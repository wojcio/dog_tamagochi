"""
Dog entity with multiple breeds, multi-line colored ASCII sprites, physics and Tamagotchi needs.
"""

from game.engine import Colors
from game.audio import audio

class DogBreed:
    def __init__(self, name, description, color, fur_color, secondary_color):
        self.name = name
        self.description = description
        self.color = color
        self.fur = fur_color
        self.secondary = secondary_color

BREEDS = {
    "corgi": DogBreed(
        "Corgi",
        "Krótkie łapki, puszysty tyłeczek i wieczna radość!",
        Colors.ORANGE,
        Colors.ORANGE,
        Colors.WHITE
    ),
    "dachshund": DogBreed(
        "Jamnik",
        "Długi jak paróweczka, sprytny i czujny tropiciel!",
        Colors.BROWN,
        Colors.BROWN,
        Colors.LIGHT_BROWN
    ),
    "setter": DogBreed(
        "Seter Irlandzki",
        "Dostojny arystokrata o mahoniowej sierści i wdzięku!",
        Colors.fg256(166),
        Colors.fg256(166),
        Colors.fg256(208)
    ),
    "shiba": DogBreed(
        "Shiba Inu (Pieseł)",
        "Much wow! Duma, zawinięty ogonek i wesoły uśmiech!",
        Colors.GOLD,
        Colors.GOLD,
        Colors.CREAM
    ),
    "poodle": DogBreed(
        "Pudel",
        "Kędzierzawy elegancik z mięciutką fryzurą!",
        Colors.BRIGHT_WHITE,
        Colors.BRIGHT_WHITE,
        Colors.PINK
    )
}

TRICKS = {
    "1": {"id": "sit", "name": "Siad! 🧘", "lvl": 1, "desc": "Piesek siada grzecznie i macha ogonkiem"},
    "2": {"id": "paw", "name": "Daj łapę! 🐾", "lvl": 2, "desc": "Piesek podaje łapkę z uśmiechem"},
    "3": {"id": "roll", "name": "Turlaj się! 🌀", "lvl": 3, "desc": "Piesek robi obrót na trawie"},
    "4": {"id": "backflip", "name": "Superskok! 🦘", "lvl": 4, "desc": "Wysoki akrobatyczny skok"},
    "5": {"id": "play_dead", "name": "Zdechł pies! 🎭", "lvl": 5, "desc": "Zabawna poza łapkami w górę"}
}

SHOP_ITEMS = {
    "tophat": {"name": "🎩 Cylinder Gentelmana", "price": 5, "icon": "🎩"},
    "bow": {"name": "🎀 Różowa Kokardka", "price": 4, "icon": "🎀"},
    "glasses": {"name": "🕶️ Stylowe Okulary", "price": 6, "icon": "🕶️"},
    "crown": {"name": "👑 Złota Korona Króla", "price": 10, "icon": "👑"},
    "scarf": {"name": "🧣 Ciepły Szalik", "price": 4, "icon": "🧣"}
}

class Dog:
    def __init__(self, breed_key="corgi", x=10.0, y=18.0):
        self.breed_key = breed_key
        self.breed = BREEDS.get(breed_key, BREEDS["corgi"])
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = "right"
        self.state = "idle" # idle, walk, jump, bark, pet, pee, sleep, eat, sit, paw, roll, backflip, play_dead
        self.state_timer = 0
        self.on_ground = True
        
        # Dimensions
        self.width = 6
        self.height = 3

        # Tamagotchi stats (0 to 100)
        self.hunger = 85.0     # 100 = syty, 0 = głodny
        self.happiness = 90.0  # 100 = przeszczęśliwy, 0 = smutny
        self.bladder = 20.0    # 0 = pusty pęcherz, 100 = pilna potrzeba!
        self.energy = 100.0    # 100 = wypoczęty, 0 = padnięty
        
        # XP, Leveling & Currency
        self.xp = 0.0
        self.level = 1
        self.bones_currency = 3 # Starting currency for treats
        self.equipped_item = None # 'tophat', 'bow', 'glasses', 'crown', 'scarf'
        self.inventory = [] # list of owned item keys

        # Counters & Achievements
        self.bones_eaten = 0
        self.times_petted = 0
        self.peeled_spots = 0
        self.tricks_performed = 0
        self.walk_distance = 0.0
        self.bark_active_ticks = 0
        self.speech_bubble = None # (text, color, ticks_remaining)

        self.anim_tick = 0

    def add_xp(self, amount):
        self.xp += amount
        needed = self.level * 100
        if self.xp >= needed and self.level < 10:
            self.xp -= needed
            self.level += 1
            self.bones_currency += 3
            audio.play('level_up')
            unlocked = [t['name'] for t in TRICKS.values() if t['lvl'] == self.level]
            unlock_msg = f" Nowy trik: {unlocked[0]}!" if unlocked else ""
            self.say(f"⭐ AWANS NA POZIOM {self.level}!{unlock_msg} ⭐", Colors.GOLD + Colors.BOLD, 45)

    def perform_trick(self, trick_key):
        trick = TRICKS.get(trick_key)
        if not trick:
            return False
        if self.level < trick['lvl']:
            self.say(f"🔒 Wymagany Poziom {trick['lvl']} dla '{trick['name']}'!", Colors.BRIGHT_RED, 25)
            audio.play('alert')
            return False
        if self.energy < 15:
            self.say("Jestem za bardzo zmęczony na triki... 💤", Colors.BRIGHT_YELLOW, 25)
            return False

        self.state = trick['id']
        self.state_timer = 28
        self.vx = 0
        self.tricks_performed += 1
        self.energy = max(0.0, self.energy - 8.0)
        self.happiness = min(100.0, self.happiness + 15.0)
        self.add_xp(25.0)
        audio.play('trick')

        if trick['id'] == 'sit':
            self.say("Grzeczny piesek! *siad* 🧘", Colors.BRIGHT_GREEN, 25)
        elif trick['id'] == 'paw':
            self.say("*podaje łapkę* Cześć! 🐾", Colors.BRIGHT_YELLOW, 25)
        elif trick['id'] == 'roll':
            self.say("*fikołek na trawie!* 🌀", Colors.BRIGHT_CYAN, 25)
        elif trick['id'] == 'backflip':
            self.vy = -1.6
            self.on_ground = False
            self.say("SUPERSKOK! WOO-HOO! 🦘", Colors.GOLD, 25)
        elif trick['id'] == 'play_dead':
            self.say("... *zdechł pies* 🎭", Colors.PINK, 28)

        return True

    def update_physics(self, world):
        self.anim_tick += 1
        
        # Apply smooth gravity
        if not self.on_ground:
            self.vy += 0.32
            if self.vy > 1.8:
                self.vy = 1.8
        
        # Horizontal movement
        new_x = self.x + self.vx
        # Clamp horizontal to world bounds
        if new_x < 1:
            new_x = 1
            self.vx = 0
        elif new_x > world.width - self.width - 1:
            new_x = world.width - self.width - 1
            self.vx = 0
        self.x = new_x
        
        # Vertical movement & robust one-way platform collision
        old_bottom = self.y + self.height
        new_bottom = old_bottom + self.vy
        
        landed_plat_y = None
        # Land on platforms only when descending
        if self.vy >= 0:
            for plat in world.platforms:
                if (self.x + self.width - 0.5 > plat.x) and (self.x + 0.5 < plat.x + plat.width):
                    if old_bottom <= plat.y + 1.3 and new_bottom >= plat.y - 0.2:
                        if landed_plat_y is None or plat.y < landed_plat_y:
                            landed_plat_y = float(plat.y)

        effective_ground = landed_plat_y if landed_plat_y is not None else float(world.ground_base_y)
        
        if new_bottom >= effective_ground:
            self.y = effective_ground - self.height
            self.vy = 0
            self.on_ground = True
        else:
            self.y += self.vy
            self.on_ground = False
            
        # Friction
        if self.on_ground:
            self.vx *= 0.65
            if abs(self.vx) < 0.05:
                self.vx = 0

        # State management
        if self.state_timer > 0:
            self.state_timer -= 1
            if self.state_timer == 0:
                self.state = "idle"

        if self.bark_active_ticks > 0:
            self.bark_active_ticks -= 1

        if self.speech_bubble:
            txt, col, left = self.speech_bubble
            if left > 1:
                self.speech_bubble = (txt, col, left - 1)
            else:
                self.speech_bubble = None

        if self.state not in ["bark", "pet", "pee", "sleep", "eat"]:
            if not self.on_ground:
                self.state = "jump"
            elif abs(self.vx) > 0.1:
                self.state = "walk"
            else:
                self.state = "idle"

    def move_left(self):
        if self.state in ["pee", "sleep"]:
            return
        speed = 0.85 if self.energy > 20 else 0.5
        self.vx = -speed
        self.facing = "left"
        self.walk_distance += 0.2
        self.energy = max(0.0, self.energy - 0.03)

    def move_right(self):
        if self.state in ["pee", "sleep"]:
            return
        speed = 0.85 if self.energy > 20 else 0.5
        self.vx = speed
        self.facing = "right"
        self.walk_distance += 0.2
        self.energy = max(0.0, self.energy - 0.03)

    def jump(self):
        if self.on_ground and self.state not in ["pee", "sleep"]:
            jump_power = -2.2 if self.energy > 15 else -1.75
            self.vy = jump_power
            self.on_ground = False
            self.energy = max(0.0, self.energy - 0.5)
            audio.play('jump')

    def drop_down(self, world):
        if self.on_ground and (self.y + self.height) < world.ground_base_y - 0.5:
            self.y += 1.4
            self.vy = 0.6
            self.on_ground = False

    def bark(self):
        self.state = "bark"
        self.state_timer = 12
        self.bark_active_ticks = 15
        barks = ["HAU! HAU!", "WOF!", "HAUUU~!", "AWOOO! 🐺", "HAU! 🐾"]
        import random
        self.say(random.choice(barks), Colors.BRIGHT_YELLOW, 20)
        audio.play('bark')
        self.happiness = min(100.0, self.happiness + 1.0)
        self.energy = max(0.0, self.energy - 0.3)

    def pee(self):
        if self.on_ground:
            self.state = "pee"
            self.state_timer = 25
            self.vx = 0
            self.peeled_spots += 1
            self.bladder = max(0.0, self.bladder - 60.0)
            self.happiness = min(100.0, self.happiness + 15.0)
            self.add_xp(10.0)
            self.say("*pssszzt* Ulga! 💧", Colors.BRIGHT_CYAN, 25)
            audio.play('pee')

    def sleep(self):
        if self.state == "sleep":
            # Wake up
            self.state = "idle"
            self.state_timer = 0
            self.say("*ziewa* Dzień dobry! ☀️", Colors.BRIGHT_YELLOW, 25)
            audio.play('menu_select')
        else:
            # Check proximity to doghouse (x: 3 - 17)
            if 3.0 <= self.x <= 17.0:
                self.state = "sleep"
                self.state_timer = 999999
                self.vx = 0
                self.say("Zzz... Kocyk w budzie! 💤🛏️", Colors.CYAN + Colors.BOLD, 30)
                audio.play('sleep')
            else:
                self.say("Muszę wrócić do budy 🏠, żeby się wyspać!", Colors.BRIGHT_YELLOW, 30)
                audio.play('alert')

    def eat_food(self, amount=35.0):
        self.state = "eat"
        self.state_timer = 18
        self.hunger = min(100.0, self.hunger + amount)
        self.happiness = min(100.0, self.happiness + 10.0)
        self.bones_eaten += 1
        self.bones_currency += 1
        self.add_xp(15.0)
        self.say("MNIAM! *chrup chrup* 🍖 (+1 🦴)", Colors.BRIGHT_GREEN, 25)
        audio.play('eat')

    def receive_pet(self, npc_name="Przechodzień"):
        self.state = "pet"
        self.state_timer = 20
        self.happiness = min(100.0, self.happiness + 25.0)
        self.times_petted += 1
        self.add_xp(20.0)
        pet_reactions = ["*macha ogonkiem* ♥", "Uwielbiam głaski! ♥", "Aww! <3", "Merd! Merd! ♥"]
        import random
        self.say(random.choice(pet_reactions), Colors.PINK, 25)
        audio.play('pet')

    def say(self, text, color=Colors.BRIGHT_WHITE, duration=30):
        self.speech_bubble = (text, color, duration)

    def update_tamagotchi(self):
        """Called periodically (e.g. 1 tick per sec or every frame at low rate)"""
        # Hunger increases (stat drops)
        self.hunger = max(0.0, self.hunger - 0.04)
        
        # Bladder fills
        self.bladder = min(100.0, self.bladder + 0.03)

        # Sleep inside doghouse restores energy fast
        if self.state == "sleep":
            self.energy = min(100.0, self.energy + 0.75)
            self.happiness = min(100.0, self.happiness + 0.05)
            if self.energy >= 100.0:
                # Fully rested! Auto wake up
                self.state = "idle"
                self.state_timer = 0
                self.say("⚡ Wypoczęty i gotowy na sztuczki! ☀️", Colors.BRIGHT_GREEN + Colors.BOLD, 40)
                audio.play('level_up')
            elif int(self.anim_tick) % 18 == 0:
                self.say("Zzz... Regeneracja ⚡💤", Colors.CYAN, 16)
        else:
            # Idle slow energy restore if resting
            if self.state == "idle" and self.energy < 100:
                self.energy = min(100.0, self.energy + 0.02)

        # Happiness dynamics
        if self.hunger < 25:
            self.happiness = max(0.0, self.happiness - 0.08)
            if int(self.anim_tick) % 90 == 0 and not self.speech_bubble:
                self.say("Jestem głodny... Daj smaczka! 🦴", Colors.BRIGHT_RED, 30)
                audio.play('alert')
        elif self.bladder > 80:
            self.happiness = max(0.0, self.happiness - 0.08)
            if int(self.anim_tick) % 90 == 0 and not self.speech_bubble:
                self.say("Chcę siku! Wyprowadź mnie! 💧", Colors.BRIGHT_YELLOW, 30)
                audio.play('alert')
        else:
            # Slow happiness drain if no interaction
            self.happiness = max(10.0, self.happiness - 0.01)

    def get_status_mood(self):
        """Returns mood emoji and title"""
        if self.state == "sleep":
            return "😴 Śpi smacznie", Colors.CYAN
        if self.hunger < 20:
            return "🤤 Głodny wilk", Colors.BRIGHT_RED
        if self.bladder > 85:
            return "😣 Chce na spacer/siku!", Colors.BRIGHT_YELLOW
        if self.happiness > 80:
            return "🥰 Wniebowzięty!", Colors.BRIGHT_GREEN
        if self.happiness > 50:
            return "😊 Zadowolony", Colors.GREEN
        return "🥺 Smutny (pogłaszcz mnie!)", Colors.BRIGHT_MAGENTA

    def get_sprite(self):
        """Returns colored multi-line sprite matrix based on breed, state, and facing."""
        fur = self.breed.fur
        sec = self.breed.secondary
        c_eye = Colors.BRIGHT_BLACK
        c_pink = Colors.PINK
        c_wet = Colors.BRIGHT_CYAN
        
        walk_leg = (self.anim_tick // 4) % 2
        tail_wag = (self.anim_tick // 3) % 2

        # Universal trick animations
        if self.state == "sit":
            return [
                [(' ', fur), ('/', fur), ('^', fur), ('^', fur), ('\\', fur), (' ', fur)],
                [('(', fur), ('^', c_pink), ('ω', fur), ('^', c_pink), (')', fur), ('~', sec)],
                [('(', sec), ('u', sec), ('_', sec), ('u', sec), (')', sec), (' ', fur)]
            ]
        if self.state == "paw":
            paw_dir = ('\\', 'o') if self.facing == "right" else ('o', '/')
            return [
                [(' ', fur), ('/', fur), ('^', fur), ('^', fur), ('\\', fur), (' ', fur)],
                [('(', fur), ('•', c_eye), ('ω', fur), ('•', c_eye), (')', fur), ('~', sec)],
                [(' ', sec), (paw_dir[0], Colors.GOLD), (paw_dir[1], Colors.GOLD), (' ', sec), ('|', sec), (' ', sec)]
            ]
        if self.state == "roll":
            phase = (self.anim_tick // 3) % 2
            if phase == 0:
                return [
                    [(' ', fur), ('(', sec), ('_', sec), ('_', sec), (')', sec), (' ', fur)],
                    [('(', fur), ('•', c_eye), ('o', fur), ('•', c_eye), (')', fur), ('~', sec)],
                    [(' ', fur), ('/', sec), (' ', sec), ('\\', sec), (' ', fur), (' ', fur)]
                ]
            else:
                return [
                    [(' ', fur), ('\\', sec), (' ', sec), ('/', sec), (' ', fur), (' ', fur)],
                    [('(', fur), ('•', c_eye), ('o', fur), ('•', c_eye), (')', fur), ('~', sec)],
                    [(' ', fur), ('(', sec), ('^', sec), ('^', sec), (')', sec), (' ', fur)]
                ]
        if self.state == "play_dead":
            return [
                [(' ', fur), ('\\', sec), (' ', sec), ('/', sec), (' ', fur), (' ', fur)],
                [('(', fur), ('x', Colors.BRIGHT_RED), ('_', fur), ('x', Colors.BRIGHT_RED), (')', fur), ('~', fur)],
                [(' ', fur), (' ', fur), (' ', fur), (' ', fur), (' ', fur), (' ', fur)]
            ]

        # Sprites by Breed
        if self.breed_key == "corgi":
            if self.state == "sleep":
                return [
                    [(' ', fur), (' ', fur), ('z', Colors.CYAN), ('Z', Colors.CYAN), (' ', fur), (' ', fur)],
                    [('(', fur), ('-', c_eye), ('ω', fur), ('-', c_eye), (')', fur), ('~', fur)],
                    [('(', sec), ('_', sec), ('u', sec), ('u', sec), (')', sec), ('z', Colors.CYAN)]
                ]
            if self.state == "pee":
                if self.facing == "right":
                    return [
                        [(' ', fur), (' ', fur), ('/', fur), ('^', fur), ('^', fur), ('\\', fur)],
                        [('(', fur), ('•', c_eye), ('ω', fur), ('•', c_eye), (')', fur), (' ', fur)],
                        [('(', sec), ('/', sec), ('|', sec), ('\\', sec), ('`', c_wet), ('💧', Colors.BRIGHT_CYAN)]
                    ]
                else:
                    return [
                        [('/', fur), ('^', fur), ('^', fur), ('\\', fur), (' ', fur), (' ', fur)],
                        [(' ', fur), ('(', fur), ('•', c_eye), ('ω', fur), ('•', c_eye), (')', fur)],
                        [('💧', Colors.BRIGHT_CYAN), ('´', c_wet), ('/', sec), ('|', sec), ('\\', sec), (')', sec)]
                    ]
            if self.facing == "right":
                tail = ')' if tail_wag == 0 else '('
                leg1 = '/' if walk_leg == 0 else '|'
                leg2 = '\\' if walk_leg == 0 else '|'
                bark_m = 'O' if self.state == "bark" else 'ω'
                return [
                    [(' ', fur), ('/', fur), ('^', fur), ('^', fur), ('\\', fur), (' ', fur)],
                    [('(', fur), ('•', c_eye), (bark_m, fur), ('•', c_eye), (')', fur), (tail, sec)],
                    [(' ', sec), (leg1, sec), (' ', sec), (leg2, sec), (' ', sec), (' ', sec)]
                ]
            else: # left
                tail = '(' if tail_wag == 0 else ')'
                leg1 = '\\' if walk_leg == 0 else '|'
                leg2 = '/' if walk_leg == 0 else '|'
                bark_m = 'O' if self.state == "bark" else 'ω'
                return [
                    [(' ', fur), ('/', fur), ('^', fur), ('^', fur), ('\\', fur), (' ', fur)],
                    [(tail, sec), ('(', fur), ('•', c_eye), (bark_m, fur), ('•', c_eye), (')', fur)],
                    [(' ', sec), (' ', sec), (leg1, sec), (' ', sec), (leg2, sec), (' ', sec)]
                ]

        elif self.breed_key == "dachshund": # Jamnik - Długi piesek!
            self.width = 8
            if self.state == "sleep":
                return [
                    [(' ', fur), (' ', fur), (' ', fur), (' ', fur), (' ', fur), ('z', Colors.CYAN), ('Z', Colors.CYAN), (' ', fur)],
                    [('(', fur), ('-', c_eye), ('..', fur), ('-', c_eye), (')', fur), ('=', fur), ('=', fur), ('~', fur)],
                    [(' ', fur), ('u', sec), ('-', sec), ('-', sec), ('-', sec), ('-', sec), ('u', sec), (' ', fur)]
                ]
            if self.facing == "right":
                tail = '~' if tail_wag == 0 else '^'
                leg1 = '/' if walk_leg == 0 else '|'
                leg2 = '\\' if walk_leg == 0 else '|'
                m = 'V' if self.state == "bark" else 'o'
                return [
                    [(' ', fur), (' ', fur), ('(', fur), ('`', fur), ('.', fur), ('´', fur), (')', fur), (' ', fur)],
                    [('(', fur), ('•', c_eye), (m, fur), ('•', c_eye), ('=', fur), ('=', fur), ('=', fur), (tail, fur)],
                    [(' ', fur), (leg1, sec), (' ', sec), (' ', sec), (' ', sec), (' ', sec), (leg2, sec), (' ', fur)]
                ]
            else:
                tail = '~' if tail_wag == 0 else '^'
                leg1 = '\\' if walk_leg == 0 else '|'
                leg2 = '/' if walk_leg == 0 else '|'
                m = 'V' if self.state == "bark" else 'o'
                return [
                    [(' ', fur), ('(', fur), ('`', fur), ('.', fur), ('´', fur), (')', fur), (' ', fur), (' ', fur)],
                    [(tail, fur), ('=', fur), ('=', fur), ('=', fur), ('(', fur), ('•', c_eye), (m, fur), ('•', c_eye)],
                    [(' ', fur), (leg1, sec), (' ', sec), (' ', sec), (' ', sec), (' ', sec), (leg2, sec), (' ', fur)]
                ]

        elif self.breed_key == "setter": # Seter Irlandzki (Mahoniowy, elegancki, z pióropuszem)
            if self.state == "sleep":
                return [
                    [(' ', fur), ('(', fur), ('~', sec), ('~', sec), (')', fur), ('z', Colors.CYAN), ('Z', Colors.CYAN)],
                    [('(', fur), ('-', c_eye), ('v', fur), ('-', c_eye), (')', fur), ('~', sec), ('~', sec)],
                    [(' ', fur), ('(', sec), ('_', sec), ('_', sec), (')', sec), (' ', fur), (' ', fur)]
                ]
            if self.facing == "right":
                tail = ('~', '>') if tail_wag == 0 else ('-', '>')
                leg1 = '/' if walk_leg == 0 else '|'
                leg2 = '\\' if walk_leg == 0 else '|'
                m = 'V' if self.state == "bark" else 'v'
                return [
                    [(' ', fur), ('(', fur), ('~', sec), ('~', sec), (')', fur), (' ', fur), (' ', fur)],
                    [('(', fur), ('•', c_eye), (m, fur), ('•', c_eye), (')', fur), (tail[0], sec), (tail[1], sec)],
                    [(' ', sec), (leg1, fur), ('~', sec), (leg2, fur), ('~', sec), (' ', sec), (' ', sec)]
                ]
            else:
                tail = ('<', '~') if tail_wag == 0 else ('<', '-')
                leg1 = '\\' if walk_leg == 0 else '|'
                leg2 = '/' if walk_leg == 0 else '|'
                m = 'V' if self.state == "bark" else 'v'
                return [
                    [(' ', fur), (' ', fur), ('(', fur), ('~', sec), ('~', sec), (')', fur), (' ', fur)],
                    [(tail[0], sec), (tail[1], sec), ('(', fur), ('•', c_eye), (m, fur), ('•', c_eye), (')', fur)],
                    [(' ', sec), (' ', sec), (leg1, fur), ('~', sec), (leg2, fur), ('~', sec), (' ', sec)]
                ]

        elif self.breed_key == "shiba": # Pieseł
            if self.state == "sleep":
                return [
                    [(' ', fur), ('^', sec), ('_', sec), ('^', sec), (' ', fur), ('z', Colors.CYAN)],
                    [('(', fur), ('u', c_eye), ('ᴥ', sec), ('u', c_eye), (')', fur), ('@', fur)],
                    [(' ', sec), ('u', sec), ('_', sec), ('u', sec), (' ', sec), (' ', sec)]
                ]
            if self.facing == "right":
                tail = '@' if tail_wag == 0 else 'Q'
                leg1 = '/' if walk_leg == 0 else '|'
                leg2 = '\\' if walk_leg == 0 else '|'
                m = 'O' if self.state == "bark" else 'ᴥ'
                return [
                    [(' ', fur), ('^', sec), ('_', sec), ('^', sec), (' ', fur), (' ', fur)],
                    [('(', fur), ('•', c_eye), (m, sec), ('•', c_eye), (')', fur), (tail, fur)],
                    [(' ', sec), (leg1, sec), (' ', sec), (leg2, sec), (' ', sec), (' ', sec)]
                ]
            else:
                tail = '@' if tail_wag == 0 else 'Q'
                leg1 = '\\' if walk_leg == 0 else '|'
                leg2 = '/' if walk_leg == 0 else '|'
                m = 'O' if self.state == "bark" else 'ᴥ'
                return [
                    [(' ', fur), (' ', fur), ('^', sec), ('_', sec), ('^', sec), (' ', fur)],
                    [(tail, fur), ('(', fur), ('•', c_eye), (m, sec), ('•', c_eye), (')', fur)],
                    [(' ', sec), (' ', sec), (leg1, sec), (' ', sec), (leg2, sec), (' ', sec)]
                ]

        else: # Poodle / Kundelek
            if self.state == "sleep":
                return [
                    [(' ', fur), ('8', c_pink), ('8', c_pink), ('8', fur), ('z', Colors.CYAN), ('Z', Colors.CYAN)],
                    [('(', fur), ('-', c_eye), ('w', fur), ('-', c_eye), (')', fur), ('*', fur)],
                    [(' ', fur), ('c', sec), ('_', sec), ('c', sec), (' ', fur), (' ', fur)]
                ]
            if self.facing == "right":
                tail = '*' if tail_wag == 0 else 'o'
                leg1 = '/' if walk_leg == 0 else '|'
                leg2 = '\\' if walk_leg == 0 else '|'
                m = 'O' if self.state == "bark" else 'w'
                return [
                    [(' ', fur), ('8', c_pink), ('8', c_pink), ('8', fur), (' ', fur), (' ', fur)],
                    [('(', fur), ('•', c_eye), (m, fur), ('•', c_eye), (')', fur), (tail, fur)],
                    [(' ', sec), (leg1, sec), (' ', sec), (leg2, sec), (' ', sec), (' ', sec)]
                ]
            else:
                tail = '*' if tail_wag == 0 else 'o'
                leg1 = '\\' if walk_leg == 0 else '|'
                leg2 = '/' if walk_leg == 0 else '|'
                m = 'O' if self.state == "bark" else 'w'
                return [
                    [(' ', fur), (' ', fur), ('8', c_pink), ('8', c_pink), ('8', fur), (' ', fur)],
                    [(tail, fur), ('(', fur), ('•', c_eye), (m, fur), ('•', c_eye), (')', fur)],
                    [(' ', sec), (leg1, sec), (' ', sec), (leg2, sec), (' ', sec), (' ', sec)]
                ]

