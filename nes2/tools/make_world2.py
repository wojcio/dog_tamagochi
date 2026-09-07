#!/usr/bin/env python3
"""
make_world2.py - Generates world2_data.c and world2_data.h with real BITMAP tile mappings.
"""

import sys

# Bitmap Tile IDs from make_chr2.py:
T_SKY = 0x00

# Clouds
T_CLD_TL = 0x01
T_CLD_TM = 0x02
T_CLD_TR = 0x03
T_CLD_BL = 0x04
T_CLD_BM = 0x05
T_CLD_BR = 0x06
T_CLD_C  = 0x07

# Sun
T_SUN_TL = 0x08
T_SUN_TR = 0x09
T_SUN_C  = 0x0A
T_SUN_BL = 0x0B
T_SUN_BR = 0x0C

# Buda
T_ROOF_L = 0x10
T_ROOF_C = 0x11
T_ROOF_R = 0x12
T_WOOD   = 0x13
T_DOOR_T = 0x14
T_DOOR_B = 0x15
T_BOWL   = 0x16
T_SIGN   = 0x17

# Park & Mostek
T_TREE_T = 0x20
T_TREE_C = 0x21
T_TREE_TR= 0x22
T_TREE_R = 0x23
T_FOUNT_B= 0x24
T_FOUNT_W= 0x25
T_BRIDGE = 0x26
T_PILLAR = 0x27
T_WATER_T= 0x28
T_WATER_B= 0x29

# Beach
T_UMB_L  = 0x30
T_UMB_R  = 0x31
T_UMB_P  = 0x32
T_LEZAK  = 0x33
T_SAND   = 0x34
T_SHELL  = 0x35
T_FOAM   = 0x36
T_CRAB_L = 0x37
T_CRAB_R = 0x38

# Agility
T_FLAG   = 0x40
T_HURDLE = 0x41
T_HPOST  = 0x42
T_HOOP_T = 0x43
T_HOOP_B = 0x44
T_TROPHY = 0x45

# Ground
T_GRASS  = 0x50
T_FLOWER = 0x51
T_DIRT   = 0x52
T_ROCK   = 0x53
T_PLAT   = 0x54

# HUD
T_HUD_TL = 0x70
T_HUD_H  = 0x71
T_HUD_TR = 0x72
T_HUD_V  = 0x73
T_HUD_BL = 0x74
T_HUD_BR = 0x75
T_HEART  = 0x76
T_LIGHT  = 0x77
T_BONE   = 0x78
T_BAR_L  = 0x79
T_BAR_F  = 0x7A
T_BAR_E  = 0x7B
T_BAR_R  = 0x7C

def text_to_tiles(txt):
    # FONT starts at 0x80 for sorted chars
    # We can match ASCII characters to font indices
    FONT_ORDER = " !&-0123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ[]"
    tiles = []
    for ch in txt:
        ch_upper = ch.upper()
        if ch_upper in FONT_ORDER:
            idx = 0x80 + FONT_ORDER.index(ch_upper)
            tiles.append(idx)
        else:
            tiles.append(0x80) # Space
    return tiles

def create_screen_matrix(screen_idx):
    # 30 rows x 32 cols
    matrix = [[T_SKY for _ in range(32)] for _ in range(30)]

    # 1. Top HUD (Rows 0-5)
    # Row 0: Frame Top
    matrix[0][0] = T_HUD_TL
    for c in range(1, 31): matrix[0][c] = T_HUD_H
    matrix[0][31] = T_HUD_TR

    # Row 1: Title
    titles = [
        " DOG TAMAGOTCHI 2D  [NES]     ",
        " [ PARK MIEJSKI & MOSTEK ]    ",
        " [ SLONECZNA PLAZA DLA PSOW ] ",
        " [ TOR PRZESZKOD AGILITY ]    "
    ]
    t_tiles = text_to_tiles(titles[screen_idx])
    matrix[1][0] = T_HUD_V
    for c in range(30): matrix[1][c + 1] = t_tiles[c]
    matrix[1][31] = T_HUD_V

    # Row 2: Status Line 1 (GLOD & ENER)
    line2 = text_to_tiles(" GLOD:        ENER:           ")
    matrix[2][0] = T_HUD_V
    for c in range(30): matrix[2][c + 1] = line2[c]
    matrix[2][31] = T_HUD_V
    # Heart icon + bar
    matrix[2][1] = T_HEART
    matrix[2][7] = T_BAR_L
    matrix[2][8] = T_BAR_F
    matrix[2][9] = T_BAR_F
    matrix[2][10] = T_BAR_F
    matrix[2][11] = T_BAR_F
    matrix[2][12] = T_BAR_E
    matrix[2][13] = T_BAR_R
    # Lightning icon + bar
    matrix[2][15] = T_LIGHT
    matrix[2][21] = T_BAR_L
    matrix[2][22] = T_BAR_F
    matrix[2][23] = T_BAR_F
    matrix[2][24] = T_BAR_F
    matrix[2][25] = T_BAR_F
    matrix[2][26] = T_BAR_E
    matrix[2][27] = T_BAR_R

    # Row 3: Status Line 2 (SZCZ & KOSC)
    line3 = text_to_tiles(" SZCZ:        KOSC:  03       ")
    matrix[3][0] = T_HUD_V
    for c in range(30): matrix[3][c + 1] = line3[c]
    matrix[3][31] = T_HUD_V
    matrix[3][7] = T_BAR_L
    matrix[3][8] = T_BAR_F
    matrix[3][9] = T_BAR_F
    matrix[3][10] = T_BAR_F
    matrix[3][11] = T_BAR_F
    matrix[3][12] = T_BAR_E
    matrix[3][13] = T_BAR_R
    matrix[3][25] = T_BONE

    # Row 4: Status Line 3 (STAN & POZ)
    line4 = text_to_tiles(" STAN: HAU!   POZ: 1 [CORGI]  ")
    matrix[4][0] = T_HUD_V
    for c in range(30): matrix[4][c + 1] = line4[c]
    matrix[4][31] = T_HUD_V

    # Row 5: Frame Bottom
    matrix[5][0] = T_HUD_BL
    for c in range(1, 31): matrix[5][c] = T_HUD_H
    matrix[5][31] = T_HUD_BR

    # 2. Scenery for Each Biome (Rows 6-21)
    if screen_idx == 0:
        # Screen 0: Ogrod & Buda
        # Sun at col 24-27, row 7-9
        matrix[7][24] = T_SUN_TL; matrix[7][25] = T_SUN_TR
        matrix[8][24] = T_SUN_BL; matrix[8][25] = T_SUN_BR
        matrix[8][23] = T_SUN_C

        # Clouds at col 16-19, row 8-9
        matrix[8][16] = T_CLD_TL; matrix[8][17] = T_CLD_TM; matrix[8][18] = T_CLD_TR
        matrix[9][16] = T_CLD_BL; matrix[9][17] = T_CLD_BM; matrix[9][18] = T_CLD_BR

        # Cloud 2 at col 4-7, row 10-11
        matrix[10][4] = T_CLD_TL; matrix[10][5] = T_CLD_TM; matrix[10][6] = T_CLD_TR
        matrix[11][4] = T_CLD_BL; matrix[11][5] = T_CLD_BM; matrix[11][6] = T_CLD_BR

        # Wooden Platform at row 14, col 8-15
        for c in range(8, 16): matrix[14][c] = T_PLAT

        # Buda at row 16-21, col 2-6
        # Roof
        matrix[16][2] = T_ROOF_L; matrix[16][3] = T_ROOF_C; matrix[16][4] = T_ROOF_R
        matrix[17][1] = T_ROOF_L; matrix[17][2] = T_WOOD; matrix[17][3] = T_WOOD; matrix[17][4] = T_WOOD; matrix[17][5] = T_ROOF_R
        # Walls & Door
        matrix[18][1] = T_WOOD; matrix[18][2] = T_DOOR_T; matrix[18][3] = T_DOOR_T; matrix[18][4] = T_WOOD; matrix[18][5] = T_WOOD
        matrix[19][1] = T_WOOD; matrix[19][2] = T_DOOR_B; matrix[19][3] = T_DOOR_B; matrix[19][4] = T_SIGN;   matrix[19][5] = T_WOOD
        matrix[20][1] = T_WOOD; matrix[20][2] = T_DOOR_B; matrix[20][3] = T_DOOR_B; matrix[20][4] = T_WOOD;   matrix[20][5] = T_WOOD
        matrix[21][1] = T_WOOD; matrix[21][2] = T_DOOR_B; matrix[21][3] = T_DOOR_B; matrix[21][4] = T_WOOD;   matrix[21][5] = T_WOOD
        matrix[21][7] = T_BOWL

        # Tree at col 20-22, row 13-21
        matrix[13][20] = T_TREE_T; matrix[13][21] = T_TREE_T
        matrix[14][19] = T_TREE_T; matrix[14][20] = T_TREE_C; matrix[14][21] = T_TREE_C; matrix[14][22] = T_TREE_T
        matrix[15][19] = T_TREE_C; matrix[15][20] = T_TREE_C; matrix[15][21] = T_TREE_C; matrix[15][22] = T_TREE_C
        for r in range(16, 21): matrix[r][20] = T_TREE_TR; matrix[r][21] = T_TREE_TR
        matrix[21][19] = T_TREE_R; matrix[21][20] = T_TREE_TR; matrix[21][21] = T_TREE_TR; matrix[21][22] = T_TREE_R

    elif screen_idx == 1:
        # Screen 1: Park Miejski & Drewniany Mostek
        # Clouds
        matrix[8][5] = T_CLD_TL; matrix[8][6] = T_CLD_TM; matrix[8][7] = T_CLD_TR
        matrix[9][5] = T_CLD_BL; matrix[9][6] = T_CLD_BM; matrix[9][7] = T_CLD_BR
        matrix[7][22] = T_CLD_TL; matrix[7][23] = T_CLD_TM; matrix[7][24] = T_CLD_TR
        matrix[8][22] = T_CLD_BL; matrix[8][23] = T_CLD_BM; matrix[8][24] = T_CLD_BR

        # Fountain at col 4-7, row 16-21
        matrix[16][5] = T_FOUNT_W; matrix[16][6] = T_FOUNT_W
        matrix[17][5] = T_FOUNT_W; matrix[17][6] = T_FOUNT_W
        matrix[18][4] = T_FOUNT_B; matrix[18][5] = T_FOUNT_B; matrix[18][6] = T_FOUNT_B; matrix[18][7] = T_FOUNT_B

        # Wooden Bridge at row 14, col 14-29
        for c in range(14, 30): matrix[14][c] = T_BRIDGE
        # Bridge Pillars
        for r in range(15, 22):
            matrix[r][15] = T_PILLAR
            matrix[r][22] = T_PILLAR
            matrix[r][28] = T_PILLAR

        # River Water flowing under the bridge (rows 18-21, col 14-31)
        for r in range(18, 22):
            for c in range(14, 32):
                matrix[r][c] = T_WATER_T if r == 18 else T_WATER_B

    elif screen_idx == 2:
        # Screen 2: Sloneczna Plaza
        # Big Shining Sun
        matrix[7][4] = T_SUN_TL; matrix[7][5] = T_SUN_TR
        matrix[8][3] = T_SUN_C;  matrix[8][4] = T_SUN_BL; matrix[8][5] = T_SUN_BR

        # Clouds
        matrix[8][20] = T_CLD_TL; matrix[8][21] = T_CLD_TM; matrix[8][22] = T_CLD_TR
        matrix[9][20] = T_CLD_BL; matrix[9][21] = T_CLD_BM; matrix[9][22] = T_CLD_BR

        # Beach Umbrella 1 at col 8-11, row 14-21
        matrix[14][8] = T_UMB_L; matrix[14][9] = T_UMB_R
        matrix[15][7] = T_UMB_L; matrix[15][8] = T_UMB_L; matrix[15][9] = T_UMB_R; matrix[15][10] = T_UMB_R
        for r in range(16, 22): matrix[r][8] = T_UMB_P

        # Beach Lounger (Leżak) at col 10-12, row 19-21
        matrix[19][11] = T_LEZAK; matrix[19][12] = T_LEZAK

        # Beach Umbrella 2 at col 20-23
        matrix[14][21] = T_UMB_L; matrix[14][22] = T_UMB_R
        matrix[15][20] = T_UMB_L; matrix[15][21] = T_UMB_L; matrix[15][22] = T_UMB_R; matrix[15][23] = T_UMB_R
        for r in range(16, 22): matrix[r][21] = T_UMB_P
        matrix[19][23] = T_LEZAK; matrix[19][24] = T_LEZAK

        # Little Red Crab at row 21, col 16-17
        matrix[21][16] = T_CRAB_L; matrix[21][17] = T_CRAB_R

    elif screen_idx == 3:
        # Screen 3: Tor Przeszkod Agility & Meta
        # Start Banner at col 2-5, row 15-21
        matrix[15][2] = T_FLAG; matrix[15][3] = T_FLAG
        for r in range(16, 22): matrix[r][2] = T_HPOST

        # Hurdle 1 at col 8-11, row 17-21
        matrix[17][8] = T_HURDLE; matrix[17][9] = T_HURDLE; matrix[17][10] = T_HURDLE
        matrix[18][8] = T_HPOST;  matrix[18][10] = T_HPOST

        # Agility Hoop at col 14-16, row 15-21
        matrix[15][14] = T_HOOP_T; matrix[15][15] = T_HOOP_T
        matrix[16][14] = T_HOOP_B; matrix[16][15] = T_HOOP_B
        matrix[17][14] = T_HOOP_B; matrix[17][15] = T_HOOP_B
        for r in range(18, 22): matrix[r][14] = T_HPOST

        # Hurdle 2 at col 19-22, row 15-21
        for c in range(19, 23): matrix[15][c] = T_PLAT

        # Trophy & Finish Banner at col 25-28, row 16-21
        matrix[16][26] = T_TROPHY; matrix[16][27] = T_TROPHY
        matrix[17][25] = T_HPOST;  matrix[17][28] = T_HPOST
        for r in range(18, 22):
            matrix[r][25] = T_HPOST
            matrix[r][28] = T_HPOST

    # 3. Ground (Rows 22-29)
    if screen_idx in [0, 1]:
        # Grass with occasional flowers
        for c in range(32):
            matrix[22][c] = T_FLOWER if (c % 5 == 2) else T_GRASS
            matrix[23][c] = T_DIRT
            for r in range(24, 28): matrix[r][c] = T_DIRT
            for r in range(28, 30): matrix[r][c] = T_ROCK
    elif screen_idx == 2:
        # Golden Beach Sand & Shoreline foam
        for c in range(32):
            matrix[22][c] = T_FOAM if (c >= 20) else (T_SHELL if c % 7 == 3 else T_SAND)
            for r in range(23, 30): matrix[r][c] = T_SAND
    else:
        # Agility Track Ground
        for c in range(32):
            matrix[22][c] = T_GRASS if (c % 2 == 0) else T_FLOWER
            for r in range(23, 30): matrix[r][c] = T_DIRT

    return matrix

def main():
    screens = [create_screen_matrix(i) for i in range(4)]

    # Generate world2_data.h
    with open("world2_data.h", "w") as f:
        f.write("#ifndef _WORLD2_DATA_H\n")
        f.write("#define _WORLD2_DATA_H\n\n")
        f.write("extern const unsigned char screen0_data[1024];\n")
        f.write("extern const unsigned char screen1_data[1024];\n")
        f.write("extern const unsigned char world_cols_bitmap[128 * 30];\n\n")
        f.write("#endif\n")

    # Generate world2_data.c
    with open("world2_data.c", "w") as f:
        f.write('#include "world2_data.h"\n\n')

        # Screen 0 (Nametable 0: 960 bytes + 64 attributes = 1024 bytes)
        f.write("const unsigned char screen0_data[1024] = {\n")
        s0_bytes = []
        for r in range(30):
            for c in range(32):
                s0_bytes.append(screens[0][r][c])
        # Attributes: rows 0-19 Palette 0, rows 20-29 Palette 1
        attr0 = [0x00] * 40 + [0x55] * 24
        s0_bytes.extend(attr0)
        for i in range(0, len(s0_bytes), 16):
            chunk = s0_bytes[i:i+16]
            f.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
        f.write("};\n\n")

        # Screen 1 (Nametable 1: 1024 bytes)
        f.write("const unsigned char screen1_data[1024] = {\n")
        s1_bytes = []
        for r in range(30):
            for c in range(32):
                s1_bytes.append(screens[1][r][c])
        attr1 = [0x00] * 40 + [0x55] * 24
        s1_bytes.extend(attr1)
        for i in range(0, len(s1_bytes), 16):
            chunk = s1_bytes[i:i+16]
            f.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
        f.write("};\n\n")

        # Column-major world: 128 cols x 30 rows = 3840 bytes
        f.write("const unsigned char world_cols_bitmap[128 * 30] = {\n")
        cols_data = []
        for col_idx in range(128):
            s_idx = col_idx // 32
            sub_col = col_idx % 32
            for r_idx in range(30):
                cols_data.append(screens[s_idx][r_idx][sub_col])

        for i in range(0, len(cols_data), 16):
            chunk = cols_data[i:i+16]
            f.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
        f.write("};\n")

    print("Generated world2_data.h and world2_data.c successfully.")

if __name__ == "__main__":
    main()
