"""
NPC entities: Friendly humans for petting, birds (pigeons) to chase, and cats.
"""

import random
from game.engine import Colors
from game.audio import audio

class HumanNPC:
    def __init__(self, name, x, y, role="Przechodzień", color=Colors.CYAN, min_x=20, max_x=80):
        self.name = name
        self.role = role
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.min_x = min_x
        self.max_x = max_x
        self.vx = random.choice([0.15, -0.15])
        self.facing = "right" if self.vx > 0 else "left"
        self.state = "walk" # walk, pet, talk, wave
        self.state_timer = 0
        self.speech_bubble = None # (text, color, ticks)
        self.pet_cooldown = 0
        self.anim_tick = 0

    def update(self, dog, world):
        self.anim_tick += 1
        if self.pet_cooldown > 0:
            self.pet_cooldown -= 1

        if self.speech_bubble:
            txt, col, left = self.speech_bubble
            if left > 1:
                self.speech_bubble = (txt, col, left - 1)
            else:
                self.speech_bubble = None

        if self.state_timer > 0:
            self.state_timer -= 1
            if self.state_timer == 0:
                self.state = "walk"
            return

        # Regular patrolling
        self.x += self.vx
        if self.x <= self.min_x:
            self.x = self.min_x
            self.vx = abs(self.vx)
            self.facing = "right"
        elif self.x >= self.max_x:
            self.x = self.max_x
            self.vx = -abs(self.vx)
            self.facing = "left"

        # Check proximity to dog
        dog_dist = abs((dog.x + dog.width/2) - (self.x + 1.5))
        if dog_dist < 4.0 and abs(dog.y - self.y) < 3.0:
            if dog.bark_active_ticks > 0 and self.pet_cooldown == 0:
                # Dog barked near human! Human notices and pets
                self.interact_pet(dog)

    def interact_pet(self, dog):
        self.state = "pet"
        self.state_timer = 30
        self.pet_cooldown = 100
        dog.receive_pet(self.name)
        
        phrases = [
            f"Ooo, jaki słodki {dog.breed.name}! *głask głask* ♥",
            "Kto jest dobrym pieskiem? Ty jesteś! ♥",
            "Ale masz mięciutkie futerko! *miziu miziu* ♥",
            "Aww, zamerdał ogonkiem! *czochranie* ♥",
            "Cześć maluchu! Masz mnóstwo energii! ♥"
        ]
        self.say(random.choice(phrases), Colors.PINK, 35)

    def say(self, text, color=Colors.BRIGHT_WHITE, duration=35):
        self.speech_bubble = (text, color, duration)

    def get_sprite(self):
        """Returns 3-line human ASCII art"""
        head_c = Colors.BRIGHT_YELLOW
        body_c = self.color
        leg_c = Colors.BLUE
        
        step = (self.anim_tick // 6) % 2
        
        if self.state == "pet":
            return [
                [(' ', body_c), ('(', head_c), ('^', head_c), ('_', head_c), ('^', head_c), (')', head_c), ('♥', Colors.RED)],
                [(' ', body_c), ('/', body_c), ('|', body_c), ('\\', body_c), ('~', Colors.PINK), (' ', body_c), (' ', body_c)],
                [(' ', leg_c), ('/', leg_c), (' ', leg_c), ('\\', leg_c), (' ', leg_c), (' ', leg_c), (' ', leg_c)]
            ]
        
        leg1 = '/' if step == 0 else '|'
        leg2 = '\\' if step == 0 else '|'
        
        return [
            [(' ', body_c), ('(', head_c), ('•', Colors.BLACK), ('_', head_c), ('•', Colors.BLACK), (')', head_c)],
            [(' ', body_c), ('/', body_c), ('[', body_c), ('|', body_c), (']', body_c), ('\\', body_c)],
            [(' ', leg_c), (leg1, leg_c), (' ', leg_c), (' ', leg_c), (leg2, leg_c), (' ', leg_c)]
        ]


class Pigeon:
    def __init__(self, x, y):
        self.x = float(x)
        self.base_y = float(y)
        self.y = float(y)
        self.state = "peck" # peck, walk, fly
        self.vx = 0.05
        self.vy = 0.0
        self.anim_tick = random.randint(0, 20)
        self.scared_timer = 0

    def update(self, dog, world):
        self.anim_tick += 1
        
        # Proximity to dog
        dog_dist = abs((dog.x + dog.width/2) - self.x)
        if dog_dist < 4.5 and abs(dog.y - self.y) < 3.5:
            self.scare()
        if dog.bark_active_ticks > 0 and dog_dist < 10.0:
            self.scare()

        if self.state == "fly":
            self.y += self.vy
            self.x += self.vx * 2.5
            self.scared_timer -= 1
            if self.scared_timer <= 0 and self.y < self.base_y:
                self.vy = 0.2
            if self.y >= self.base_y:
                self.y = self.base_y
                self.vy = 0
                self.state = "peck"
        else:
            # Peck / stroll
            if random.random() < 0.02:
                self.vx = -self.vx
            self.x += self.vx
            if self.x < 5: self.x = 5; self.vx = abs(self.vx)
            if self.x > world.width - 5: self.x = world.width - 5; self.vx = -abs(self.vx)

    def scare(self):
        if self.state != "fly":
            self.state = "fly"
            self.vy = -0.5
            self.scared_timer = 45
            self.vx = 0.4 if random.random() > 0.5 else -0.4
            audio.play('scare')

    def get_sprite(self):
        c_p = Colors.GRAY
        c_b = Colors.BRIGHT_RED
        if self.state == "fly":
            flap = (self.anim_tick // 3) % 2
            wing = "\\_(•)>_/" if flap == 0 else "-(•)-"
            return [[(ch, c_p) for ch in wing]]
        else:
            peck = ">" if (self.anim_tick // 6) % 2 == 0 else "."
            return [[('(', c_p), ('•', c_b), (')', c_p), (peck, Colors.YELLOW)]]


class Cat:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.facing = "left"
        self.state = "chill"
        self.speech_bubble = None
        self.anim_tick = 0

    def update(self, dog):
        self.anim_tick += 1
        if self.speech_bubble:
            txt, col, left = self.speech_bubble
            if left > 1:
                self.speech_bubble = (txt, col, left - 1)
            else:
                self.speech_bubble = None

        dog_dist = abs((dog.x + dog.width/2) - self.x)
        if dog_dist < 5.0 and not self.speech_bubble:
            if dog.state == "bark":
                self.say("Pssszt! *hiss* 😾", Colors.BRIGHT_RED, 25)
            elif random.random() < 0.05:
                self.say("Miau? 🐱", Colors.BRIGHT_WHITE, 20)

    def say(self, text, color, dur):
        self.speech_bubble = (text, color, dur)

    def get_sprite(self):
        c = Colors.BRIGHT_BLACK
        w = Colors.WHITE
        tail = '~' if (self.anim_tick // 8) % 2 == 0 else '^'
        return [
            [('^', c), ('_', w), ('^', c), (' ', c)],
            [('(', c), ('•', Colors.YELLOW), ('x', c), ('•', Colors.YELLOW), (')', c), (tail, c)],
            [(' ', c), ('u', c), (' ', c), ('u', c), (' ', c)]
        ]

class Crab:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.08
        self.min_x = x - 8
        self.max_x = x + 8
        self.anim_tick = random.randint(0, 10)

    def update(self, dog):
        self.anim_tick += 1
        self.x += self.vx
        if self.x <= self.min_x or self.x >= self.max_x:
            self.vx = -self.vx
        
        # Scuttle away fast if dog is close
        if abs(dog.x - self.x) < 4.0:
            self.vx = 0.2 if dog.x < self.x else -0.2

    def get_sprite(self):
        c = Colors.BRIGHT_RED
        snap = ">" if (self.anim_tick // 4) % 2 == 0 else "<"
        return [
            [(snap, c), ('(', c), ('•', Colors.BLACK), ('w', c), ('•', Colors.BLACK), (')', c), (snap, c)],
            [(' ', c), ('/', c), (' ', c), ('\\', c), (' ', c), ('/', c), (' ', c)]
        ]
