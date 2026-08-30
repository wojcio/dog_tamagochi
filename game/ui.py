"""
Game UI, Multi-Biome World Renderer, Day/Night Lighting, Tamagotchi HUD,
Tricks Menu, Gardener Shop, and Breed Selector.
"""

from game.engine import Colors
from game.dog import BREEDS, TRICKS, SHOP_ITEMS
from game.audio import audio

def create_bar(value, max_value=100.0, length=8, fill_color=Colors.BRIGHT_GREEN, empty_color=Colors.DARK_GRAY):
    clamped = max(0.0, min(max_value, value))
    fill_len = int(round((clamped / max_value) * length))
    empty_len = length - fill_len
    bar_str = f"{fill_color}{'█' * fill_len}{empty_color}{'░' * empty_len}{Colors.RESET}"
    return bar_str

class Renderer:
    def __init__(self, terminal):
        self.term = terminal
        self.view_width = terminal.target_width
        self.view_height = terminal.target_height
        self.game_height = 20
        self.hud_height = 8

    def render_world_and_hud(self, world, dog, npcs, pigeons, cats, crabs, modal_state=None, modal_data=None):
        self.term.clear_buffer()

        # Camera centering on dog
        camera_x = int(dog.x + dog.width // 2 - self.view_width // 2)
        camera_x = max(0, min(world.width - self.view_width, camera_x))

        time_name, sky_col, is_night, celestial_icon = world.get_time_of_day_info()

        # 1. Render Dynamic Sky & Celestial Bodies
        for y in range(world.ground_base_y):
            for x in range(self.view_width):
                if is_night:
                    self.term.draw_char(x, y, ' ', Colors.bg256(234))
                elif "Zachód" in time_name:
                    self.term.draw_char(x, y, ' ', Colors.bg256(215) if y < 4 else Colors.RESET)
                elif "Świt" in time_name:
                    self.term.draw_char(x, y, ' ', Colors.bg256(223) if y < 4 else Colors.RESET)
                else: # Day
                    self.term.draw_char(x, y, ' ', Colors.BG_SKY if y < 4 else Colors.RESET)

        # Stars at Night
        if is_night:
            for sx, sy, star_ch in world.stars:
                screen_sx = sx - camera_x
                if 0 <= screen_sx < self.view_width and sy < world.ground_base_y - 4:
                    self.term.draw_text(screen_sx, sy, star_ch, Colors.BRIGHT_WHITE + Colors.BOLD)

        # Sun or Moon
        body_screen_x = 84 - int((camera_x // 10) % 70)
        if 0 <= body_screen_x < self.view_width - 8:
            if is_night:
                self.term.draw_text(body_screen_x, 1, "   .--.   ", Colors.CREAM + Colors.BOLD)
                self.term.draw_text(body_screen_x, 2, "  ( 🌙 )  ", Colors.GOLD + Colors.BOLD)
                self.term.draw_text(body_screen_x, 3, "   `--'   ", Colors.CREAM + Colors.BOLD)
            elif "Zachód" in time_name:
                self.term.draw_text(body_screen_x, 2, "  .--.  ", Colors.RED + Colors.BOLD)
                self.term.draw_text(body_screen_x, 3, " -(🌅)- ", Colors.GOLD + Colors.BOLD)
            else:
                self.term.draw_text(body_screen_x, 1, "  \\ | /  ", Colors.BRIGHT_YELLOW)
                self.term.draw_text(body_screen_x, 2, " --(☀)-- ", Colors.GOLD + Colors.BOLD)
                self.term.draw_text(body_screen_x, 3, "  / | \\  ", Colors.BRIGHT_YELLOW)

        # Clouds
        for cloud in world.clouds:
            cx = int(cloud["x"]) - camera_x
            cy = int(cloud["y"])
            if -15 < cx < self.view_width:
                cloud_col = Colors.GRAY if is_night else Colors.BRIGHT_WHITE
                if cloud["type"] == 0:
                    self.term.draw_text(cx, cy, "  .---.  ", cloud_col + Colors.BOLD)
                    self.term.draw_text(cx, cy + 1, " (  ☁  ) ", cloud_col + Colors.BOLD)
                    self.term.draw_text(cx, cy + 2, "  `---'  ", cloud_col + Colors.BOLD)
                else:
                    self.term.draw_text(cx, cy, "  (☁☁☁)  ", cloud_col)
                    self.term.draw_text(cx, cy + 1, " (☁☁☁☁☁) ", cloud_col)

        # 2. Render Platforms
        for plat in world.platforms:
            px = int(plat.x) - camera_x
            py = int(plat.y)
            if px + plat.width > 0 and px < self.view_width:
                for col in range(plat.width):
                    sx = px + col
                    if 0 <= sx < self.view_width:
                        ch = '='
                        if col == 0: ch = '['
                        elif col == plat.width - 1: ch = ']'
                        self.term.draw_char(sx, py, ch, plat.style + Colors.BOLD)

        # 3. Render Multi-Biome Props
        ground_y = world.ground_base_y
        for prop in world.props:
            px = int(prop.x) - camera_x
            py = int(prop.y)

            # Doghouse (Zone 1)
            if prop.prop_type == 'doghouse':
                if px + 11 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 4, "   /\\    ", Colors.RED + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 3, "  /  \\   ", Colors.RED + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, " /____\\  ", Colors.RED + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 1, " | [ ]_ |", Colors.BROWN)
                    self.term.draw_text(px, ground_y,     " | [BUDA]|", Colors.BROWN + Colors.BOLD)

            # Shop stand (Zone 1)
            elif prop.prop_type == 'shop':
                if px + 14 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 4, "┌──────────┐", Colors.GOLD + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 3, "│ SKLEPIK 🦴│", Colors.GOLD + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, "│ 🎩🎀🕶️👑 │", Colors.BRIGHT_WHITE)
                    self.term.draw_text(px, ground_y - 1, "│ [K-Kupuj]│", Colors.BRIGHT_CYAN)
                    self.term.draw_text(px, ground_y,     "└──────────┘", Colors.GOLD)

            # Trees (Zone 1 & 2)
            elif prop.prop_type == 'tree':
                if px + 10 > 0 and px < self.view_width:
                    tree_c1 = Colors.DARK_GREEN if is_night else Colors.GRASS_GREEN
                    tree_c2 = Colors.BRIGHT_BLACK if is_night else Colors.DARK_GREEN
                    self.term.draw_text(px - 1, 5, "   .---.   ", tree_c1 + Colors.BOLD)
                    self.term.draw_text(px - 1, 6, "  ( @@@ )  ", tree_c2 + Colors.BOLD)
                    self.term.draw_text(px - 2, 7, " ( @@@@@@@ ) ", tree_c1 + Colors.BOLD)
                    self.term.draw_text(px - 2, 8, "( @@@@@@@@@ )", tree_c2 + Colors.BOLD)
                    self.term.draw_text(px - 2, 9, " ( @@@@@@@ ) ", tree_c1 + Colors.BOLD)
                    self.term.draw_text(px - 1, 10,"  (  @@@  )  ", tree_c2 + Colors.BOLD)
                    self.term.draw_text(px - 1, 11,"   `--|--'   ", Colors.BROWN)
                    for ty in range(12, ground_y):
                        self.term.draw_text(px + 2, ty, " | | ", Colors.BROWN)
                    self.term.draw_text(px + 1, ground_y, "_/ | \\_", Colors.BROWN + Colors.BOLD)
                    if prop.marked:
                        self.term.draw_text(px + 1, ground_y - 1, "💧✓", Colors.BRIGHT_CYAN + Colors.BOLD)

            # Fountain (Zone 2)
            elif prop.prop_type == 'fountain':
                if px + 11 > 0 and px < self.view_width:
                    spray = "* ⛲ *" if (dog.anim_tick // 4) % 2 == 0 else " * ⛲ * "
                    self.term.draw_text(px + 1, ground_y - 3, spray, Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, " (~~~~~~) ", Colors.CYAN)
                    self.term.draw_text(px, ground_y - 1, "  [====]  ", Colors.GRAY)
                    self.term.draw_text(px, ground_y,     " [======] ", Colors.DARK_GRAY)

            # Hydrant
            elif prop.prop_type == 'hydrant':
                if px + 4 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 3, " (o) ", Colors.BRIGHT_RED + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, "=[|]=", Colors.RED + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 1, " |#| ", Colors.RED)
                    self.term.draw_text(px, ground_y,     " [=] ", Colors.DARK_GRAY)
                    if prop.marked:
                        self.term.draw_text(px, ground_y - 4, "💧✓", Colors.BRIGHT_CYAN + Colors.BOLD)

            # Street Lamps (Glow at dusk / night!)
            elif prop.prop_type == 'lamp':
                if px + 4 > 0 and px < self.view_width:
                    glow_col = Colors.BRIGHT_YELLOW + Colors.BOLD if (is_night or "Zachód" in time_name) else Colors.YELLOW
                    self.term.draw_text(px, 9, " /☼\\ ", glow_col)
                    for ly in range(10, ground_y):
                        self.term.draw_text(px + 1, ly, " | ", Colors.DARK_GRAY)
                    self.term.draw_text(px, ground_y, " [=] ", Colors.DARK_GRAY)

            # Benches
            elif prop.prop_type == 'bench':
                if px + prop.width > 0 and px < self.view_width:
                    bench_str = "[" + "=" * (prop.width - 2) + "]"
                    self.term.draw_text(px, py, bench_str, Colors.LIGHT_BROWN)
                    target_ground = min(ground_y, py + 3)
                    for by_line in range(py + 1, target_ground):
                        self.term.draw_text(px, by_line, "|", Colors.LIGHT_BROWN)
                        self.term.draw_text(px + prop.width - 1, by_line, "|", Colors.LIGHT_BROWN)

            # Beach Umbrellas (Zone 3)
            elif prop.prop_type == 'umbrella':
                if px + 8 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 4, "  /\\/\\/\\  ", Colors.BRIGHT_MAGENTA + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 3, " /______\\ ", Colors.PINK + Colors.BOLD)
                    self.term.draw_text(px + 4, ground_y - 2, "|", Colors.WHITE)
                    self.term.draw_text(px + 4, ground_y - 1, "|", Colors.WHITE)
                    self.term.draw_text(px, ground_y,     " [___/ ] |", Colors.CYAN) # Lounger
                    if prop.marked:
                        self.term.draw_text(px + 2, ground_y - 1, "💧✓", Colors.BRIGHT_CYAN + Colors.BOLD)

            # Agility Start Gate (Zone 4)
            elif prop.prop_type == 'start_gate':
                if px + 10 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 4, "╔════════╗", Colors.GOLD + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 3, "║ 🏁START║", Colors.BRIGHT_GREEN + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, "║   >>   ║", Colors.GOLD)
                    self.term.draw_text(px, ground_y - 1, "║        ║", Colors.GOLD)
                    self.term.draw_text(px, ground_y,     "╩        ╩", Colors.GOLD)

            # Agility Hurdle
            elif prop.prop_type == 'hurdle':
                if px + 6 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 2, "[====]", Colors.BRIGHT_YELLOW + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 1, "|    |", Colors.RED)
                    self.term.draw_text(px, ground_y,     "|    |", Colors.RED)

            # Agility Slalom Poles
            elif prop.prop_type == 'slalom':
                if px + 10 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 3, " 🚩   🚩   🚩 ", Colors.BRIGHT_RED + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, " |    |    |  ", Colors.WHITE)
                    self.term.draw_text(px, ground_y - 1, " |    |    |  ", Colors.WHITE)
                    self.term.draw_text(px, ground_y,     " ┴    ┴    ┴  ", Colors.DARK_GRAY)

            # Agility Hoop
            elif prop.prop_type == 'hoop':
                if px + 8 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 5, "  .---.  ", Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 4, " (     ) ", Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 3, " (  ⭕ ) ", Colors.GOLD + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, "  `---'  ", Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_text(px + 3, ground_y - 1, " | ", Colors.DARK_GRAY)
                    self.term.draw_text(px + 3, ground_y,     " ┴ ", Colors.DARK_GRAY)

            # Agility Finish Gate
            elif prop.prop_type == 'finish_gate':
                if px + 10 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 4, "╔════════╗", Colors.GOLD + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 3, "║ 🏆META ║", Colors.GOLD + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 2, "║  ★★★★  ║", Colors.BRIGHT_YELLOW)
                    self.term.draw_text(px, ground_y - 1, "║        ║", Colors.GOLD)
                    self.term.draw_text(px, ground_y,     "╩        ╩", Colors.GOLD)

        # 4. Render Food Items
        for it in world.items:
            if not it.collected:
                ix = int(it.x) - camera_x
                iy = int(it.y)
                if 0 <= ix < self.view_width:
                    if it.item_type == 'bone':
                        self.term.draw_text(ix, iy, "🦴(==)", Colors.BRIGHT_WHITE + Colors.BOLD)
                    elif it.item_type == 'steak':
                        self.term.draw_text(ix, iy, "🥩[Steak]", Colors.BRIGHT_RED + Colors.BOLD)
                    elif it.item_type == 'bowl':
                        self.term.draw_text(ix, iy, "🥣\\_U_/", Colors.BRIGHT_YELLOW + Colors.BOLD)
                    else: # treat
                        self.term.draw_text(ix, iy, "🍖*Smaczek*", Colors.GOLD + Colors.BOLD)

        # 5. Render Toy Ball
        bx = int(world.ball.x) - camera_x
        by = int(world.ball.y)
        if 0 <= bx < self.view_width:
            self.term.draw_text(bx, by, "⚽(o)", Colors.BRIGHT_WHITE + Colors.BOLD)

        # 6. Render Pigeons & Crabs
        for pig in pigeons:
            px = int(pig.x) - camera_x
            py = int(pig.y)
            if 0 <= px < self.view_width:
                self.term.draw_colored_sprite(px, py, pig.get_sprite())

        for crab in crabs:
            cx = int(crab.x) - camera_x
            cy = int(crab.y)
            if 0 <= cx < self.view_width:
                self.term.draw_colored_sprite(cx, cy, crab.get_sprite())

        # 7. Render Cats
        for cat in cats:
            cx = int(cat.x) - camera_x
            cy = int(cat.y)
            if 0 <= cx < self.view_width:
                self.term.draw_colored_sprite(cx, cy, cat.get_sprite())
                if cat.speech_bubble:
                    self._draw_speech_bubble(cx - 2, cy - 2, cat.speech_bubble[0], cat.speech_bubble[1])

        # 8. Render Humans (NPCs)
        for human in npcs:
            hx = int(human.x) - camera_x
            hy = int(human.y)
            if -5 < hx < self.view_width:
                self.term.draw_colored_sprite(hx, hy, human.get_sprite())
                if human.speech_bubble:
                    self._draw_speech_bubble(hx - 4, hy - 2, human.speech_bubble[0], human.speech_bubble[1])

        # 9. Render Dog Player + Equipped Accessory
        dx = int(dog.x) - camera_x
        dy = int(dog.y)
        dog_sprite = dog.get_sprite()
        self.term.draw_colored_sprite(dx, dy, dog_sprite)

        # Accessory on head
        if dog.equipped_item:
            item_info = SHOP_ITEMS.get(dog.equipped_item)
            if item_info:
                hat_x = dx + 2 if dog.facing == "right" else dx + 1
                self.term.draw_text(hat_x, max(0, dy - 1), item_info['icon'], Colors.BOLD)

        # Dog speech / action bubble
        if dog.speech_bubble:
            self._draw_speech_bubble(dx - 3, dy - 2, dog.speech_bubble[0], dog.speech_bubble[1])

        # 10. Render Biome Ground & Terrain
        for x in range(self.view_width):
            world_x = camera_x + x
            
            # Biome Ground Textures:
            if world_x < 105: # Ogród
                grass_ch = "w" if world_x % 3 == 0 else ("W" if world_x % 3 == 1 else "v")
                flower_ch = "🌸" if world_x % 15 == 0 else ("🌼" if world_x % 21 == 0 else grass_ch)
                if flower_ch in ["🌸", "🌼"]:
                    self.term.draw_text(x, ground_y, flower_ch, Colors.PINK)
                else:
                    self.term.draw_char(x, ground_y, grass_ch, Colors.GRASS_GREEN + Colors.BOLD)
                self.term.draw_char(x, ground_y + 1, "░", Colors.BROWN)

            elif world_x < 210: # Park Miejski
                if 143 <= world_x <= 165: # Stream under bridge
                    wave_ch = "~" if (dog.anim_tick // 4 + world_x) % 2 == 0 else "≈"
                    self.term.draw_char(x, ground_y, wave_ch, Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "▓", Colors.BLUE)
                else:
                    grass_ch = "W" if world_x % 2 == 0 else "w"
                    self.term.draw_char(x, ground_y, grass_ch, Colors.DARK_GREEN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "░", Colors.BROWN)

            elif world_x < 315: # Słoneczna Plaża
                if world_x > 295: # Ocean shore
                    wave_ch = "≈" if (dog.anim_tick // 3 + world_x) % 2 == 0 else "~"
                    self.term.draw_char(x, ground_y, wave_ch, Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "▓", Colors.BLUE)
                else:
                    sand_ch = "░" if world_x % 2 == 0 else "▒"
                    self.term.draw_char(x, ground_y, sand_ch, Colors.GOLD)
                    self.term.draw_char(x, ground_y + 1, "▒", Colors.BROWN)

            else: # Tor Agility
                turf_ch = "=" if world_x % 2 == 0 else "_"
                turf_col = Colors.BRIGHT_RED if world_x % 6 < 3 else Colors.BRIGHT_WHITE
                self.term.draw_char(x, ground_y, turf_ch, turf_col + Colors.BOLD)
                self.term.draw_char(x, ground_y + 1, "░", Colors.DARK_GRAY)

        # 11. Render Modals (if active)
        if modal_state == "tricks":
            self._render_tricks_modal(dog)
        elif modal_state == "shop":
            self._render_shop_modal(dog, modal_data or 0)

        # 12. Render Tamagotchi HUD
        self.render_hud(dog, world)

    def _draw_speech_bubble(self, x, y, text, color=Colors.BRIGHT_WHITE):
        clean_len = len(text)
        bx = max(1, min(self.view_width - clean_len - 3, x))
        by = max(0, y)

        self.term.draw_text(bx, by, f"┌{'─' * (clean_len + 2)}┐", color)
        self.term.draw_text(bx, by + 1, f"│ {text} │", color + Colors.BOLD)
        self.term.draw_text(bx, by + 2, f"└─v{'─' * (clean_len - 1)}┘", color)

    def _render_tricks_modal(self, dog):
        w = 60
        h = 13
        mx = (self.view_width - w) // 2
        my = 4

        self.term.draw_text(mx, my,     f"╔{'═' * (w - 2)}╗", Colors.GOLD + Colors.BOLD)
        self.term.draw_text(mx, my + 1, f"║{' 🎪 AKADEMIA PSICH SZTUCZEK [T - Zamknij] '.center(w - 2)}║", Colors.BRIGHT_YELLOW + Colors.BOLD)
        self.term.draw_text(mx, my + 2, f"╠{'═' * (w - 2)}╣", Colors.GOLD)

        for i, (k, trick) in enumerate(TRICKS.items()):
            is_unlocked = dog.level >= trick['lvl']
            status = f"{Colors.BRIGHT_GREEN}✓ ODBLOKOWANY{Colors.RESET}" if is_unlocked else f"{Colors.BRIGHT_RED}🔒 Od Poz. {trick['lvl']}{Colors.RESET}"
            hotkey = f"{Colors.BRIGHT_WHITE}[{k}]{Colors.RESET}" if is_unlocked else f"{Colors.GRAY}[-]{Colors.RESET}"
            
            line = f" {hotkey} {trick['name']} ({status}) - {trick['desc'][:20]}"
            self.term.draw_text(mx + 2, my + 3 + i, line[:w-4])

        xp_needed = dog.level * 100
        xp_bar = create_bar(dog.xp, xp_needed, 15, Colors.GOLD)
        self.term.draw_text(mx + 2, my + 9, f"⭐ Poziom: {dog.level} | XP: [{xp_bar}] {int(dog.xp)}/{xp_needed} | Wykonano: {dog.tricks_performed}", Colors.BRIGHT_CYAN)
        self.term.draw_text(mx, my + 10, f"╚{'═' * (w - 2)}╝", Colors.GOLD + Colors.BOLD)

    def _render_shop_modal(self, dog, selected_idx):
        w = 64
        h = 13
        mx = (self.view_width - w) // 2
        my = 4

        self.term.draw_text(mx, my,     f"╔{'═' * (w - 2)}╗", Colors.GOLD + Colors.BOLD)
        self.term.draw_text(mx, my + 1, f"║{' 👨‍🌾 SKLEPIK PANA OGRODNIKA [K - Zamknij] '.center(w - 2)}║", Colors.BRIGHT_YELLOW + Colors.BOLD)
        self.term.draw_text(mx, my + 2, f"╠{'═' * (w - 2)}╣", Colors.GOLD)

        item_keys = list(SHOP_ITEMS.keys())
        for i, key in enumerate(item_keys):
            item = SHOP_ITEMS[key]
            is_owned = key in dog.inventory
            is_equipped = dog.equipped_item == key
            is_sel = (i == selected_idx)

            sel_mark = f"{Colors.GOLD}▶ {Colors.RESET}" if is_sel else "  "
            
            if is_equipped:
                status_txt = f"{Colors.BRIGHT_GREEN}[ZAŁOŻONY]{Colors.RESET}"
            elif is_owned:
                status_txt = f"{Colors.BRIGHT_CYAN}[POSIADANY - Enter aby założyć]{Colors.RESET}"
            else:
                can_afford = dog.bones_currency >= item['price']
                afford_c = Colors.GOLD if can_afford else Colors.BRIGHT_RED
                status_txt = f"{afford_c}Cena: {item['price']} 🦴{Colors.RESET}"

            line = f"{sel_mark}{item['name']} {status_txt}"
            self.term.draw_text(mx + 2, my + 3 + i, line)

        self.term.draw_text(mx + 2, my + 9, f"🦴 Twoje Psie Kostki: {dog.bones_currency} | Użyj [W/S/↑/↓] wybór, [ENTER] Kup/Załóż, [U] Zdejmij", Colors.BRIGHT_CYAN)
        self.term.draw_text(mx, my + 10, f"╚{'═' * (w - 2)}╝", Colors.GOLD + Colors.BOLD)

    def render_hud(self, dog, world):
        hud_y = world.ground_base_y + 2
        w = self.view_width

        # Border separator
        self.term.draw_text(0, hud_y, "═" * w, Colors.CYAN + Colors.BOLD)

        # Line 1: Header / Dog Identity, Mood, Biome Zone & Time of Day
        time_name, _, _, _ = world.get_time_of_day_info()
        zone_name, zone_ico, zone_col = world.get_zone_info(dog.x)
        mood_txt, mood_col = dog.get_status_mood()

        equipped_tag = f" {SHOP_ITEMS[dog.equipped_item]['icon']}" if dog.equipped_item else ""
        header = f" 🐕 {Colors.BOLD}{dog.breed.name.upper()}{equipped_tag}{Colors.RESET} | {zone_col}{zone_ico} {zone_name}{Colors.RESET} | {time_name} | {mood_col}{mood_txt}{Colors.RESET}"
        self.term.draw_text(0, hud_y + 1, header)
        
        # Level & Currency in header right
        xp_needed = dog.level * 100
        stats_hdr = f"⭐ Poz. {dog.level} ({int(dog.xp)}/{xp_needed} XP) | 🦴 Kostki: {dog.bones_currency} | 🐾 {int(dog.walk_distance)}m "
        self.term.draw_text(max(0, w - len(stats_hdr) + 8), hud_y + 1, stats_hdr, Colors.GOLD + Colors.BOLD)

        # Line 2: Tamagotchi Need Bars
        h_color = Colors.BRIGHT_GREEN if dog.hunger > 40 else (Colors.YELLOW if dog.hunger > 20 else Colors.BRIGHT_RED)
        h_bar = create_bar(dog.hunger, 100, 8, h_color)
        hunger_str = f"🍖 Głód: [{h_bar}] {int(dog.hunger):>2}%"

        hp_color = Colors.PINK if dog.happiness > 50 else Colors.YELLOW
        hp_bar = create_bar(dog.happiness, 100, 8, hp_color)
        happy_str = f" ❤️  Szczęście: [{hp_bar}] {int(dog.happiness):>2}%"

        b_color = Colors.BRIGHT_RED if dog.bladder > 75 else (Colors.YELLOW if dog.bladder > 45 else Colors.BRIGHT_CYAN)
        b_bar = create_bar(dog.bladder, 100, 8, b_color)
        bladder_str = f" 💧 Pęcherz: [{b_bar}] {int(dog.bladder):>2}%"

        e_color = Colors.BRIGHT_YELLOW if dog.energy > 30 else Colors.BRIGHT_RED
        e_bar = create_bar(dog.energy, 100, 8, e_color)
        energy_str = f" ⚡ Energia: [{e_bar}] {int(dog.energy):>2}%"

        full_bars_line = f" {hunger_str}   {happy_str}   {bladder_str}   {energy_str}"
        self.term.draw_text(0, hud_y + 2, full_bars_line)

        # Line 3: Urgent Reminder or Notification Box
        if world.agility_active:
            race_sec = (world.time_tick - world.agility_start_tick) / 30.0
            best_str = f" | Rekord: {world.agility_best_time:.1f}s" if world.agility_best_time else ""
            alert = f" 🏆 {Colors.GOLD}{Colors.BOLD}TOR AGILITY W TOKU!{Colors.RESET} Czas: {race_sec:.1f}s{best_str} - Biegnij do METY!"
            self.term.draw_text(0, hud_y + 3, alert)
        elif 3.0 <= dog.x <= 17.0:
            if dog.state == "sleep":
                alert = f" 😴 {Colors.CYAN}{Colors.BOLD}PIESEK ŚPI W BUDZIE...{Colors.RESET} Regeneracja energii: {int(dog.energy)}% ⚡ [Z/Q/Ruch - Pobudka]"
            else:
                alert = f" 🛏️ {Colors.CYAN}{Colors.BOLD}JESTEŚ PRZY BUDZIE!{Colors.RESET} Wciśnij {Colors.BRIGHT_WHITE}[Z] / [Q]{Colors.RESET} aby położyć się spać i odnowić energię ⚡💤"
            self.term.draw_text(0, hud_y + 3, alert)
        elif dog.energy < 20:
            alert = f" ⚠️  {Colors.CYAN}{Colors.BOLD}PIESEK JEST ZMĘCZONY NA SZTUCZKI!{Colors.RESET} Wróć do budy 🏠 (Ogród) i wciśnij [Z / Q], by się wyspać!"
            self.term.draw_text(0, hud_y + 3, alert)
        elif dog.hunger < 25:
            alert = f" ⚠️  {Colors.BRIGHT_RED}{Colors.BOLD}PIESEK JEST GŁODNY!{Colors.RESET} Zbierz kość 🦴 lub miskę 🥣!"
            self.term.draw_text(0, hud_y + 3, alert)
        elif dog.bladder > 80:
            alert = f" ⚠️  {Colors.BRIGHT_YELLOW}{Colors.BOLD}PIESEK CHCE SIKU!{Colors.RESET} Podejdź do drzewa 🌳 / hydrantu 🚰 i wciśnij [S]!"
            self.term.draw_text(0, hud_y + 3, alert)
        elif dog.happiness < 30:
            alert = f" ⚠️  {Colors.PINK}{Colors.BOLD}PIESEK JEST SMUTNY!{Colors.RESET} Zrób sztuczkę [T], pobaw się piłką ⚽ lub poproś o głaski [E]!"
            self.term.draw_text(0, hud_y + 3, alert)
        else:
            tip = f" 💡 {Colors.DIM}Sklep u Ogrodnika: [K] | Sztuczki: [T] | Sen w budzie: [Z/Q] | Dźwięk PC: [M]{Colors.RESET}"
            self.term.draw_text(0, hud_y + 3, tip)

        # Line 4: Controls Legend
        snd_status = f"{Colors.BRIGHT_GREEN}🔊{Colors.RESET}" if audio.enabled else f"{Colors.BRIGHT_RED}🔇{Colors.RESET}"
        controls = f" {Colors.DARK_GRAY}STEROWANIE:{Colors.RESET} {Colors.BRIGHT_WHITE}[←/→]{Colors.RESET} Bieg {Colors.BRIGHT_WHITE}[Spacja/↑]{Colors.RESET} Skok {Colors.BRIGHT_WHITE}[B]{Colors.RESET} Szczek {Colors.BRIGHT_WHITE}[T]{Colors.RESET} Triki {Colors.BRIGHT_WHITE}[K]{Colors.RESET} Sklep {Colors.BRIGHT_WHITE}[E]{Colors.RESET} Głaski {Colors.BRIGHT_WHITE}[S]{Colors.RESET} Siku {Colors.BRIGHT_WHITE}[Z/Q]{Colors.RESET} Sen w budzie {Colors.BRIGHT_WHITE}[M]{Colors.RESET} {snd_status} {Colors.BRIGHT_WHITE}[P]{Colors.RESET} Pauza {Colors.BRIGHT_WHITE}[ESC]{Colors.RESET} Menu"
        self.term.draw_text(0, hud_y + 4, controls)


def draw_breed_selection_menu(terminal, selected_index=0):
    terminal.clear_buffer()
    w = terminal.target_width
    h = terminal.target_height

    title_art = [
        "  ██████╗  ██████╗  ██████╗  ████████╗ █████╗ ███╗   ███╗ █████╗  ██████╗  ██████╗ ████████╗ ██████╗██╗  ██╗██╗",
        "  ██╔══██╗██╔═══██╗██╔════╝  ╚══██╔══╝██╔══██╗████╗ ████║██╔══██╗██╔════╝ ██╔═══██╗╚══██╔══╝██╔════╝██║  ██║██║",
        "  ██║  ██║██║   ██║██║  ███╗    ██║   ███████║██╔████╔██║███████║██║  ███╗██║   ██║   ██║   ██║     ███████║██║",
        "  ██║  ██║██║   ██║██║   ██║    ██║   ██╔══██║██║╚██╔╝██║██╔══██║██║   ██║██║   ██║   ██║   ██║     ██╔══██║██║",
        "  ██████╔╝╚██████╔╝╚██████╔╝    ██║   ██║  ██║██║ ╚═╝ ██║██║  ██║╚██████╔╝╚██████╔╝   ██║   ╚██████╗██║  ██║██║",
        "  ╚═════╝  ╚═════╝  ╚═════╝     ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝"
    ]

    for idx, line in enumerate(title_art):
        terminal.draw_text(max(0, (w - len(line)) // 2), 1 + idx, line, Colors.GOLD + Colors.BOLD)

    sub = "🐾 PLATFORMOWY SYMULATOR PSA & TAMAGOTCHI 2D 🐾"
    terminal.draw_text((w - len(sub)) // 2, 8, sub, Colors.BRIGHT_CYAN + Colors.BOLD)

    prompt = "--- WYBIERZ SWOJĄ RASĘ PIESKA ---"
    terminal.draw_text((w - len(prompt)) // 2, 10, prompt, Colors.BRIGHT_WHITE + Colors.UNDERLINE)

    breed_keys = list(BREEDS.keys())
    
    card_width = 19
    spacing = 1
    total_cards_w = len(breed_keys) * card_width + (len(breed_keys) - 1) * spacing
    start_x = max(1, (w - total_cards_w) // 2)

    for i, key in enumerate(breed_keys):
        breed = BREEDS[key]
        bx = start_x + i * (card_width + spacing)
        by = 12
        is_selected = (i == selected_index)

        border_col = Colors.GOLD + Colors.BOLD if is_selected else Colors.DARK_GRAY
        title_col = Colors.BRIGHT_YELLOW + Colors.BOLD if is_selected else Colors.WHITE

        terminal.draw_text(bx, by,     f"┌{'─' * (card_width - 2)}┐", border_col)
        terminal.draw_text(bx, by + 1, f"│{breed.name[:card_width-2].center(card_width - 2)}│", title_col)
        terminal.draw_text(bx, by + 2, f"├{'─' * (card_width - 2)}┤", border_col)

        if key == "corgi":
            terminal.draw_text(bx + 5, by + 3, " /^^\\  ", Colors.ORANGE)
            terminal.draw_text(bx + 5, by + 4, "(•ω•) )", Colors.ORANGE)
            terminal.draw_text(bx + 5, by + 5, " /  \\  ", Colors.WHITE)
        elif key == "dachshund":
            terminal.draw_text(bx + 3, by + 3, "  (`.` ) ", Colors.BROWN)
            terminal.draw_text(bx + 3, by + 4, "(•o•)===~", Colors.BROWN)
            terminal.draw_text(bx + 3, by + 5, " /     \\ ", Colors.LIGHT_BROWN)
        elif key == "setter":
            terminal.draw_text(bx + 5, by + 3, " (~~)  ", Colors.fg256(166))
            terminal.draw_text(bx + 5, by + 4, "(•v•)~>", Colors.fg256(166))
            terminal.draw_text(bx + 5, by + 5, " /~ \\~ ", Colors.fg256(208))
        elif key == "shiba":
            terminal.draw_text(bx + 5, by + 3, " ^_^   ", Colors.GOLD)
            terminal.draw_text(bx + 5, by + 4, "(•ᴥ•) @", Colors.GOLD)
            terminal.draw_text(bx + 5, by + 5, " /  \\  ", Colors.CREAM)
        else: # poodle
            terminal.draw_text(bx + 5, by + 3, " 888   ", Colors.PINK)
            terminal.draw_text(bx + 5, by + 4, "(•w•) *", Colors.BRIGHT_WHITE)
            terminal.draw_text(bx + 5, by + 5, " c_c   ", Colors.BRIGHT_WHITE)

        terminal.draw_text(bx, by + 7, f"├{'─' * (card_width - 2)}┤", border_col)
        
        desc_words = breed.description.split(" ")
        line1 = ""
        line2 = ""
        for word in desc_words:
            if len(line1) + len(word) + 1 <= card_width - 4:
                line1 += (" " if line1 else "") + word
            elif len(line2) + len(word) + 1 <= card_width - 4:
                line2 += (" " if line2 else "") + word
        
        terminal.draw_text(bx + 2, by + 8, line1[:card_width-4], Colors.GRAY)
        terminal.draw_text(bx + 2, by + 9, line2[:card_width-4], Colors.GRAY)
        terminal.draw_text(bx, by + 10, f"└{'─' * (card_width - 2)}┘", border_col)

        if is_selected:
            terminal.draw_text(bx + 3, by + 11, "▲ [WYBRANY] ▲", Colors.BRIGHT_GREEN + Colors.BOLD)

    footer = "Użyj [← / → / A / D] aby wybrać rasę, wciśnij [ENTER / SPACJA] aby rozpocząć grę! [Q] Wyjście"
    terminal.draw_text((w - len(footer)) // 2, h - 3, footer, Colors.BRIGHT_CYAN)
