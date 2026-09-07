#!/usr/bin/env python3
"""
make_world2.py - Generates world2_data.c and world2_data.h with authentic Super Mario Bros style layouts.
"""

import sys

T_SKY      = 0x00
T_CLD_TL   = 0x01
T_CLD_TM   = 0x02
T_CLD_TR   = 0x03
T_CLD_BL   = 0x04
T_CLD_BM   = 0x05
T_CLD_BR   = 0x06
T_CLD_C    = 0x07

T_SUN_TL   = 0x08
T_SUN_TR   = 0x09
T_SUN_C    = 0x0A
T_SUN_BL   = 0x0B
T_SUN_BR   = 0x0C

# Trunk (Pal 2)
T_TRUNK_L  = 0x34
T_TRUNK_R  = 0x35
T_ROOT_L   = 0x36
T_ROOT_R   = 0x37

# Bridge & Scenery
T_BRIDGE   = 0x38
T_PILLAR   = 0x39
T_FOUNT_B  = 0x3A
T_FOUNT_W  = 0x3B
T_WATER    = 0x3C
T_UMB_L    = 0x3D
T_UMB_R    = 0x3E
T_UMB_P    = 0x3F
T_LEZAK    = 0x3E

# Agility
T_FLAG     = 0x40
T_HURDLE   = 0x41
T_HPOST    = 0x42
T_HOOP_T   = 0x43
T_HOOP_B   = 0x44
T_TROPHY   = 0x45

# Ground
T_GRASS    = 0x50
T_FLOWER   = 0x51
T_DIRT     = 0x52
T_DIRT_D   = 0x53
T_PLAT     = 0x54
T_BOWL     = 0x55

# HUD
T_HUD_TL   = 0x70
T_HUD_H    = 0x71
T_HUD_TR   = 0x72
T_HUD_V    = 0x73
T_HUD_BL   = 0x74
T_HUD_BR   = 0x75
T_HEART    = 0x76
T_LIGHT    = 0x77
T_BONE     = 0x78
T_BAR_L    = 0x79
T_BAR_F    = 0x7A
T_BAR_E    = 0x7B
T_BAR_R    = 0x7C

def text_to_tiles(txt):
    FONT_ORDER = " !&-0123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ[]"
    tiles = []
    for ch in txt:
        ch_upper = ch.upper()
        if ch_upper in FONT_ORDER:
            tiles.append(0x80 + FONT_ORDER.index(ch_upper))
        else:
            tiles.append(0x80)
    return tiles

def place_tree(tiles, pals, top_row, left_col, trunk_height=6):
    """Places a 5x4 SMB canopy (tiles 0x20..0x33, Pal 1) with 2-tile trunk (Pal 2)."""
    # 5 cols x 4 rows
    for r in range(4):
        for c in range(5):
            t_id = 0x20 + r * 5 + c
            rr = top_row + r
            cc = left_col + c
            if 0 <= rr < 30 and 0 <= cc < 32:
                tiles[rr][cc] = t_id
                pals[rr][cc] = 1 # Nature Green

    # Trunk at left_col + 2 and left_col + 3
    trunk_start = top_row + 4
    trunk_end = trunk_start + trunk_height - 1
    for r in range(trunk_start, trunk_end):
        if 0 <= r < 30:
            if left_col + 2 < 32:
                tiles[r][left_col + 2] = T_TRUNK_L
                pals[r][left_col + 2] = 2
            if left_col + 3 < 32:
                tiles[r][left_col + 3] = T_TRUNK_R
                pals[r][left_col + 3] = 2

    # Root base
    if 0 <= trunk_end < 30:
        if left_col + 2 < 32:
            tiles[trunk_end][left_col + 2] = T_ROOT_L
            pals[trunk_end][left_col + 2] = 2
        if left_col + 3 < 32:
            tiles[trunk_end][left_col + 3] = T_ROOT_R
            pals[trunk_end][left_col + 3] = 2

def place_buda(tiles, pals, top_row, left_col):
    """Places a 4x4 SMB doghouse (tiles 0x10..0x1F): Roof Pal 3, Walls Pal 2."""
    for r in range(4):
        for c in range(4):
            t_id = 0x10 + r * 4 + c
            rr = top_row + r
            cc = left_col + c
            if 0 <= rr < 30 and 0 <= cc < 32:
                tiles[rr][cc] = t_id
                pals[rr][cc] = 3 if r < 2 else 2 # Roof Red, Walls Wood

    # Bowl
    if left_col + 4 < 32:
        tiles[top_row + 3][left_col + 4] = T_BOWL
        pals[top_row + 3][left_col + 4] = 2

def create_screen_matrix(screen_idx):
    matrix = [[T_SKY for _ in range(32)] for _ in range(30)]
    pals   = [[0 for _ in range(32)] for _ in range(30)]

    # 1. Top HUD (Rows 0-5)
    matrix[0][0] = T_HUD_TL
    for c in range(1, 31): matrix[0][c] = T_HUD_H
    matrix[0][31] = T_HUD_TR

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

    line2 = text_to_tiles(" GLOD:        ENER:           ")
    matrix[2][0] = T_HUD_V
    for c in range(30): matrix[2][c + 1] = line2[c]
    matrix[2][31] = T_HUD_V
    matrix[2][1] = T_HEART
    matrix[2][7] = T_BAR_L; matrix[2][8] = T_BAR_F; matrix[2][9] = T_BAR_F; matrix[2][10] = T_BAR_F; matrix[2][11] = T_BAR_F; matrix[2][12] = T_BAR_E; matrix[2][13] = T_BAR_R
    matrix[2][15] = T_LIGHT
    matrix[2][21] = T_BAR_L; matrix[2][22] = T_BAR_F; matrix[2][23] = T_BAR_F; matrix[2][24] = T_BAR_F; matrix[2][25] = T_BAR_F; matrix[2][26] = T_BAR_E; matrix[2][27] = T_BAR_R

    line3 = text_to_tiles(" SZCZ:        KOSC:  03       ")
    matrix[3][0] = T_HUD_V
    for c in range(30): matrix[3][c + 1] = line3[c]
    matrix[3][31] = T_HUD_V
    matrix[3][7] = T_BAR_L; matrix[3][8] = T_BAR_F; matrix[3][9] = T_BAR_F; matrix[3][10] = T_BAR_F; matrix[3][11] = T_BAR_F; matrix[3][12] = T_BAR_E; matrix[3][13] = T_BAR_R
    matrix[3][27] = T_BONE

    line4 = text_to_tiles(" STAN: HAU!   POZ: 1 [CORGI]  ")
    matrix[4][0] = T_HUD_V
    for c in range(30): matrix[4][c + 1] = line4[c]
    matrix[4][31] = T_HUD_V

    matrix[5][0] = T_HUD_BL
    for c in range(1, 31): matrix[5][c] = T_HUD_H
    matrix[5][31] = T_HUD_BR

    # 2. Scenery
    if screen_idx == 0:
        # Sun at col 24-25, row 7-8
        matrix[7][24] = T_SUN_TL; matrix[7][25] = T_SUN_TR
        matrix[8][24] = T_SUN_BL; matrix[8][25] = T_SUN_BR
        matrix[8][23] = T_SUN_C

        # Clouds
        matrix[8][15] = T_CLD_TL; matrix[8][16] = T_CLD_TM; matrix[8][17] = T_CLD_TR
        matrix[9][15] = T_CLD_BL; matrix[9][16] = T_CLD_BM; matrix[9][17] = T_CLD_BR
        matrix[10][4] = T_CLD_TL; matrix[10][5] = T_CLD_TM; matrix[10][6] = T_CLD_TR
        matrix[11][4] = T_CLD_BL; matrix[11][5] = T_CLD_BM; matrix[11][6] = T_CLD_BR

        # Jump Platform
        for c in range(8, 15):
            matrix[15][c] = T_PLAT
            pals[15][c] = 2

        # Buda at col 2..5, row 18..21
        place_buda(matrix, pals, top_row=18, left_col=2)

        # Tree at col 19..23, row 14..21 (Canopy 14..17, Trunk 18..21)
        place_tree(matrix, pals, top_row=14, left_col=19, trunk_height=4)

    elif screen_idx == 1:
        matrix[7][6] = T_CLD_TL; matrix[7][7] = T_CLD_TM; matrix[7][8] = T_CLD_TR
        matrix[8][6] = T_CLD_BL; matrix[8][7] = T_CLD_BM; matrix[8][8] = T_CLD_BR
        matrix[8][22] = T_CLD_TL; matrix[8][23] = T_CLD_TM; matrix[8][24] = T_CLD_TR
        matrix[9][22] = T_CLD_BL; matrix[9][23] = T_CLD_BM; matrix[9][24] = T_CLD_BR

        # Tree at col 2..6, row 14..21 (Canopy 14..17, Trunk 18..21)
        place_tree(matrix, pals, top_row=14, left_col=2, trunk_height=4)

        # Fountain
        matrix[17][9] = T_FOUNT_W; matrix[17][10] = T_FOUNT_W; pals[17][9] = 3; pals[17][10] = 3
        matrix[18][9] = T_FOUNT_W; matrix[18][10] = T_FOUNT_W; pals[18][9] = 3; pals[18][10] = 3
        for c in range(8, 12):
            matrix[19][c] = T_FOUNT_B; pals[19][c] = 3
            matrix[20][c] = T_FOUNT_B; pals[20][c] = 3
            matrix[21][c] = T_FOUNT_B; pals[21][c] = 3

        # Bridge
        for c in range(15, 29):
            matrix[15][c] = T_BRIDGE; pals[15][c] = 2
        for r in range(16, 22):
            matrix[r][17] = T_PILLAR; pals[r][17] = 2
            matrix[r][25] = T_PILLAR; pals[r][25] = 2

    elif screen_idx == 2:
        matrix[7][12] = T_SUN_TL; matrix[7][13] = T_SUN_TR
        matrix[8][12] = T_SUN_BL; matrix[8][13] = T_SUN_BR
        matrix[8][11] = T_SUN_C

        matrix[8][4] = T_CLD_TL; matrix[8][5] = T_CLD_TM; matrix[8][6] = T_CLD_TR
        matrix[9][4] = T_CLD_BL; matrix[9][5] = T_CLD_BM; matrix[9][6] = T_CLD_BR
        matrix[8][22] = T_CLD_TL; matrix[8][23] = T_CLD_TM; matrix[8][24] = T_CLD_TR
        matrix[9][22] = T_CLD_BL; matrix[9][23] = T_CLD_BM; matrix[9][24] = T_CLD_BR

        # Umbrellas
        matrix[15][6] = T_UMB_L; matrix[15][7] = T_UMB_R; pals[15][6] = 3; pals[15][7] = 3
        for r in range(16, 22): matrix[r][6] = T_UMB_P; pals[r][6] = 3
        matrix[20][8] = T_LEZAK; pals[20][8] = 3

        matrix[15][18] = T_UMB_L; matrix[15][19] = T_UMB_R; pals[15][18] = 3; pals[15][19] = 3
        for r in range(16, 22): matrix[r][18] = T_UMB_P; pals[r][18] = 3
        matrix[20][20] = T_LEZAK; pals[20][20] = 3

    elif screen_idx == 3:
        matrix[8][8] = T_CLD_TL; matrix[8][9] = T_CLD_TM; matrix[8][10] = T_CLD_TR
        matrix[9][8] = T_CLD_BL; matrix[9][9] = T_CLD_BM; matrix[9][10] = T_CLD_BR

        # Tree at col 25..29, row 14..21 (Canopy 14..17, Trunk 18..21)
        place_tree(matrix, pals, top_row=14, left_col=25, trunk_height=4)

        # Flags & Hurdles
        matrix[15][2] = T_FLAG; pals[15][2] = 3
        for r in range(16, 22): matrix[r][2] = T_HPOST; pals[r][2] = 3

        for c in range(7, 11): matrix[18][c] = T_HURDLE; pals[18][c] = 1
        matrix[19][7] = T_HPOST; matrix[19][10] = T_HPOST
        matrix[20][7] = T_HPOST; matrix[20][10] = T_HPOST
        matrix[21][7] = T_HPOST; matrix[21][10] = T_HPOST

        matrix[16][14] = T_HOOP_T; matrix[17][14] = T_HOOP_B
        matrix[18][14] = T_HOOP_T; matrix[19][14] = T_HOOP_B
        matrix[20][14] = T_HPOST;   matrix[21][14] = T_HPOST
        pals[16][14] = 3; pals[17][14] = 3; pals[18][14] = 3; pals[19][14] = 3

        for c in range(17, 22): matrix[15][c] = T_PLAT; pals[15][c] = 2

        matrix[17][23] = T_TROPHY; matrix[17][24] = T_TROPHY; pals[17][23] = 3; pals[17][24] = 3
        for r in range(18, 22):
            matrix[r][22] = T_HPOST; matrix[r][25] = T_HPOST
            pals[r][22] = 1; pals[r][25] = 1

    # 3. Ground
    if screen_idx == 2:
        for c in range(32):
            if c >= 20:
                matrix[22][c] = T_WATER; pals[22][c] = 3
            else:
                matrix[22][c] = T_DIRT; pals[22][c] = 2
            for r in range(23, 30):
                matrix[r][c] = T_DIRT; pals[r][c] = 2
    else:
        for c in range(32):
            matrix[22][c] = T_GRASS if (c % 4 != 2) else T_FLOWER
            pals[22][c] = 1
            for r in range(23, 30):
                matrix[r][c] = T_DIRT if r < 28 else T_DIRT_D
                pals[r][c] = 2

    # 4. Attribute table calculation
    attr_table = []
    for by in range(8):
        for bx in range(8):
            def get_quad_pal(r_start, c_start):
                votes = {}
                for dr in range(2):
                    for dc in range(2):
                        r = r_start + dr
                        c = c_start + dc
                        if r < 30 and c < 32:
                            p = pals[r][c]
                            if p != 0: # Ignore sky
                                votes[p] = votes.get(p, 0) + 1
                if not votes: return 0
                return max(votes.items(), key=lambda x: x[1])[0]

            r0 = by * 4
            c0 = bx * 4
            p_tl = get_quad_pal(r0, c0)
            p_tr = get_quad_pal(r0, c0 + 2)
            p_bl = get_quad_pal(r0 + 2, c0)
            p_br = get_quad_pal(r0 + 2, c0 + 2)

            attr_byte = (p_tl & 3) | ((p_tr & 3) << 2) | ((p_bl & 3) << 4) | ((p_br & 3) << 6)
            attr_table.append(attr_byte)

    return matrix, attr_table

def main():
    screens_data = [create_screen_matrix(i) for i in range(4)]
    screens_tiles = [s[0] for s in screens_data]
    screens_attrs = [s[1] for s in screens_data]

    with open("world2_data.h", "w") as f:
        f.write("#ifndef _WORLD2_DATA_H\n")
        f.write("#define _WORLD2_DATA_H\n\n")
        f.write("extern const unsigned char screen0_data[1024];\n")
        f.write("extern const unsigned char screen1_data[1024];\n")
        f.write("extern const unsigned char world_cols_bitmap[128 * 30];\n\n")
        f.write("#endif\n")

    with open("world2_data.c", "w") as f:
        f.write('#include "world2_data.h"\n\n')

        # Screen 0
        f.write("const unsigned char screen0_data[1024] = {\n")
        s0_bytes = []
        for r in range(30):
            for c in range(32):
                s0_bytes.append(screens_tiles[0][r][c])
        s0_bytes.extend(screens_attrs[0])
        for i in range(0, len(s0_bytes), 16):
            chunk = s0_bytes[i:i+16]
            f.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
        f.write("};\n\n")

        # Screen 1
        f.write("const unsigned char screen1_data[1024] = {\n")
        s1_bytes = []
        for r in range(30):
            for c in range(32):
                s1_bytes.append(screens_tiles[1][r][c])
        s1_bytes.extend(screens_attrs[1])
        for i in range(0, len(s1_bytes), 16):
            chunk = s1_bytes[i:i+16]
            f.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
        f.write("};\n\n")

        # World matrix
        f.write("const unsigned char world_cols_bitmap[128 * 30] = {\n")
        cols_data = []
        for col_idx in range(128):
            s_idx = col_idx // 32
            sub_col = col_idx % 32
            for r_idx in range(30):
                cols_data.append(screens_tiles[s_idx][r_idx][sub_col])

        for i in range(0, len(cols_data), 16):
            chunk = cols_data[i:i+16]
            f.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
        f.write("};\n\n")

        # World attribute columns (32 cols x 8 rows = 256 bytes)
        f.write("const unsigned char world_attr_cols[256] = {\n")
        attr_cols_data = []
        for gac in range(32):
            s_idx = gac // 8
            c_idx = gac % 8
            for r in range(8):
                attr_cols_data.append(screens_attrs[s_idx][r * 8 + c_idx])

        for i in range(0, len(attr_cols_data), 16):
            chunk = attr_cols_data[i:i+16]
            f.write("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",\n")
        f.write("};\n")

    with open("world2_data.h", "w") as f:
        f.write("#ifndef _WORLD2_DATA_H\n")
        f.write("#define _WORLD2_DATA_H\n\n")
        f.write("extern const unsigned char screen0_data[1024];\n")
        f.write("extern const unsigned char screen1_data[1024];\n")
        f.write("extern const unsigned char world_cols_bitmap[128 * 30];\n")
        f.write("extern const unsigned char world_attr_cols[256];\n\n")
        f.write("#endif\n")

    print("Generated world2_data.h and world2_data.c successfully.")

if __name__ == "__main__":
    main()
