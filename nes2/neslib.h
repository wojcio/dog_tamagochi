#ifndef _NESLIB_H
#define _NESLIB_H

// Joypad button bitmasks
#define PAD_A      0x01
#define PAD_B      0x02
#define PAD_SELECT 0x04
#define PAD_START  0x08
#define PAD_UP     0x10
#define PAD_DOWN   0x20
#define PAD_LEFT   0x40
#define PAD_RIGHT  0x80

// Sprite attributes
#define OAM_FLIP_V 0x80
#define OAM_FLIP_H 0x40
#define OAM_BEHIND 0x20

void __fastcall__ ppu_wait_nmi(void);
void __fastcall__ ppu_wait_frame(void);
void __fastcall__ ppu_off(void);
void __fastcall__ ppu_on_all(void);
void __fastcall__ ppu_on_bg(void);
void __fastcall__ ppu_on_spr(void);
void __fastcall__ ppu_mask(unsigned char mask);

void __fastcall__ oam_clear(void);
unsigned char __fastcall__ oam_spr(unsigned char x, unsigned char y, unsigned char chrnum, unsigned char attr);
unsigned char __fastcall__ oam_meta_spr(unsigned char x, unsigned char y, const unsigned char *data);
void __fastcall__ oam_hide_rest(unsigned char sprid);

unsigned char __fastcall__ pad_poll(unsigned char pad);
unsigned char __fastcall__ pad_trigger(unsigned char pad);
unsigned char __fastcall__ pad_state(unsigned char pad);

void __fastcall__ scroll(unsigned int x, unsigned int y);

void __fastcall__ vram_adr(unsigned int adr);
void __fastcall__ vram_put(unsigned char n);
void __fastcall__ vram_fill(unsigned char n, unsigned int len);
void __fastcall__ vram_inc(unsigned char n);
void __fastcall__ vram_read(unsigned char *dst, unsigned int size);
void __fastcall__ vram_write(const unsigned char *src, unsigned int size);

void __fastcall__ pal_all(const unsigned char *data);
void __fastcall__ pal_bg(const unsigned char *data);
void __fastcall__ pal_spr(const unsigned char *data);
void __fastcall__ pal_col(unsigned char index, unsigned char color);
void __fastcall__ pal_clear(void);

// APU SFX
void __fastcall__ sfx_play(unsigned char sound);

// Fast VBlank Column Streaming
void __fastcall__ queue_col_stream(unsigned char col_id);

#endif
