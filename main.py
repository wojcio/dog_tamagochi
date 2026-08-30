#!/usr/bin/env python3
"""
🐕 Tamagotchi Dog Simulator 2D Platformer 🐾
Kolorowa platformówka 2D w ASCII Art z symulacją potrzeb Tamagotchi,
cyklem dnia i nocy, 4 biomami, akademią sztuczek, sklepikiem i torami przeszkód!
"""

import sys
import time
import signal
from game.engine import Terminal, Colors
from game.dog import Dog, BREEDS, TRICKS, SHOP_ITEMS
from game.world import World
from game.npc import HumanNPC, Pigeon, Cat, Crab
from game.ui import Renderer, draw_breed_selection_menu
from game.audio import audio

def handle_exit(signum, frame):
    try:
        audio.cleanup()
    except Exception:
        pass
    sys.stdout.write("\033[?25h\033[?1049l" + Colors.RESET)
    sys.stdout.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def run_game(breed_key="corgi", terminal=None):
    if terminal is None:
        terminal = Terminal(width=105, height=28)
        terminal.enter_fullscreen()

    world = World(width=420, height=22)
    dog = Dog(breed_key=breed_key, x=10.0, y=16.0)
    renderer = Renderer(terminal)

    # Spawn Diverse NPCs across the 4 Biomes
    npcs = [
        HumanNPC("Pan Ogrodnik", x=58, y=16, role="Sprzedawca", color=Colors.GOLD, min_x=53, max_x=64),
        HumanNPC("Pani Ania", x=85, y=16, role="Spacerowicz", color=Colors.PINK, min_x=72, max_x=102),
        HumanNPC("Pan Tomek", x=135, y=16, role="Biegacz", color=Colors.BRIGHT_BLUE, min_x=115, max_x=175),
        HumanNPC("Kasia", x=185, y=16, role="Dziecko z piłką", color=Colors.BRIGHT_MAGENTA, min_x=170, max_x=205),
        HumanNPC("Marek Plażowicz", x=245, y=16, role="Plażowicz", color=Colors.BRIGHT_YELLOW, min_x=230, max_x=280),
        HumanNPC("Sędzia Agility", x=322, y=16, role="Sędzia", color=Colors.BRIGHT_WHITE, min_x=318, max_x=328)
    ]

    pigeons = [
        Pigeon(25, 18),
        Pigeon(82, 18),
        Pigeon(150, 12), # on bridge
        Pigeon(188, 14), # on picnic table
        Pigeon(240, 18)
    ]

    cats = [
        Cat(78, 15),  # on garden bench
        Cat(192, 14)  # on park picnic table
    ]

    crabs = [
        Crab(235, 18),
        Crab(265, 18),
        Crab(295, 18)
    ]

    clock_tick = 0
    running = True
    paused = False
    modal_state = None # None, 'tricks', 'shop'
    shop_selected_idx = 0
    shop_item_keys = list(SHOP_ITEMS.keys())

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
                        dog.move_left()
                    elif k in ['RIGHT', 'd']:
                        dog.move_right()
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

        # Render frame
        renderer.render_world_and_hud(
            world, dog, npcs, pigeons, cats, crabs,
            modal_state=modal_state,
            modal_data=shop_selected_idx if modal_state == "shop" else None
        )
        terminal.render()

        # Target ~30 FPS
        elapsed = time.time() - frame_start
        sleep_time = max(0.001, (1.0 / 30.0) - elapsed)
        time.sleep(sleep_time)


def main():
    terminal = Terminal(width=105, height=28)
    terminal.enter_fullscreen()

    try:
        breed_keys = list(BREEDS.keys())
        selected_idx = 0
        in_menu = True

        while in_menu:
            draw_breed_selection_menu(terminal, selected_idx)
            terminal.render()

            keys = terminal.get_input()
            if keys:
                for k in keys:
                    if k in ['q', 'CTRL_C', 'ESC']:
                        in_menu = False
                        break
                    elif k in ['LEFT', 'a']:
                        selected_idx = (selected_idx - 1) % len(breed_keys)
                        audio.play('menu_move')
                    elif k in ['RIGHT', 'd']:
                        selected_idx = (selected_idx + 1) % len(breed_keys)
                        audio.play('menu_move')
                    elif k in ['ENTER', 'SPACE']:
                        audio.play('menu_select')
                        time.sleep(0.15)
                        chosen_breed = breed_keys[selected_idx]
                        run_game(chosen_breed, terminal)
            
            time.sleep(0.03)

    except KeyboardInterrupt:
        pass
    finally:
        audio.cleanup()
        terminal.exit_fullscreen()
        print(f"\n{Colors.GOLD}Dziękujemy za opiekę nad pieskiem! Do zobaczenia! 🐾{Colors.RESET}\n")

if __name__ == "__main__":
    main()
