; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; ppu.s: PPU Hardware Management, Palettes, and OAM
; ==============================================================================

wait_vblank:
    bit PPUSTATUS
@loop:
    bit PPUSTATUS
    bpl @loop
    rts

load_palettes:
    lda PPUSTATUS       ; Reset address latch
    lda #$3F
    sta PPUADDR
    lda #$00
    sta PPUADDR

    ldx #0
@pal_loop:
    lda palette_data, x
    sta PPUDATA
    inx
    cpx #32
    bne @pal_loop
    rts

; Authentic Colorful Retro Terminal Palettes on Dark Black Background
palette_data:
    ; Background Palettes ($3F00 - $3F0F)
    .byte $0F, $30, $28, $16   ; BG0: Dark Background ($0F), White Text ($30), Gold ($28), Red ($16)
    .byte $0F, $2A, $16, $27   ; BG1: Grass/Flowers: Dark, Bright Green ($2A), Red ($16), Earth ($27)
    .byte $0F, $30, $28, $2C   ; BG2: Sun/Clouds: Dark, White ($30), Sun Gold ($28), Cyan Water ($2C)
    .byte $0F, $10, $00, $30   ; BG3: Shading: Dark, Light Gray ($10), Dark Gray ($00), White ($30)

    ; Sprite Palettes ($3F10 - $3F1F)
    .byte $0F, $27, $30, $0F   ; SPR0: Corgi: Transparent, Tan Fur ($27), White Fur ($30), Black ($0F)
    .byte $0F, $2C, $30, $16   ; SPR1: Sleep/Water: Transparent, Cyan ($2C), White ($30), Red ($16)
    .byte $0F, $30, $28, $16   ; SPR2: Bone/Ball: Transparent, White ($30), Gold ($28), Red ($16)
    .byte $0F, $2A, $30, $28   ; SPR3: Sparkles: Transparent, Green ($2A), White ($30), Gold ($28)

clear_oam:
    ldx #0
    lda #$FF
@clear_loop:
    sta OAM_BUFFER, x
    inx
    inx
    inx
    inx
    bne @clear_loop
    rts
