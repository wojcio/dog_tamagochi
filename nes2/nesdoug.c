#include "neslib.h"
#include "nesdoug.h"

static unsigned int current_scroll_x = 0;
static unsigned int current_scroll_y = 0;

void __fastcall__ set_scroll_x(unsigned int x) {
    current_scroll_x = x;
    scroll(current_scroll_x, current_scroll_y);
}

void __fastcall__ set_scroll_y(unsigned int y) {
    current_scroll_y = y;
    scroll(current_scroll_x, current_scroll_y);
}

unsigned int __fastcall__ get_scroll_x(void) {
    return current_scroll_x;
}

unsigned int __fastcall__ get_scroll_y(void) {
    return current_scroll_y;
}

unsigned char __fastcall__ check_collision(void *box1, void *box2) {
    struct Box *b1 = (struct Box*)box1;
    struct Box *b2 = (struct Box*)box2;
    if (b1->x >= b2->x + b2->width) return 0;
    if (b1->x + b1->width <= b2->x) return 0;
    if (b1->y >= b2->y + b2->height) return 0;
    if (b1->y + b1->height <= b2->y) return 0;
    return 1;
}

// VRAM Ring Buffer
#define VRAM_BUF_SIZE 128
static unsigned char vram_buf[VRAM_BUF_SIZE];
static unsigned char vram_buf_idx = 0;

void __fastcall__ set_vram_buffer(void) {
    vram_buf_idx = 0;
    vram_buf[0] = 0xFF; // Terminator
}

void __fastcall__ one_vram_buffer(unsigned char data, int ppu_address) {
    if (vram_buf_idx >= VRAM_BUF_SIZE - 5) return;
    vram_buf[vram_buf_idx++] = (unsigned char)(ppu_address >> 8);
    vram_buf[vram_buf_idx++] = (unsigned char)(ppu_address & 0xFF);
    vram_buf[vram_buf_idx++] = 1; // Length (horizontal)
    vram_buf[vram_buf_idx++] = data;
    vram_buf[vram_buf_idx] = 0xFF; // Terminator
}

void __fastcall__ multi_vram_buffer_horz(const char *data, unsigned char len, int ppu_address) {
    unsigned char i;
    if (vram_buf_idx + len + 4 >= VRAM_BUF_SIZE) return;
    vram_buf[vram_buf_idx++] = (unsigned char)(ppu_address >> 8);
    vram_buf[vram_buf_idx++] = (unsigned char)(ppu_address & 0xFF);
    vram_buf[vram_buf_idx++] = len; // Bit 7 = 0: horizontal
    for (i = 0; i < len; ++i) {
        vram_buf[vram_buf_idx++] = data[i];
    }
    vram_buf[vram_buf_idx] = 0xFF;
}

void __fastcall__ multi_vram_buffer_vert(const char *data, unsigned char len, int ppu_address) {
    unsigned char i;
    if (vram_buf_idx + len + 4 >= VRAM_BUF_SIZE) return;
    vram_buf[vram_buf_idx++] = (unsigned char)(ppu_address >> 8);
    vram_buf[vram_buf_idx++] = (unsigned char)(ppu_address & 0xFF);
    vram_buf[vram_buf_idx++] = len | 0x80; // Bit 7 = 1: vertical (+32)
    for (i = 0; i < len; ++i) {
        vram_buf[vram_buf_idx++] = data[i];
    }
    vram_buf[vram_buf_idx] = 0xFF;
}

// Called during VBlank from neslib NMI
void flush_vram_buffer_internal(void) {
    unsigned char idx = 0;
    unsigned char hi, lo, len, vert, i;
    while (idx < vram_buf_idx) {
        hi = vram_buf[idx++];
        if (hi == 0xFF) break;
        lo = vram_buf[idx++];
        len = vram_buf[idx++];
        vert = len & 0x80;
        len &= 0x7F;

        if (vert) {
            vram_inc(1); // Set vertical increment +32
        } else {
            vram_inc(0); // Set horizontal increment +1
        }
        vram_adr(((int)hi << 8) | lo);
        for (i = 0; i < len; ++i) {
            vram_put(vram_buf[idx++]);
        }
    }
    vram_inc(0);
    vram_buf_idx = 0;
    vram_buf[0] = 0xFF;
}
