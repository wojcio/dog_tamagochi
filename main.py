#!/usr/bin/env python3
"""
🐕 Tamagotchi Dog Simulator 2D Platformer 🐾
Kolorowa platformówka 2D w ASCII Art z symulacją potrzeb Tamagotchi,
cyklem dnia i nocy, 8 biomami (Ogród, Las, Rzeka, Park, Psi Park, Ulica,
Plaża, Agility), akademią sztuczek, sklepikiem, pływaniem i torami przeszkód!
"""

import sys
import time
import signal
from game.engine import Terminal, Colors
from game.dog import Dog, BREEDS, TRICKS, SHOP_ITEMS
from game.world import World
from game.npc import HumanNPC, Pigeon, Cat, Crab, Squirrel, Duck, DogFriend
from game.ui import (Renderer, draw_breed_selection_menu, draw_start_menu,
                     draw_name_input)
from game.audio import audio
from game import save as SaveSystem
from game import quests as QuestSystem

_ACTIVE_GAME = None  # (dog, world, meta) for crash/Ctrl+C save


def handle_exit(signum, frame):
    # Persist the dog mid-game before quitting on Ctrl+C / SIGTERM.
    try:
        if _ACTIVE_GAME is not None:
            SaveSystem.save_game(_ACTIVE_GAME["dog"], _ACTIVE_GAME["world"],
                                 _ACTIVE_GAME["meta"], _ACTIVE_GAME.get("quests"))
    except Exception:
        pass
    try:
        audio.cleanup()
    except Exception:
        pass
    sys.stdout.write("\033[?25h\033[?1049l" + Colors.RESET)
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


def run_game(breed_key="corgi", terminal=None, resume=False, name="", meta=None):
    global _ACTIVE_GAME
    if terminal is None:
        terminal = Terminal(width=105, height=28)
        terminal.enter_fullscreen()

    world = World(width=840, height=22)
    renderer = Renderer(terminal)

    greeting = None
    quests_state = None
    if resume:
        raw = SaveSystem.load_raw()
        if raw:
            bk = raw.get("dog", {}).get("breed_key", breed_key)
            dog = Dog(breed_key=bk if bk in BREEDS else "corgi", x=10.0, y=16.0)
            SaveSystem.apply_to_dog(raw, dog)
            SaveSystem.apply_to_world(raw, world)
            meta = raw.get("meta", {"created_at": time.time()})
            dog.name = meta.get("name", "") or ""
            quests_state = QuestSystem.sanitize(raw.get("quests"))
            greeting, days = SaveSystem.apply_offline_decay(
                dog, raw.get("saved_at", time.time()), meta)
            dog.days_together = days
        else:
            resume = False  # save vanished; fall through to a fresh game

    if not resume:
        dog = Dog(breed_key=breed_key, x=10.0, y=16.0, name=name)
        if meta is None:
            meta = SaveSystem.new_meta(dog.name)
        dog.days_together = SaveSystem.days_together(meta)

    # Daily quests: keep today's set, roll a fresh batch when the day changed.
    quests_state, quests_rolled = QuestSystem.ensure_today(
        quests_state, QuestSystem.today_str(), dog)

    _ACTIVE_GAME = {"dog": dog, "world": world, "meta": meta, "quests": quests_state}
    last_autosave = time.time()

    if greeting:
        dog.say(greeting, Colors.PINK + Colors.BOLD, 150)
    elif quests_rolled:
        dog.say("Nowe zadania na dziś! Wciśnij [R] 📋", Colors.GOLD + Colors.BOLD, 110)
    else:
        dog.say(f"Cześć! Jestem {dog.breed.name}! 🐾", Colors.BRIGHT_GREEN + Colors.BOLD, 90)

    # Spawn Diverse NPCs across the 8 Biomes
    npcs = [
        HumanNPC("Pan Ogrodnik", x=58, y=16, role="Sprzedawca", color=Colors.GOLD, min_x=53, max_x=64),
        HumanNPC("Pani Ania", x=85, y=16, role="Spacerowicz", color=Colors.PINK, min_x=72, max_x=102),
        HumanNPC("Pan Tomek", x=345, y=16, role="Biegacz", color=Colors.BRIGHT_BLUE, min_x=325, max_x=385),
        HumanNPC("Kasia", x=395, y=16, role="Dziecko z piłką", color=Colors.BRIGHT_MAGENTA, min_x=380, max_x=415),
        HumanNPC("Leśniczy", x=160, y=16, role="Leśniczy", color=Colors.DARK_GREEN, min_x=115, max_x=200),
        HumanNPC("Marek Plażowicz", x=665, y=16, role="Plażowicz", color=Colors.BRIGHT_YELLOW, min_x=650, max_x=700),
        HumanNPC("Sędzia Agility", x=742, y=16, role="Sędzia", color=Colors.BRIGHT_WHITE, min_x=738, max_x=748)
    ]

    pigeons = [
        Pigeon(25, 18),
        Pigeon(82, 18),
        Pigeon(360, 12), # on park bridge
        Pigeon(398, 14), # on picnic table
        Pigeon(660, 18)
    ]

    cats = [
        Cat(78, 15),   # on garden bench
        Cat(402, 14),  # on park picnic table
        Cat(592, 16),  # na płocie przy ulicy
        Cat(608, 14)   # na ławce przy ulicy
    ]

    crabs = [
        Crab(655, 18),
        Crab(685, 18),
        Crab(715, 18)
    ]

    squirrels = [
        Squirrel(120, 110, 135),   # Las zachodni
        Squirrel(150, 140, 170),   # Las środkowy
        Squirrel(195, 175, 205),   # Las wschodni
        Squirrel(575, 545, 615)    # przebiezająca przez ulicę 🐿️🚗
    ]

    ducks = [
        Duck(235),
        Duck(290)
    ]

    dog_friends = [
        DogFriend("Burek", 440, 424, 468, color=Colors.BRIGHT_BLACK),
        DogFriend("Luna", 490, 480, 515),
        DogFriend("Azor", 510, 480, 518, color=Colors.BRIGHT_WHITE)
    ]

    clock_tick = 0
    running = True
    paused = False
    modal_state = None # None, 'tricks', 'shop'
    shop_selected_idx = 0
    shop_item_keys = list(SHOP_ITEMS.keys())

    # Held-key movement: keep walking smoothly between OS key-repeat events.
    held_dir = 0        # -1 left, +1 right, 0 none
    held_key_time = 0.0
    HOLD_GRACE = 0.14   # seconds a direction stays active after its last event

    while running:
        frame_start = time.time()
        clock_tick += 1

        # Process input
        keys = terminal.get_input()
        if keys:
            for k in keys:
                # Exit / Back to Menu
                if k in ['ESC', 'CTRL_C']:
                    if modal_state is not None:
                        modal_state = None
                    else:
                        running = False
                        break

                # Sleep / Nap in Doghouse (Z or Q)
                elif k in ['z', 'q']:
                    if modal_state is not None:
                        modal_state = None
                    else:
                        dog.sleep()

                # Pause
                elif k == 'p':
                    if modal_state is None:
                        paused = not paused
                        if paused:
                            dog.say("PAUZA [P - Wznów]", Colors.YELLOW, 999)
                        else:
                            dog.speech_bubble = None

                # Mute Audio
                elif k == 'm':
                    is_on = audio.toggle_mute()
                    status_str = "WŁĄCZONY 🔊" if is_on else "WYŁĄCZONY 🔇"
                    dog.say(f"Dźwięk PC: {status_str}", Colors.BRIGHT_WHITE, 25)

                # Modal: Tricks Menu
                elif k == 't':
                    if modal_state == "tricks":
                        modal_state = None
                    else:
                        modal_state = "tricks"
                        audio.play('menu_select')

                # Modal: Shop Menu
                elif k == 'k':
                    if modal_state == "shop":
                        modal_state = None
                    else:
                        modal_state = "shop"
                        shop_selected_idx = 0
                        audio.play('menu_select')

                # Modal: Daily Quest Log
                elif k == 'r':
                    if modal_state == "quests":
                        modal_state = None
                    else:
                        modal_state = "quests"
                        audio.play('menu_select')

                # Shop Navigation
                elif modal_state == "shop":
                    if k in ['UP', 'w']:
                        shop_selected_idx = (shop_selected_idx - 1) % len(shop_item_keys)
                        audio.play('menu_move')
                    elif k in ['DOWN', 's']:
                        shop_selected_idx = (shop_selected_idx + 1) % len(shop_item_keys)
                        audio.play('menu_move')
                    elif k in ['ENTER', 'SPACE']:
                        cur_key = shop_item_keys[shop_selected_idx]
                        item_data = SHOP_ITEMS[cur_key]
                        if cur_key in dog.inventory:
                            # Equip/Toggle
                            if dog.equipped_item == cur_key:
                                dog.equipped_item = None
                                dog.say(f"Zdjęto: {item_data['name']}", Colors.WHITE, 20)
                            else:
                                dog.equipped_item = cur_key
                                dog.say(f"Założono: {item_data['name']}! ✨", Colors.GOLD, 25)
                            audio.play('menu_select')
                        else:
                            # Try to buy
                            if dog.bones_currency >= item_data['price']:
                                dog.bones_currency -= item_data['price']
                                dog.inventory.append(cur_key)
                                dog.equipped_item = cur_key
                                audio.play('buy')
                                dog.say(f"Kupiono i założono: {item_data['name']}! 🎉", Colors.BRIGHT_GREEN, 30)
                            else:
                                audio.play('alert')
                                dog.say(f"Brakuje Ci {item_data['price'] - dog.bones_currency} 🦴 kości!", Colors.BRIGHT_RED, 25)
                    elif k == 'u':
                        dog.equipped_item = None
                        dog.say("Zdjęto akcesorium.", Colors.WHITE, 20)

                # Direct Trick Keys 1-5
                elif k in ['1', '2', '3', '4', '5']:
                    dog.perform_trick(k)

                # In-Game Movement & Actions
                elif not paused and modal_state is None:
                    if k in ['LEFT', 'a']:
                        held_dir = -1
                        held_key_time = frame_start
                    elif k in ['RIGHT', 'd']:
                        held_dir = 1
                        held_key_time = frame_start
                    elif k in ['UP', 'w']:
                        dog.jump()
                    elif k in ['SPACE', 'b', 'h']:
                        dog.bark()
                        for p in pigeons:
                            if abs(dog.x - p.x) < 14:
                                p.scare()
                    elif k == 'e': # Ask for pet
                        for h in npcs:
                            if abs((dog.x + dog.width/2) - (h.x + 1.5)) < 6.0:
                                h.interact_pet(dog)
                                break
                        else:
                            dog.bark()
                    elif k == 'DOWN': # Drop down from platform
                        dog.drop_down(world)
                    elif k == 's': # Pee
                        dog.pee()
                        marked_prop = world.check_mark_prop(dog)
                        if marked_prop:
                            dog.say("Zaznaczono terytorium! 💦✓", Colors.BRIGHT_CYAN, 25)

        # Apply continuous movement while a direction is held (fills key-repeat gaps).
        if not paused and modal_state is None and held_dir != 0:
            if time.time() - held_key_time <= HOLD_GRACE:
                if held_dir < 0:
                    dog.move_left()
                else:
                    dog.move_right()
            else:
                held_dir = 0

        if not paused:
            # Physics & world updates
            dog.update_physics(world)
            dog.update_tamagotchi()
            world.update(dog)
            
            # Collisions & Interactions
            world.check_item_pickup(dog)
            world.check_ball_interaction(dog)

            for h in npcs:
                h.update(dog, world)

            for p in pigeons:
                p.update(dog, world)

            for c in cats:
                c.update(dog)

            for cr in crabs:
                cr.update(dog)

            for sq in squirrels:
                sq.update(dog, world)

            for dk in ducks:
                dk.update(dog, world)

            for pal in dog_friends:
                pal.update(dog, world)

        # Daily quest progress & rollover (only while the world simulates).
        if not paused:
            if clock_tick % 300 == 0:  # ~every 10s: did the calendar day flip?
                day = QuestSystem.today_str()
                if day != quests_state["date"]:
                    quests_state, _ = QuestSystem.ensure_today(quests_state, day, dog)
                    _ACTIVE_GAME["quests"] = quests_state
                    dog.say("Nowy dzień — nowe zadania! [R] 📋", Colors.GOLD + Colors.BOLD, 120)
            for ev in QuestSystem.check_completions(quests_state, dog):
                audio.play('level_up')
                dog.say(f"ZADANIE UKOŃCZONE! +{ev['bones']}🦴 +{ev['xp']}XP 🎉",
                        Colors.BRIGHT_GREEN + Colors.BOLD, 110)

        # Render frame
        renderer.render_world_and_hud(
            world, dog, npcs, pigeons, cats, crabs,
            squirrels=squirrels, ducks=ducks, dog_friends=dog_friends,
            modal_state=modal_state,
            modal_data=(shop_selected_idx if modal_state == "shop"
                        else quests_state if modal_state == "quests" else None),
            quests=quests_state
        )
        terminal.render()

        # Autosave every ~30s so a crash loses little progress.
        now = time.time()
        if now - last_autosave > 30.0:
            dog.days_together = SaveSystem.days_together(meta)
            try:
                SaveSystem.save_game(dog, world, meta, quests_state)
                last_autosave = now
            except Exception:
                pass

        # Target ~30 FPS
        elapsed = time.time() - frame_start
        sleep_time = max(0.001, (1.0 / 30.0) - elapsed)
        time.sleep(sleep_time)

    # Normal exit (ESC): persist the dog's state.
    try:
        dog.days_together = SaveSystem.days_together(meta)
        SaveSystem.save_game(dog, world, meta, quests_state)
    except Exception:
        pass
    _ACTIVE_GAME = None


DEFAULT_NAMES = {
    "corgi": "Kora", "dachshund": "Parówka", "setter": "Dżek",
    "shiba": "Hachi", "poodle": "Fafik",
}


def save_info_from(raw):
    """Build a display dict for the start menu from a raw save."""
    d = raw.get("dog", {})
    meta = raw.get("meta", {})
    breed = BREEDS.get(d.get("breed_key", "corgi"), BREEDS["corgi"])
    return {
        "name": meta.get("name") or "",
        "breed_name": breed.name,
        "level": int(d.get("level", 1) or 1),
        "days": SaveSystem.days_together(meta),
        "bones": int(d.get("bones_currency", 0) or 0),
    }


def start_menu(terminal, save_info):
    """Resume / New menu. Returns 'continue', 'new' or 'quit'."""
    sel = 0
    while True:
        draw_start_menu(terminal, save_info, sel)
        terminal.render()
        for k in terminal.get_input():
            if k in ['UP', 'DOWN', 'w', 's']:
                sel = 1 - sel
                audio.play('menu_move')
            elif k in ['ENTER', 'SPACE']:
                audio.play('menu_select')
                return 'continue' if sel == 0 else 'new'
            elif k in ['q', 'CTRL_C', 'ESC']:
                return 'quit'
        time.sleep(0.03)


def choose_breed(terminal):
    """Breed picker. Returns a breed_key, or None to quit."""
    keys = list(BREEDS.keys())
    idx = 0
    while True:
        draw_breed_selection_menu(terminal, idx)
        terminal.render()
        for k in terminal.get_input():
            if k in ['q', 'CTRL_C', 'ESC']:
                return None
            elif k in ['LEFT', 'a']:
                idx = (idx - 1) % len(keys); audio.play('menu_move')
            elif k in ['RIGHT', 'd']:
                idx = (idx + 1) % len(keys); audio.play('menu_move')
            elif k in ['ENTER', 'SPACE']:
                audio.play('menu_select'); time.sleep(0.15)
                return keys[idx]
        time.sleep(0.03)


def enter_name(terminal, breed):
    """Name-entry loop. Returns the typed (capitalized) name or '' for default."""
    buf = ""
    while True:
        draw_name_input(terminal, buf, breed)
        terminal.render()
        for k in terminal.get_input():
            if k == 'ENTER':
                audio.play('menu_select')
                name = buf.strip()
                return (name[:1].upper() + name[1:]) if name else ""
            elif k == 'ESC':
                return ""
            elif k in ('\x7f', '\b', 'BACKSPACE'):
                buf = buf[:-1]; audio.play('menu_move')
            elif len(k) == 1 and k.isprintable() and len(buf) < 14:
                if k not in (' ',):
                    buf += k; audio.play('menu_move')
        time.sleep(0.03)


def main():
    terminal = Terminal(width=105, height=28)
    terminal.enter_fullscreen()

    try:
        while True:
            raw = SaveSystem.load_raw() if SaveSystem.exists() else None

            if raw is not None:
                choice = start_menu(terminal, save_info_from(raw))
                if choice == 'quit':
                    break
                if choice == 'continue':
                    run_game(terminal=terminal, resume=True)
                    continue  # back to the start menu (save now exists)
                # choice == 'new' -> fall through to adoption flow

            breed_key = choose_breed(terminal)
            if breed_key is None:
                break  # user quit from breed selection

            name = enter_name(terminal, BREEDS[breed_key])
            if not name:
                name = DEFAULT_NAMES.get(breed_key, "Piesek")

            run_game(breed_key=breed_key, terminal=terminal, resume=False, name=name)
            # loop back: a save now exists, so the start menu is shown next

    except KeyboardInterrupt:
        pass
    finally:
        audio.cleanup()
        terminal.exit_fullscreen()
        print(f"\n{Colors.GOLD}Dziękujemy za opiekę nad pieskiem! Do zobaczenia! 🐾{Colors.RESET}\n")

if __name__ == "__main__":
    main()
