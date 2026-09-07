#ifndef _NESDOUG_H
#define _NESDOUG_H

void __fastcall__ set_scroll_x(unsigned int x);
void __fastcall__ set_scroll_y(unsigned int y);
unsigned int __fastcall__ get_scroll_x(void);
unsigned int __fastcall__ get_scroll_y(void);

struct Box {
    int x;
    int y;
    int width;
    int height;
};

unsigned char __fastcall__ check_collision(void *box1, void *box2);

// Buffered VRAM writing during VBlank
void __fastcall__ set_vram_buffer(void);
void __fastcall__ one_vram_buffer(unsigned char data, int ppu_address);
void __fastcall__ multi_vram_buffer_horz(const char *data, unsigned char len, int ppu_address);
void __fastcall__ multi_vram_buffer_vert(const char *data, unsigned char len, int ppu_address);

#endif
