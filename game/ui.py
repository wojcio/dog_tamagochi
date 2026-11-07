"""
Game UI, Multi-Biome World Renderer, Day/Night Lighting, Tamagotchi HUD,
Tricks Menu, Gardener Shop, and Breed Selector.
"""

import re
import time

from game.engine import Colors, str_width
from game.dog import BREEDS, TRICKS, SHOP_ITEMS
from game.world import zone_at, PARK_STREAM_MIN, PARK_STREAM_MAX, ZEBRA_MIN, ZEBRA_MAX
from game.audio import audio
from game import quests as QuestSystem

def visible_width(s):
    """Width of a string that may contain ANSI escape codes and emoji."""
    return str_width(re.sub(r'\033\[[0-9;]*[A-Za-z]', '', s))

def center_text(text, width):
    """Center text within `width` columns, counting emoji as 2 cells."""
    pad = max(0, width - visible_width(text))
    left = pad // 2
    return ' ' * left + text + ' ' * (pad - left)

TITLE_ART = [
    "  ██████╗  ██████╗  ██████╗  ████████╗ █████╗ ███╗   ███╗ █████╗  ██████╗  ██████╗ ████████╗ ██████╗██╗  ██╗██╗",
    "  ██╔══██╗██╔═══██╗██╔════╝  ╚══██╔══╝██╔══██╗████╗ ████║██╔══██╗██╔════╝ ██╔═══██╗╚══██╔══╝██╔════╝██║  ██║██║",
    "  ██║  ██║██║   ██║██║  ███╗    ██║   ███████║██╔████╔██║███████║██║  ███╗██║   ██║   ██║   ██║     ███████║██║",
    "  ██║  ██║██║   ██║██║   ██║    ██║   ██╔══██║██║╚██╔╝██║██╔══██║██║   ██║██║   ██║   ██║   ██║     ██╔══██║██║",
    "  ██████╔╝╚██████╔╝╚██████╔╝    ██║   ██║  ██║██║ ╚═╝ ██║██║  ██║╚██████╔╝╚██████╔╝   ██║   ╚██████╗██║  ██║██║",
    "  ╚═════╝  ╚═════╝  ╚═════╝     ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝"
]

def draw_banner(terminal, subtitle="🐾 PLATFORMOWY SYMULATOR PSA & TAMAGOTCHI 2D 🐾", top=1):
    """Draw the shared ASCII title + emoji subtitle, centered and width-correct."""
    w = terminal.target_width
    for idx, line in enumerate(TITLE_ART):
        terminal.draw_text(max(0, (w - len(line)) // 2), top + idx, line, Colors.GOLD + Colors.BOLD)
    if subtitle:
        terminal.draw_text(max(0, (w - visible_width(subtitle)) // 2), top + len(TITLE_ART) + 1,
                           subtitle, Colors.BRIGHT_CYAN + Colors.BOLD)

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
        self._quests_ctx = None

    def render_world_and_hud(self, world, dog, npcs, pigeons, cats, crabs,
                             squirrels=None, ducks=None, dog_friends=None,
                             modal_state=None, modal_data=None, quests=None):
        squirrels = squirrels or []
        ducks = ducks or []
        dog_friends = dog_friends or []
        self.term.clear_buffer()
        self._quests_ctx = quests

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

            # Forest Pine (Las) - tall dark silhouette
            elif prop.prop_type == 'pine':
                if px + 8 > 0 and px < self.view_width:
                    pine_c = Colors.BLACK if is_night else Colors.DARK_GREEN
                    pine_c2 = Colors.DARK_GREEN if is_night else Colors.GRASS_GREEN
                    self.term.draw_text(px + 3, 4,  "  ▲  ", pine_c2 + Colors.BOLD)
                    self.term.draw_text(px + 2, 5,  " ▲▲▲ ", pine_c + Colors.BOLD)
                    self.term.draw_text(px + 1, 6,  "▲▲▲▲▲", pine_c2 + Colors.BOLD)
                    self.term.draw_text(px + 2, 7,  " ▲▲▲ ", pine_c + Colors.BOLD)
                    self.term.draw_text(px + 1, 8,  "▲▲▲▲▲", pine_c2 + Colors.BOLD)
                    self.term.draw_text(px,     9, "▲▲▲▲▲▲▲", pine_c + Colors.BOLD)
                    self.term.draw_text(px + 1, 10, "▲▲▲▲▲", pine_c2 + Colors.BOLD)
                    self.term.draw_text(px + 1, 11, "▲▲▲▲▲", pine_c + Colors.BOLD)
                    self.term.draw_text(px + 2, 12, "▲▲▲▲▲", pine_c2 + Colors.BOLD)
                    for ty in range(13, ground_y):
                        self.term.draw_text(px + 3, ty, " | ", Colors.BROWN)
                    self.term.draw_text(px + 2, ground_y, "_|_|_", Colors.BROWN + Colors.BOLD)
                    if prop.marked:
                        self.term.draw_text(px + 1, ground_y - 1, "💧✓", Colors.BRIGHT_CYAN + Colors.BOLD)

            # Fallen Log (Las)
            elif prop.prop_type == 'log':
                if px + prop.width > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 2, "(≈" + "=" * (prop.width - 4) + "≈)", Colors.LIGHT_BROWN + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 1, "(" + "░" * (prop.width - 2) + ")", Colors.BROWN)

            # Mushroom (Las floor)
            elif prop.prop_type == 'mushroom':
                if px + 2 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 1, "🍄", Colors.RED)

            # Fern (Las floor)
            elif prop.prop_type == 'fern':
                if px + 3 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 1, "\\|/", Colors.DARK_GREEN + Colors.BOLD)

            # Reed (Rzeka banks)
            elif prop.prop_type == 'reed':
                if px + 3 > 0 and px < self.view_width:
                    sway = "/" if (dog.anim_tick // 10) % 2 == 0 else "\\"
                    self.term.draw_text(px, ground_y - 2, "|╥" + sway, Colors.DARK_GREEN + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 1, "|║|", Colors.GREEN)

            # Rock
            elif prop.prop_type == 'rock':
                if px + 3 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 1, "(#)", Colors.GRAY + Colors.BOLD)

            # Dog Park Fence (long rails with posts)
            elif prop.prop_type == 'fence':
                if px + prop.width > 0 and px < self.view_width:
                    for col in range(prop.width):
                        sx = px + col
                        if not (0 <= sx < self.view_width):
                            continue
                        if col % 4 == 0:
                            self.term.draw_char(sx, ground_y - 3, '╬', Colors.LIGHT_BROWN + Colors.BOLD)
                            self.term.draw_char(sx, ground_y - 2, '║', Colors.LIGHT_BROWN)
                            self.term.draw_char(sx, ground_y - 1, '║', Colors.LIGHT_BROWN)
                        else:
                            self.term.draw_char(sx, ground_y - 3, '═', Colors.LIGHT_BROWN)
                            self.term.draw_char(sx, ground_y - 2, '─', Colors.BROWN)
                            self.term.draw_char(sx, ground_y - 1, '─', Colors.BROWN)

            # Dog Park Gate Sign
            elif prop.prop_type == 'park_sign':
                if px + 9 > 0 and px < self.view_width:
                    self.term.draw_text(px - 1, ground_y - 5, "┌────────┐", Colors.BRIGHT_MAGENTA + Colors.BOLD)
                    self.term.draw_text(px - 1, ground_y - 4, "│PSI PARK🎾│", Colors.BRIGHT_MAGENTA + Colors.BOLD)
                    self.term.draw_text(px - 1, ground_y - 3, "└───┬────┘", Colors.BRIGHT_MAGENTA)
                    self.term.draw_text(px + 2, ground_y - 2, "│", Colors.BROWN)
                    self.term.draw_text(px + 2, ground_y - 1, "│", Colors.BROWN)

            # Ball Pit (Psi Park)
            elif prop.prop_type == 'ballpit':
                if px + prop.width > 0 and px < self.view_width:
                    balls = ""
                    for col in range(prop.width):
                        if col % 2 == 0:
                            balls += "●"
                        else:
                            balls += "○"
                    self.term.draw_text(px, ground_y - 1, "⚽" + balls + "⚽", Colors.BRIGHT_YELLOW + Colors.BOLD)
                    self.term.draw_text(px, ground_y, "[" + "~" * (prop.width + 2) + "]", Colors.GOLD)

            # Agility Tunnel (Psi Park)
            elif prop.prop_type == 'tunnel':
                if px + prop.width > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 2, " .----. ", Colors.BRIGHT_BLUE + Colors.BOLD)
                    self.term.draw_text(px, ground_y - 1, "( ⭕⭕ )", Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_text(px, ground_y,     "`-'--'-`", Colors.BRIGHT_BLUE)

            # Parked Bicycle (Ulica)
            elif prop.prop_type == 'bike':
                if px + 6 > 0 and px < self.view_width:
                    self.term.draw_text(px, ground_y - 2, " _ o", Colors.BRIGHT_CYAN)
                    self.term.draw_text(px, ground_y - 1, "/|_\\|", Colors.BRIGHT_WHITE + Colors.BOLD)
                    self.term.draw_text(px, ground_y,     "o   o", Colors.BRIGHT_BLACK)

            # Traffic Light (Ulica) - synced with the car signal!
            elif prop.prop_type == 'traffic_light':
                if px + 4 > 0 and px < self.view_width:
                    g_on = world.signal_green
                    c_g = Colors.BRIGHT_GREEN + Colors.BOLD if g_on else Colors.DARK_GRAY
                    c_r = Colors.BRIGHT_RED + Colors.BOLD if not g_on else Colors.DARK_GRAY
                    self.term.draw_text(px, ground_y - 5, "[=]", Colors.DARK_GRAY)
                    self.term.draw_char(px + 1, ground_y - 4, '●' if g_on else '○', c_g)
                    self.term.draw_char(px + 1, ground_y - 3, '●' if not g_on else '○', c_r)
                    for ty in range(ground_y - 2, ground_y):
                        self.term.draw_text(px + 1, ty, "|", Colors.DARK_GRAY)
                    self.term.draw_text(px, ground_y, "[=]", Colors.DARK_GRAY)

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

        # 5. Render Toy Balls (garden + dog park pit)
        for ball in world.balls:
            bx = int(ball.x) - camera_x
            by = int(ball.y)
            if 0 <= bx < self.view_width:
                self.term.draw_text(bx, by, "⚽(o)", Colors.BRIGHT_WHITE + Colors.BOLD)

        # 5b. Render River Ducks (on the water surface, under the dog)
        for duck in ducks:
            ux = int(duck.x) - camera_x
            uy = int(duck.y)
            if 0 <= ux < self.view_width:
                self.term.draw_colored_sprite(ux, uy, duck.get_sprite())

        # 5c. Render Street Cars (road level, above ground, below the dog)
        for car in world.cars:
            cx = int(car["x"]) - camera_x
            if -6 < cx < self.view_width:
                c_body = Colors.BRIGHT_RED if car["style"] == '🚗' else \
                         Colors.BRIGHT_YELLOW if car["style"] == '🚕' else \
                         Colors.BRIGHT_BLUE if car["style"] == '🚓' else Colors.BRIGHT_CYAN
                self.term.draw_text(cx, ground_y - 3, " _[]_ ", c_body + Colors.BOLD)
                self.term.draw_text(cx, ground_y - 2, car["style"] + "|=|", c_body + Colors.BOLD)
                self.term.draw_text(cx, ground_y - 1, "o---o", Colors.BRIGHT_BLACK + Colors.BOLD)

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

        # 7b. Render Squirrels (Las & Ulica)
        for sq in squirrels:
            sx = int(sq.x) - camera_x
            sy = int(sq.y)
            if 0 <= sx < self.view_width:
                self.term.draw_colored_sprite(sx, sy, sq.get_sprite())

        # 8. Render Humans (NPCs)
        for human in npcs:
            hx = int(human.x) - camera_x
            hy = int(human.y)
            if -5 < hx < self.view_width:
                self.term.draw_colored_sprite(hx, hy, human.get_sprite())
                if human.speech_bubble:
                    self._draw_speech_bubble(hx - 4, hy - 2, human.speech_bubble[0], human.speech_bubble[1])

        # 8b. Render Dog Friends (Psi Park)
        for pal in dog_friends:
            fx = int(pal.x) - camera_x
            fy = int(pal.y)
            if -6 < fx < self.view_width:
                self.term.draw_colored_sprite(fx, fy, pal.get_sprite())
                if pal.speech_bubble:
                    self._draw_speech_bubble(fx - 3, fy - 2, pal.speech_bubble[0], pal.speech_bubble[1])

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

        # Dripping wet after swimming!
        if dog.wet_timer > 0:
            drip = '💦' if (dog.anim_tick // 4) % 2 == 0 else '˙'
            self.term.draw_text(dx + 1, max(0, dy - 1), drip, Colors.BRIGHT_CYAN + Colors.BOLD)

        # Dog speech / action bubble
        if dog.speech_bubble:
            self._draw_speech_bubble(dx - 3, dy - 2, dog.speech_bubble[0], dog.speech_bubble[1])

        # 10. Render Biome Ground & Terrain (driven by the ZONES table)
        for x in range(self.view_width):
            world_x = camera_x + x
            zone = world.zone_at(world_x)
            style = zone["ground"]

            if style == "garden":  # Ogród
                grass_ch = "w" if world_x % 3 == 0 else ("W" if world_x % 3 == 1 else "v")
                flower_ch = "🌸" if world_x % 15 == 0 else ("🌼" if world_x % 21 == 0 else grass_ch)
                if flower_ch in ["🌸", "🌼"]:
                    self.term.draw_text(x, ground_y, flower_ch, Colors.PINK)
                else:
                    self.term.draw_char(x, ground_y, grass_ch, Colors.GRASS_GREEN + Colors.BOLD)
                self.term.draw_char(x, ground_y + 1, "░", Colors.BROWN)

            elif style == "forest":  # Las
                grass_ch = "v" if world_x % 3 == 0 else "W"
                self.term.draw_char(x, ground_y, grass_ch, Colors.DARK_GREEN + Colors.BOLD)
                if world_x % 7 == 0:
                    self.term.draw_char(x, ground_y, '·', Colors.BRIGHT_BLACK)  # pine needles
                self.term.draw_char(x, ground_y + 1, "▒", Colors.BROWN)

            elif style == "river":  # Rzeka
                if world.is_water(world_x):
                    wave_ch = "≈" if (dog.anim_tick // 3 + world_x) % 2 == 0 else "~"
                    self.term.draw_char(x, ground_y, wave_ch, Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "▓", Colors.BLUE)
                else:
                    grass_ch = "W" if world_x % 2 == 0 else "w"
                    self.term.draw_char(x, ground_y, grass_ch, Colors.DARK_GREEN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "░", Colors.BROWN)

            elif style == "park":  # Park Miejski
                if PARK_STREAM_MIN <= world_x <= PARK_STREAM_MAX:  # Stream under bridge
                    wave_ch = "~" if (dog.anim_tick // 4 + world_x) % 2 == 0 else "≈"
                    self.term.draw_char(x, ground_y, wave_ch, Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "▓", Colors.BLUE)
                else:
                    grass_ch = "W" if world_x % 2 == 0 else "w"
                    self.term.draw_char(x, ground_y, grass_ch, Colors.DARK_GREEN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "░", Colors.BROWN)

            elif style == "dogpark":  # Psi Park
                grass_ch = "W" if world_x % 2 == 0 else "w"
                if world_x % 23 == 0:
                    self.term.draw_text(x, ground_y, "🎾", Colors.BRIGHT_YELLOW)
                else:
                    self.term.draw_char(x, ground_y, grass_ch, Colors.GRASS_GREEN + Colors.BOLD)
                self.term.draw_char(x, ground_y + 1, "░", Colors.BROWN)

            elif style == "street":  # Ulica
                if ZEBRA_MIN <= world_x <= ZEBRA_MAX:
                    zeb = "█" if ((world_x - ZEBRA_MIN) // 2) % 2 == 0 else "▂"
                    col = Colors.BRIGHT_WHITE if zeb == "█" else Colors.BRIGHT_BLACK
                    self.term.draw_char(x, ground_y, zeb, col + Colors.BOLD)
                elif (world_x - zone["start"]) < 3 or (zone["end"] - world_x) <= 3:
                    self.term.draw_char(x, ground_y, "▄", Colors.WHITE)  # krawężnik / curb
                else:
                    lane = "-" if (world_x + dog.anim_tick // 20) % 8 < 3 else "▂"
                    self.term.draw_char(x, ground_y, lane, Colors.BRIGHT_BLACK + Colors.BOLD)
                self.term.draw_char(x, ground_y + 1, "▒", Colors.DARK_GRAY)

            elif style == "beach":  # Słoneczna Plaża
                if world_x > zone["end"] - 20:  # Ocean shore
                    wave_ch = "≈" if (dog.anim_tick // 3 + world_x) % 2 == 0 else "~"
                    self.term.draw_char(x, ground_y, wave_ch, Colors.BRIGHT_CYAN + Colors.BOLD)
                    self.term.draw_char(x, ground_y + 1, "▓", Colors.BLUE)
                else:
                    sand_ch = "░" if world_x % 2 == 0 else "▒"
                    self.term.draw_char(x, ground_y, sand_ch, Colors.GOLD)
                    self.term.draw_char(x, ground_y + 1, "▒", Colors.BROWN)

            else:  # turf — Tor Agility
                turf_ch = "=" if world_x % 2 == 0 else "_"
                turf_col = Colors.BRIGHT_RED if world_x % 6 < 3 else Colors.BRIGHT_WHITE
                self.term.draw_char(x, ground_y, turf_ch, turf_col + Colors.BOLD)
                self.term.draw_char(x, ground_y + 1, "░", Colors.DARK_GRAY)

        # 10b. Fireflies over the Las at night ✨
        if is_night:
            for x in range(self.view_width):
                world_x = camera_x + x
                if zone_at(world_x)["id"] == "forest":
                    if (world_x * 7 + world.time_tick // 25) % 29 == 0:
                        fy = 13 + (world_x * 5) % 5
                        self.term.draw_char(x, fy, '✦', Colors.BRIGHT_YELLOW)
                    elif (world_x * 13 + world.time_tick // 40) % 37 == 0:
                        fy = 12 + (world_x * 3) % 6
                        self.term.draw_char(x, fy, '·', Colors.BRIGHT_YELLOW + Colors.DIM)

        # 11. Render Modals (if active)
        if modal_state == "tricks":
            self._render_tricks_modal(dog)
        elif modal_state == "shop":
            self._render_shop_modal(dog, modal_data or 0)
        elif modal_state == "quests":
            self._render_quest_modal(dog, modal_data)

        # 12. Render Tamagotchi HUD
        self.render_hud(dog, world, quests=self._quests_ctx)

    def _draw_speech_bubble(self, x, y, text, color=Colors.BRIGHT_WHITE):
        clean_len = str_width(text)
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
        self.term.draw_text(mx, my + 1, f"║{center_text(' 🎪 AKADEMIA PSICH SZTUCZEK [T - Zamknij] ', w - 2)}║", Colors.BRIGHT_YELLOW + Colors.BOLD)
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
        self.term.draw_text(mx, my + 1, f"║{center_text(' 🪴 SKLEPIK PANA OGRODNIKA [K - Zamknij] ', w - 2)}║", Colors.BRIGHT_YELLOW + Colors.BOLD)
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

    def _render_quest_modal(self, dog, quest_state):
        w = 64
        mx = (self.view_width - w) // 2
        my = 4

        self.term.draw_text(mx, my,     f"╔{'═' * (w - 2)}╗", Colors.GOLD + Colors.BOLD)
        self.term.draw_text(mx, my + 1, f"║{center_text(' 📋 CODZIENNE ZADANIA [R - Zamknij] ', w - 2)}║", Colors.BRIGHT_YELLOW + Colors.BOLD)
        self.term.draw_text(mx, my + 2, f"╠{'═' * (w - 2)}╣", Colors.GOLD)

        done = QuestSystem.done_count(quest_state)
        total = QuestSystem.total_count(quest_state)

        y = my + 3
        for q in (quest_state or {}).get("quests", []):
            prog = QuestSystem.progress_of(q, dog)
            if q["done"]:
                bar = create_bar(1, 1, 12, Colors.BRIGHT_GREEN)
                line_col = Colors.BRIGHT_GREEN
                mark = "✓"
            else:
                bar = create_bar(min(prog, q["target"]), q["target"], 12, Colors.GOLD, Colors.DARK_GRAY)
                line_col = Colors.BRIGHT_WHITE
                mark = "○"
            got = int(prog)
            label = f"{mark} {q['text']}"
            if visible_width(label) > w - 26:
                label = label[:w - 28]
            tail = f"{got}/{q['target']}"
            self.term.draw_text(mx + 2, y, label, line_col)
            self.term.draw_text(mx + w - 18, y, f"[{bar}]", line_col)
            self.term.draw_text(mx + w - 6, y, tail, Colors.BRIGHT_CYAN)
            y += 1

        earned = sum(q["bones"] for q in (quest_state or {}).get("quests", []) if q["done"])
        self.term.draw_text(mx + 2, y + 1,
                            f"Ukończone dziś: {done}/{total} | Nagroda za dzień: {earned} 🦴 | Nowe zadania co dobę 🌅",
                            Colors.BRIGHT_CYAN)
        self.term.draw_text(mx, y + 2, f"╚{'═' * (w - 2)}╝", Colors.GOLD + Colors.BOLD)

    def render_hud(self, dog, world, quests=None):
        hud_y = world.ground_base_y + 2
        w = self.view_width

        # Border separator
        self.term.draw_text(0, hud_y, "═" * w, Colors.CYAN + Colors.BOLD)

        # Line 1: Header / Dog Identity, Mood, Biome Zone & Time of Day
        time_name, _, _, _ = world.get_time_of_day_info()
        zone_name, zone_ico, zone_col = world.get_zone_info(dog.x)
        mood_txt, mood_col = dog.get_status_mood()

        equipped_tag = f" {SHOP_ITEMS[dog.equipped_item]['icon']}" if dog.equipped_item else ""
        name = getattr(dog, "name", "") or ""
        identity = f"{Colors.BOLD}{name}·{dog.breed.name}{Colors.RESET}" if name else f"{Colors.BOLD}{dog.breed.name.upper()}{Colors.RESET}"
        header = f" 🐕 {identity}{equipped_tag} | {zone_col}{zone_ico} {zone_name}{Colors.RESET} | {time_name} | {mood_col}{mood_txt}{Colors.RESET}"
        self.term.draw_text(0, hud_y + 1, header)

        # Level & Currency in header right (compact; walk distance lives in achievements)
        days = getattr(dog, "days_together", 0)
        xp_needed = dog.level * 100
        badge = ""
        if quests and QuestSystem.total_count(quests):
            badge = f" | 📋 {QuestSystem.done_count(quests)}/{QuestSystem.total_count(quests)}"
        stats_hdr = f"⭐ Poz. {dog.level} ({int(dog.xp)}/{xp_needed} XP) | 🦴 {dog.bones_currency} | 📅 {days}d{badge}"
        # Long dog names can collide with the stats; drop the XP fraction first.
        if visible_width(header) + visible_width(stats_hdr) > w - 1:
            stats_hdr = f"⭐ {dog.level} | 🦴 {dog.bones_currency} | 📅 {days}d{badge}"
        self.term.draw_text(max(0, w - visible_width(stats_hdr)), hud_y + 1, stats_hdr, Colors.GOLD + Colors.BOLD)

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

    draw_banner(terminal)

    prompt = "--- WYBIERZ SWOJĄ RASĘ PIESKA ---"
    terminal.draw_text((w - visible_width(prompt)) // 2, 10, prompt, Colors.BRIGHT_WHITE + Colors.UNDERLINE)

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

    footer = "Użyj [← / → / A / D] aby wybrać rasę, wciśnij [ENTER / SPACJA] aby nadać imię! [Q] Wyjście"
    terminal.draw_text(max(0, (w - visible_width(footer)) // 2), h - 3, footer, Colors.BRIGHT_CYAN)


def draw_start_menu(terminal, save_info, selected=0):
    """Resume / New-game start screen shown when a save exists.

    save_info: dict(name, breed_name, level, days, bones). selected: 0=Continue, 1=New.
    """
    terminal.clear_buffer()
    w = terminal.target_width
    h = terminal.target_height
    draw_banner(terminal, subtitle="🐾 POWRÓT DO DOMU 🐾")

    name = save_info.get("name") or "Piesek"
    breed = save_info.get("breed_name", "")
    level = save_info.get("level", 1)
    days = save_info.get("days", 0)
    bones = save_info.get("bones", 0)

    box_w = 56
    bx = (w - box_w) // 2
    by = 11

    terminal.draw_text(bx, by,     "╔" + "═" * (box_w - 2) + "╗", Colors.GOLD + Colors.BOLD)
    info = center_text(f"🏠 {name}  ·  {breed}", box_w - 2)
    terminal.draw_text(bx, by + 1, "║" + info + "║", Colors.BRIGHT_YELLOW + Colors.BOLD)
    stats = center_text(f"⭐ Poz. {level}   📅 Razem: {days} dni   🦴 {bones}", box_w - 2)
    terminal.draw_text(bx, by + 2, "║" + stats + "║", Colors.BRIGHT_CYAN)
    terminal.draw_text(bx, by + 3, "╚" + "═" * (box_w - 2) + "╝", Colors.GOLD + Colors.BOLD)

    opt1 = center_text("[ENTER]  Kontynuuj opiekę nad pieskiem", box_w)
    opt2 = center_text("[N]  Adoptuj nowego szczeniaka (nadpisze zapis)", box_w)
    c1 = Colors.BRIGHT_GREEN + Colors.BOLD if selected == 0 else Colors.WHITE
    c2 = Colors.BRIGHT_MAGENTA + Colors.BOLD if selected == 1 else Colors.WHITE
    m1 = "▶ " if selected == 0 else "  "
    m2 = "▶ " if selected == 1 else "  "
    terminal.draw_text(bx, by + 5, m1 + opt1, c1)
    terminal.draw_text(bx, by + 6, m2 + opt2, c2)

    foot = "[↑/↓] wybór   [Q] Wyjdź"
    terminal.draw_text(max(0, (w - visible_width(foot)) // 2), h - 3, foot, Colors.DARK_GRAY)


def draw_name_input(terminal, name_buffer, breed, max_len=14):
    """Text-entry screen to name the new dog. Draws a breed sprite + input box."""
    terminal.clear_buffer()
    w = terminal.target_width
    h = terminal.target_height
    draw_banner(terminal, subtitle="🐾 ADOPTUJ SZCZENIAKA 🐾")

    prompt = f"Jak nazwiesz swojego {breed.name}?"
    terminal.draw_text(max(0, (w - visible_width(prompt)) // 2), 11, prompt, Colors.BRIGHT_WHITE + Colors.BOLD)

    # Breed sprite preview
    art = {
        "corgi":      [" /^^\\ ", "(•ω•) )", " /  \\ "],
        "dachshund":  [" (`.` ) ", "(•o•)==~", " /    \\ "],
        "setter":     [" (~~)  ", "(•v•)~>", " /~\\~ "],
        "shiba":      [" ^_^   ", "(•ᴥ•) @", " /  \\ "],
        "poodle":     ["  888  ", "(•w•) *", " c_c   "],
    }.get(breed_key_of(breed), [" (•ω•) "])
    sx = (w - 9) // 2
    for i, row in enumerate(art):
        terminal.draw_text(sx, 13 + i, row, breed.fur + Colors.BOLD)

    # Input box
    box_w = max(24, min(max_len + 6, 40))
    bx = (w - box_w) // 2
    by = 17
    terminal.draw_text(bx, by, "┌" + "─" * (box_w - 2) + "┐", Colors.GOLD + Colors.BOLD)
    field = name_buffer + ("█" if (int(time.time() * 2) % 2 == 0) else " ")
    field = field[:max_len]
    terminal.draw_text(bx + 2, by + 1, field, Colors.BRIGHT_GREEN + Colors.BOLD)
    terminal.draw_text(bx, by + 2, "└" + "─" * (box_w - 2) + "┘", Colors.GOLD + Colors.BOLD)

    hint = "[a-z] wpisz imię   [⌫] cofnij   [ENTER] gotowe   [ESC] pusty"
    terminal.draw_text(max(0, (w - visible_width(hint)) // 2), by + 4, hint, Colors.DARK_GRAY)


def breed_key_of(breed):
    """Reverse-lookup a breed key from its DogBreed object."""
    for k, v in BREEDS.items():
        if v is breed:
            return k
    return "corgi"
