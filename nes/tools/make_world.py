#!/usr/bin/env python3
"""
Generates the 4-Biome Scrolling World for Dog Tamagotchi NES Edition:
Total World: 128 columns x 30 rows (4 Screens of 32x30)
Outputs:
- screen_0.bin (1024 bytes: Screen 0 initial Nametable + Attributes)
- screen_1.bin (1024 bytes: Screen 1 initial Nametable + Attributes)
- world_cols.bin (3840 bytes: 128 columns x 30 rows in column-major order)
"""

import sys

# Screen HUD Headers (Rows 0-5)
HUD_TITLES = [
    "║ DOG TAMAGOTCHI 2D  [NES]     ║", # Screen 0: Ogrod
    "║ [ PARK MIEJSKI & MOSTEK ]    ║", # Screen 1: Park
    "║ [ SŁONECZNA PLAŻA DLA PSÓW ] ║", # Screen 2: Plaza
    "║ [ TOR PRZESZKÓD AGILITY ]    ║"  # Screen 3: Agility
]

def make_hud_rows(screen_idx):
    return [
        "╔══════════════════════════════╗",
        HUD_TITLES[screen_idx],
        "║ GLOD:[████░░]  ENER:[████░░] ║",
        "║ SZCZ:[████░░]  KOSC:  03 🦴  ║",
        "║ STAN: HAU!     POZ: 1 [CORGI]║",
        "╚══════════════════════════════╝"
    ]

SCREENS_SCENERY = {
    0: [ # Ogrod & Dom
        "                                ",
        "                 .---.          ",
        "                (  ☁  )   \\ | / ",
        "                 `---'   --(☀)--",
        "   .---.                  / | \\ ",
        "  (  ☁  )      [===========]    ",
        "   `---'            | |         ",
        "                    | |         ",
        "       [========]   | |         ",
        "          | |       | |         ",
        "   / \\    | |       | |   (~~~~)",
        "  /   \\   | |       | |   |    |",
        " /_____\\  | |  (o)  | |   |    |",
        " | [ ] |  | | =[|]= | |   |    |",
        " | BUDA|  | |  | |  | |   |    |",
        " |____/|  | |  | |  | |   |____|"
    ],
    1: [ # Park Miejski & Drewniany Mostek
        "                                ",
        "   .---.                        ",
        "  (  ☁  )                .---.  ",
        "   `---'                (  ☁  ) ",
        "   [ PARK MIEJSKI ]      `---'  ",
        "     (~~~~~~) ⛲                ",
        "     [======]   ================",
        "      |    |    |              |",
        "      |    |    |   [MOSTEK]   |",
        "      |    |    |              |",
        "   (~~~~)       |  ~≈~≈~≈~≈~   |",
        "   |    |       |  ~≈~≈~≈~≈~   |",
        "   |    |  (o)  |  ~≈~≈~≈~≈~   |",
        "   |    | =[|]= |              |",
        "   |    |  | |  |              |",
        "   |____|  | |  |              |"
    ],
    2: [ # Sloneczna Plaza
        "                                ",
        "   \\ | /                        ",
        "  --(☀)--               .---.   ",
        "   / | \\               (  ☁  )  ",
        "  [ SŁONECZNA PLAŻA ]   `---'   ",
        "      /----\\  ⛱️                ",
        "     /______\\      /----\\  ⛱️   ",
        "        |         /______\\      ",
        "      [___/ ]        |          ",
        "      LEZAK        [___/ ]      ",
        "                    LEZAK       ",
        "                                ",
        "        (o)                     ",
        "       =[|]=      (KRAB)        ",
        "        | |       (V..V)        ",
        "        | |        🦀           "
    ],
    3: [ # Tor Agility
        "                                ",
        "  [ TOR AGILITY ]        .---.  ",
        "                        (  ☁  ) ",
        "   ╔════════╗            `---'  ",
        "   ║ 🏁START║  ||||  [====]     ",
        "   ║   >>   ║  🚩🚩  |    |     ",
        "   ╩        ╩  ┴  ┴  |    |     ",
        "                     |    |     ",
        "        ( ⭕ )                  ",
        "         |  |        ╔════════╗ ",
        "        OBRECZ       ║ 🏆META ║ ",
        "        |    |       ║ PUCHAR ║ ",
        "        |    |       ╩        ╩ ",
        "  [==========]                  ",
        "       |                        ",
        "       |                        "
    ]
}

def get_ground_rows(s_idx):
    if s_idx in [0, 1]:
        r22 = "════════════════════════════════"
        r23 = " w   🌸   W   w   v   w   W  ~≈~"
        fill = "░▒░▒░▒░▒░▒░▒░▒░▒░▒░▒░▒░▒░▒░▒░▒░▒"
    elif s_idx == 2:
        r22 = "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        r23 = " ~≈~≈~≈~≈~  ░▒░▒░▒░▒░▒  ~≈~≈~≈~ "
        fill = "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
    else:
        r22 = "════════════════════════════════"
        r23 = "=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_"
        fill = "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒"
    
    rows = [r22, r23]
    for _ in range(6):
        rows.append(fill)
    return rows

GLYPH_MAP = {
    '█': 0x80, '░': 0x81, '▒': 0x82, '▓': 0x83,
    '♥': 0x84, '⚡': 0x85, '🦴': 0x86, '☀': 0x87,
    '☁': 0x88, '🌸': 0x89, '💧': 0x8A, '•': 0x8B,
    'ω': 0x8C, '═': 0x8D, '║': 0x8E, '╔': 0x8F,
    '╗': 0x90, '╚': 0x91, '╝': 0x92, '─': 0x93,
    '│': 0x94, '≈': 0x7E, '~': 0x7E
}

def row_to_bytes(r_str):
    chars = list(r_str)
    if len(chars) < 32:
        chars += [' '] * (32 - len(chars))
    elif len(chars) > 32:
        chars = chars[:32]
    return [GLYPH_MAP.get(ch, ord(ch) & 0xFF) for ch in chars]

def screen_to_matrix(s_idx):
    matrix = []
    for r in make_hud_rows(s_idx):
        matrix.append(row_to_bytes(r))
    for r in SCREENS_SCENERY[s_idx]:
        matrix.append(row_to_bytes(r))
    for r in get_ground_rows(s_idx):
        matrix.append(row_to_bytes(r))
    assert len(matrix) == 30
    return matrix

def main():
    # 1. Generate all 4 screens
    all_matrices = [screen_to_matrix(i) for i in range(4)]

    for s_idx in [0, 1]:
        screen_bytes = []
        for r in all_matrices[s_idx]:
            screen_bytes.extend(r)
        assert len(screen_bytes) == 960

        attr = [0x00] * 64
        for i in range(40, 64):
            attr[i] = 0x55 # Green
        screen_bytes.extend(attr)
        assert len(screen_bytes) == 1024

        with open(f"screen_{s_idx}.bin", "wb") as f:
            f.write(bytearray(screen_bytes))
        print(f"Generated screen_{s_idx}.bin (1024 bytes).")

    # 2. Build world_cols.bin (all 30 rows x 128 columns)
    full_world = []
    for r_idx in range(30):
        full_r = []
        for s_idx in range(4):
            full_r.extend(all_matrices[s_idx][r_idx])
        assert len(full_r) == 128
        full_world.append(full_r)

    # Column-major order: 128 columns x 30 rows = 3840 bytes
    cols_data = []
    for col_idx in range(128):
        for r_idx in range(30):
            cols_data.append(full_world[r_idx][col_idx])

    assert len(cols_data) == 128 * 30 == 3840
    with open("world_cols.bin", "wb") as f:
        f.write(bytearray(cols_data))
    print(f"Generated world_cols.bin (3840 bytes, 128 cols x 30 rows).")

if __name__ == "__main__":
    main()
