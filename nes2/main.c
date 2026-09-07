// ==============================================================================
// 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES2 (C EDITION)
// Written in C for MOS 6502 using neslib, nesdoug, and custom BITMAP pixel art.
// ==============================================================================

#include "neslib.h"
#include "nesdoug.h"
#include "world2_data.h"

// ------------------------------------------------------------------------------
// CONSTANTS & DEFINITIONS
// ------------------------------------------------------------------------------
#define GROUND_Y         152
#define JUMP_VELOCITY    -6
#define GRAVITY          1
#define MAX_FALL_SPEED   5
#define RUN_SPEED        2

#define MODE_PLAY        0
#define MODE_SLEEP       1

#define SFX_BARK         1
#define SFX_JUMP         2
#define SFX_EAT          3

#define T_BAR_L          0x79
#define T_BAR_F          0x7A
#define T_BAR_E          0x7B
#define T_BAR_R          0x7C

// ------------------------------------------------------------------------------
// PALETTES
// ------------------------------------------------------------------------------
const unsigned char bg_palette[16] = {
    0x21, // Backdrop: Sky Blue
    0x0F, 0x30, 0x12, // Pal 0 (Sky & HUD): Black, White, Soft Blue
    0x0F, 0x1A, 0x29, // Pal 1 (Nature): Dark Forest Green, Lush Green, Brown
    0x0F, 0x16, 0x27, // Pal 2 (Buda & Beach): Red, Orange/Tan, Sand Yellow
    0x0F, 0x02, 0x11  // Pal 3 (Water & Mostek): Dark Blue, Azure, White
};

const unsigned char spr_palette[16] = {
    0x21,
    0x0F, 0x27, 0x30, // Pal 0: Corgi Dog (Black outline, Golden fur, White paws)
    0x0F, 0x30, 0x16, // Pal 1: Effects (White, Light Blue, Red)
    0x0F, 0x16, 0x37, // Pal 2: Items (Red Ball, Golden Bone, White)
    0x0F, 0x16, 0x28  // Pal 3: Crab (Red, Sand, White)
};

// ------------------------------------------------------------------------------
// CORGI METASPRITE DEFINITIONS (24x24 px = 3x3 tiles, dx, dy, tile, attr)
// ------------------------------------------------------------------------------
const unsigned char metaspr_idle_right[] = {
    0, 0, 0x00, 0,   8, 0, 0x01, 0,   16, 0, 0x02, 0,
    0, 8, 0x03, 0,   8, 8, 0x04, 0,   16, 8, 0x05, 0,
    0, 16, 0x06, 0,  8, 16, 0x07, 0,  16, 16, 0x08, 0,
    128
};

const unsigned char metaspr_idle_left[] = {
    16, 0, 0x00, OAM_FLIP_H,   8, 0, 0x01, OAM_FLIP_H,   0, 0, 0x02, OAM_FLIP_H,
    16, 8, 0x03, OAM_FLIP_H,   8, 8, 0x04, OAM_FLIP_H,   0, 8, 0x05, OAM_FLIP_H,
    16, 16, 0x06, OAM_FLIP_H,  8, 16, 0x07, OAM_FLIP_H,  0, 16, 0x08, OAM_FLIP_H,
    128
};

const unsigned char metaspr_walk1_right[] = {
    0, 0, 0x09, 0,   8, 0, 0x0A, 0,   16, 0, 0x0B, 0,
    0, 8, 0x0C, 0,   8, 8, 0x0D, 0,   16, 8, 0x0E, 0,
    0, 16, 0x0F, 0,  8, 16, 0x10, 0,  16, 16, 0x11, 0,
    128
};

const unsigned char metaspr_walk1_left[] = {
    16, 0, 0x09, OAM_FLIP_H,   8, 0, 0x0A, OAM_FLIP_H,   0, 0, 0x0B, OAM_FLIP_H,
    16, 8, 0x0C, OAM_FLIP_H,   8, 8, 0x0D, OAM_FLIP_H,   0, 8, 0x0E, OAM_FLIP_H,
    16, 16, 0x0F, OAM_FLIP_H,  8, 16, 0x10, OAM_FLIP_H,  0, 16, 0x11, OAM_FLIP_H,
    128
};

const unsigned char metaspr_walk2_right[] = {
    0, 0, 0x12, 0,   8, 0, 0x13, 0,   16, 0, 0x14, 0,
    0, 8, 0x15, 0,   8, 8, 0x16, 0,   16, 8, 0x17, 0,
    0, 16, 0x18, 0,  8, 16, 0x19, 0,  16, 16, 0x1A, 0,
    128
};

const unsigned char metaspr_walk2_left[] = {
    16, 0, 0x12, OAM_FLIP_H,   8, 0, 0x13, OAM_FLIP_H,   0, 0, 0x14, OAM_FLIP_H,
    16, 8, 0x15, OAM_FLIP_H,   8, 8, 0x16, OAM_FLIP_H,   0, 8, 0x17, OAM_FLIP_H,
    16, 16, 0x18, OAM_FLIP_H,  8, 16, 0x19, OAM_FLIP_H,  0, 16, 0x1A, OAM_FLIP_H,
    128
};

const unsigned char metaspr_jump_right[] = {
    0, 0, 0x1B, 0,   8, 0, 0x1C, 0,   16, 0, 0x1D, 0,
    0, 8, 0x1E, 0,   8, 8, 0x1F, 0,   16, 8, 0x20, 0,
    0, 16, 0x21, 0,  8, 16, 0x22, 0,  16, 16, 0x23, 0,
    128
};

const unsigned char metaspr_jump_left[] = {
    16, 0, 0x1B, OAM_FLIP_H,   8, 0, 0x1C, OAM_FLIP_H,   0, 0, 0x1D, OAM_FLIP_H,
    16, 8, 0x1E, OAM_FLIP_H,   8, 8, 0x1F, OAM_FLIP_H,   0, 8, 0x20, OAM_FLIP_H,
    16, 16, 0x21, OAM_FLIP_H,  8, 16, 0x22, OAM_FLIP_H,  0, 16, 0x23, OAM_FLIP_H,
    128
};

const unsigned char metaspr_sleep[] = {
    0, 0, 0x24, 0,   8, 0, 0x25, 0,   16, 0, 0x26, 0,
    0, 8, 0x27, 0,   8, 8, 0x28, 0,   16, 8, 0x29, 0,
    128
};

const unsigned char metaspr_hau[] = {
    0, 0, 0x32, 1,   8, 0, 0x33, 1,
    0, 8, 0x34, 1,   8, 8, 0x35, 1,
    128
};

// ------------------------------------------------------------------------------
// GAME STATE VARIABLES
// ------------------------------------------------------------------------------
int dog_x = 32;
int dog_y = GROUND_Y;
signed char dog_vy = 0;
unsigned char dog_dir = 0; // 0 = right, 1 = left
unsigned char dog_on_ground = 1;
unsigned char dog_anim_timer = 0;
unsigned char dog_anim_frame = 0;
unsigned char bark_timer = 0;
unsigned char game_mode = MODE_PLAY;

// Camera & Scrolling
unsigned int cam_x = 0;
unsigned char cam_col = 0;
unsigned char cam_prev_col = 0;

// Tamagotchi Needs (0..100)
unsigned char stat_hunger = 80;
unsigned char stat_energy = 80;
unsigned char stat_happy  = 80;
unsigned char stat_bones  = 3;
unsigned char need_timer  = 0;

// Items (16-bit X)
int item1_x = 180; int item1_y = 100; unsigned char item1_active = 1;
int item2_x = 420; int item2_y = 100; unsigned char item2_active = 1;
int ball_x  = 300; int ball_y  = GROUND_Y + 8; signed char ball_vx = 0;

// ------------------------------------------------------------------------------
// PLATFORM COLLISION DETECTION ACROSS 4 BIOMES
// ------------------------------------------------------------------------------
void check_collision_platforms(void) {
    if (dog_y >= GROUND_Y) {
        dog_y = GROUND_Y;
        dog_vy = 0;
        dog_on_ground = 1;
        return;
    }

    if (dog_vy < 0) {
        dog_on_ground = 0;
        return;
    }

    // Biome 0: Platform at x=64..128, y=104
    if (dog_x >= 64 && dog_x <= 128 && dog_y >= 104 && dog_y <= 110) {
        dog_y = 104;
        dog_vy = 0;
        dog_on_ground = 1;
        return;
    }

    // Biome 1: Bridge Platform at x=368..480, y=104
    if (dog_x >= 368 && dog_x <= 480 && dog_y >= 104 && dog_y <= 110) {
        dog_y = 104;
        dog_vy = 0;
        dog_on_ground = 1;
        return;
    }

    // Biome 2: Leżak / Platform at x=576..656, y=104
    if (dog_x >= 576 && dog_x <= 656 && dog_y >= 104 && dog_y <= 110) {
        dog_y = 104;
        dog_vy = 0;
        dog_on_ground = 1;
        return;
    }

    // Biome 3: Agility Hurdles at x=840..920, y=104
    if (dog_x >= 840 && dog_x <= 920 && dog_y >= 104 && dog_y <= 110) {
        dog_y = 104;
        dog_vy = 0;
        dog_on_ground = 1;
        return;
    }

    dog_on_ground = 0;
}

// ------------------------------------------------------------------------------
// COLUMN STREAMING FOR HORIZONTAL SCROLLING
// ------------------------------------------------------------------------------
void stream_column(unsigned char col_id) {
    queue_col_stream(col_id);
}

// ------------------------------------------------------------------------------
// UPDATE HUD METERS IN VRAM BUFFER
// ------------------------------------------------------------------------------
void update_hud_meter(unsigned char val, unsigned int nt_addr) {
    static unsigned char bar[6];
    unsigned char fill = val / 20; // 0..5
    unsigned char i;
    for (i = 0; i < 5; ++i) {
        bar[i] = (i < fill) ? T_BAR_F : T_BAR_E;
    }
    bar[5] = T_BAR_R;
    multi_vram_buffer_horz((const char*)bar, 6, nt_addr);
}

void update_hud(void) {
    // NT0 ($2000)
    update_hud_meter(stat_hunger, 0x2048);
    update_hud_meter(stat_energy, 0x2056);
    update_hud_meter(stat_happy,  0x2068);

    // NT1 ($2400)
    update_hud_meter(stat_hunger, 0x2448);
    update_hud_meter(stat_energy, 0x2456);
    update_hud_meter(stat_happy,  0x2468);
}

void init_game(void) {
    dog_x = 32;
    dog_y = GROUND_Y;
    dog_vy = 0;
    dog_dir = 0;
    dog_on_ground = 1;
    dog_anim_timer = 0;
    dog_anim_frame = 0;
    bark_timer = 0;
    game_mode = MODE_PLAY;

    cam_x = 0;
    cam_col = 0;
    cam_prev_col = 0;

    stat_hunger = 80;
    stat_energy = 80;
    stat_happy  = 80;
    stat_bones  = 3;
    need_timer  = 0;

    item1_x = 180; item1_y = 100; item1_active = 1;
    item2_x = 420; item2_y = 100; item2_active = 1;
    ball_x  = 300; ball_y  = GROUND_Y + 8; ball_vx = 0;
}

// ------------------------------------------------------------------------------
// MAIN INITIALIZATION & GAME LOOP
// ------------------------------------------------------------------------------
void main(void) {
    unsigned char pad, pad_trig;
    int screen_x;

    init_game();

    // 1. Initialize PPU & Hardware
    ppu_off();
    pal_bg(bg_palette);
    pal_spr(spr_palette);

    // 2. Load Screen 0 into NT0 ($2000) and Screen 1 into NT1 ($2400)
    vram_adr(0x2000);
    vram_write(screen0_data, 1024);
    vram_adr(0x2400);
    vram_write(screen1_data, 1024);

    set_vram_buffer();
    set_scroll_x(0);
    set_scroll_y(0);
    oam_clear();

    ppu_on_all();

    // --------------------------------------------------------------------------
    // MAIN 60 FPS GAME LOOP
    // --------------------------------------------------------------------------
    while (1) {
        ppu_wait_nmi();

        // 1. Read Controller Inputs
        pad = pad_poll(0);
        pad_trig = pad_trigger(0);

        // 2. Sleep Mode Check
        if (game_mode == MODE_SLEEP) {
            if (pad_trig & (PAD_A | PAD_B | PAD_START | PAD_UP)) {
                game_mode = MODE_PLAY;
                sfx_play(SFX_BARK);
            } else {
                // Regenerate energy during sleep
                if ((need_timer & 0x0F) == 0 && stat_energy < 100) {
                    stat_energy++;
                }
            }
        } else {
            // Normal Playing Mode

            // --- B BUTTON (BARK / HAU!) ---
            if (pad_trig & PAD_B) {
                bark_timer = 25;
                sfx_play(SFX_BARK);
                if (stat_happy < 100) stat_happy += 2;
            }
            if (bark_timer > 0) bark_timer--;

            // --- DOWN BUTTON (SLEEP IN BUDA) ---
            if ((pad_trig & PAD_DOWN) && dog_x >= 16 && dog_x <= 60) {
                game_mode = MODE_SLEEP;
                sfx_play(SFX_JUMP);
            }

            // --- A BUTTON (JUMP) ---
            if ((pad_trig & PAD_A) && dog_on_ground) {
                dog_vy = JUMP_VELOCITY;
                dog_on_ground = 0;
                sfx_play(SFX_JUMP);
            }

            // --- LEFT / RIGHT WALKING ---
            if (pad & PAD_LEFT) {
                dog_dir = 1;
                dog_x -= RUN_SPEED;
                if (dog_x < 16) dog_x = 16;
                dog_anim_timer++;
                dog_anim_frame = ((dog_anim_timer >> 3) & 1) + 1;
            } else if (pad & PAD_RIGHT) {
                dog_dir = 0;
                dog_x += RUN_SPEED;
                if (dog_x > 980) dog_x = 980;
                dog_anim_timer++;
                dog_anim_frame = ((dog_anim_timer >> 3) & 1) + 1;
            } else {
                dog_anim_timer = 0;
                dog_anim_frame = 0; // Idle
            }

            // --- VERTICAL PHYSICS & GRAVITY ---
            if (!dog_on_ground) {
                dog_vy += GRAVITY;
                if (dog_vy > MAX_FALL_SPEED) dog_vy = MAX_FALL_SPEED;
                dog_y += dog_vy;
                dog_anim_frame = 3; // Jump frame
            }
            check_collision_platforms();

            // --- ITEM PICKUPS ---
            if (item1_active && dog_x >= item1_x - 16 && dog_x <= item1_x + 16 &&
                dog_y >= item1_y - 16 && dog_y <= item1_y + 16) {
                item1_active = 0;
                stat_bones++;
                if (stat_happy < 90) stat_happy += 10;
                sfx_play(SFX_EAT);
            }

            if (item2_active && dog_x >= item2_x - 16 && dog_x <= item2_x + 16 &&
                dog_y >= item2_y - 16 && dog_y <= item2_y + 16) {
                item2_active = 0;
                stat_bones++;
                if (stat_happy < 90) stat_happy += 10;
                sfx_play(SFX_EAT);
            }

            // --- TOY BALL PHYSICS ---
            if (dog_x >= ball_x - 16 && dog_x <= ball_x + 16 &&
                dog_y >= ball_y - 16 && dog_y <= ball_y + 16) {
                ball_vx = (dog_dir == 0) ? 3 : -3;
                sfx_play(SFX_JUMP);
                if (stat_happy < 100) stat_happy++;
            }
            if (ball_vx != 0) {
                ball_x += ball_vx;
                if ((need_timer & 0x03) == 0) {
                    if (ball_vx > 0) ball_vx--;
                    else ball_vx++;
                }
            }
        }

        // --- TAMAGOTCHI DEGRADATION TIMERS ---
        need_timer++;
        if (need_timer >= 120) {
            need_timer = 0;
            if (stat_hunger > 0) stat_hunger--;
            if (stat_energy > 0 && (pad & (PAD_LEFT | PAD_RIGHT | PAD_A))) stat_energy--;
            if (stat_hunger < 20 && stat_happy > 0) stat_happy--;
            update_hud();
        }

        // --- CAMERA TRACKING & HARDWARE SCROLLING ---
        if (dog_x < 116) {
            cam_x = 0;
        } else if (dog_x > 768 + 116) {
            cam_x = 768;
        } else {
            cam_x = dog_x - 116;
        }

        // Check if camera crossed an 8-pixel column boundary
        cam_col = (unsigned char)(cam_x >> 3);
        if (cam_col != cam_prev_col) {
            if (cam_col > cam_prev_col) {
                // Moving right: stream leading column entering right
                unsigned char c = cam_col + 32;
                if (c > 127) c = 127;
                stream_column(c);
            } else {
                // Moving left: stream leading column entering left
                stream_column(cam_col);
            }
            cam_prev_col = cam_col;
        }

        set_scroll_x(cam_x);

        // --- SPRITE RENDERING ---
        oam_clear();
        screen_x = dog_x - cam_x;

        if (game_mode == MODE_SLEEP) {
            oam_meta_spr(screen_x, dog_y + 8, metaspr_sleep);
            oam_spr(screen_x + 18, dog_y - 8, 0x36, 1); // Zzz
        } else {
            if (dog_anim_frame == 3) {
                oam_meta_spr(screen_x, dog_y, dog_dir ? metaspr_jump_left : metaspr_jump_right);
            } else if (dog_anim_frame == 1) {
                oam_meta_spr(screen_x, dog_y, dog_dir ? metaspr_walk1_left : metaspr_walk1_right);
            } else if (dog_anim_frame == 2) {
                oam_meta_spr(screen_x, dog_y, dog_dir ? metaspr_walk2_left : metaspr_walk2_right);
            } else {
                oam_meta_spr(screen_x, dog_y, dog_dir ? metaspr_idle_left : metaspr_idle_right);
            }

            if (bark_timer > 0) {
                int bubble_x = (dog_dir == 0) ? (screen_x + 22) : (screen_x - 16);
                if (bubble_x >= 0 && bubble_x <= 240) {
                    oam_meta_spr(bubble_x, dog_y - 12, metaspr_hau);
                }
            }
        }

        // Render Collectible Bones
        if (item1_active) {
            int ix = item1_x - cam_x;
            if (ix >= 0 && ix <= 248) {
                oam_spr(ix, item1_y, 0x30, 2);
            }
        }
        if (item2_active) {
            int ix = item2_x - cam_x;
            if (ix >= 0 && ix <= 248) {
                oam_spr(ix, item2_y, 0x30, 2);
            }
        }

        // Render Toy Ball
        {
            int bx = ball_x - cam_x;
            if (bx >= 0 && bx <= 248) {
                oam_spr(bx, ball_y, 0x31, 2);
            }
        }
    }
}
