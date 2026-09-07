; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; main.s: NES Bootloader, Reset, NMI Handler, Main Loop, and Game Integration
; ==============================================================================

.include "constants.inc"

; ------------------------------------------------------------------------------
; ZERO PAGE RAM ALLOCATIONS ($0000 - $00FF)
; ------------------------------------------------------------------------------
.segment "ZEROPAGE"
nmi_counter:    .res 1
frame_ready:    .res 1
game_mode:      .res 1      ; MODE_PLAY, MODE_SLEEP, MODE_PAUSED

; Joypad Input
gamepad_cur:    .res 1
gamepad_prev:   .res 1
gamepad_press:  .res 1

; 16-bit Dog State
dog_x_lo:       .res 1
dog_x_hi:       .res 1
dog_y:          .res 1
dog_vx:         .res 1
dog_vy:         .res 1
dog_dir:        .res 1      ; 0 = right, 1 = left
dog_on_ground:  .res 1      ; 0 = air, 1 = grounded
dog_anim_timer: .res 1
dog_anim_frame: .res 1
bark_timer:     .res 1
dog_screen_x:   .res 1

; 16-bit Camera & Scrolling
cam_x_lo:       .res 1
cam_x_hi:       .res 1
scroll_x:       .res 1
scroll_nt:      .res 1
cam_prev_col:   .res 1
col_draw_flag:  .res 1
col_to_draw:    .res 1
col_dest_hi:    .res 1
col_dest_lo:    .res 1

; Tamagotchi Needs (0..100)
stat_hunger:    .res 1
stat_energy:    .res 1
stat_happy:     .res 1
stat_bones:     .res 1
tamagotchi_tick:.res 1

hunger_bar_val: .res 1
energy_bar_val: .res 1
happy_bar_val:  .res 1

; APU Sound Engine State
sfx_playing:    .res 1
sfx_timer:      .res 1
sfx_step:       .res 1

; Items and Collectibles (16-bit X)
item1_x_lo:     .res 1
item1_x_hi:     .res 1
item1_y:        .res 1
item1_active:   .res 1

item2_x_lo:     .res 1
item2_x_hi:     .res 1
item2_y:        .res 1
item2_active:   .res 1

; Toy Ball (16-bit X)
toyball_x_lo:   .res 1
toyball_x_hi:   .res 1
toyball_y:      .res 1
toyball_vx:     .res 1

; Working pointers and scratchpad
ptr_lo:         .res 1
ptr_hi:         .res 1
math_temp:      .res 1
math_temp_hi:   .res 1

; ------------------------------------------------------------------------------
; OAM SPRITE BUFFER ($0200 - $02FF)
; ------------------------------------------------------------------------------
.segment "OAM"
OAM_BUFFER:     .res 256

; ------------------------------------------------------------------------------
; CODE SEGMENT ($8000 - $FFF9)
; ------------------------------------------------------------------------------
.segment "CODE"

.include "input.s"
.include "apu.s"
.include "ppu.s"
.include "world.s"
.include "dog.s"
.include "tamagotchi.s"

; ------------------------------------------------------------------------------
; RESET HANDLER: Hardware Initialization & Boot Sequence
; ------------------------------------------------------------------------------
reset_handler:
    sei                 ; Ignore IRQs
    cld                 ; Disable decimal mode

    ; Disable APU frame IRQ
    ldx #$40
    stx APU_FRAME

    ; Setup stack pointer to $01FF
    ldx #$FF
    txs

    ; Disable NMI and Rendering during initial boot
    inx                 ; X = 0
    stx PPUCTRL
    stx PPUMASK
    stx DMC_FREQ        ; Disable DMC IRQ

    ; First VBlank wait (PPU warmup)
    jsr wait_vblank

    ; Clear RAM ($0000 - $07FF) except stack
    txa
@clear_ram:
    sta $0000, x
    sta $0200, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram

    ; Second VBlank wait (PPU is now fully stabilized)
    jsr wait_vblank

    ; Initialize PPU Palettes and World Nametables (Screen 0 & Screen 1)
    jsr load_palettes
    jsr load_world_nametable
    jsr clear_oam

    ; Sprite 0 unused (hidden offscreen)
    lda #$FF
    sta OAM_BUFFER + 0

    ; Initialize APU, Player, and Needs
    jsr init_apu
    jsr init_dog
    jsr init_tamagotchi

    ; Reset PPU scroll to (0, 0)
    lda PPUSTATUS
    lda #0
    sta PPUSCROLL
    sta PPUSCROLL

    ; Enable VBlank NMI & PPU Rendering
    ; Bit 7 = 1 (NMI Enable)
    ; Bit 4 = 0 (Background from Pattern Table 0: $0000 - ASCII Font)
    ; Bit 3 = 1 (Sprites from Pattern Table 1: $1000 - Corgi Sprites)
    ; Bit 0 = 0 (Start at Nametable 0)
    ; %10001000 = $88
    lda #%10001000
    sta PPUCTRL

    ; PPUMASK: Enable BG, Sprites, and Left 8px clipping -> %00011110 = $1E
    lda #%00011110
    sta PPUMASK

; ------------------------------------------------------------------------------
; MAIN GAME LOOP (Synchronized to 60 FPS via NMI counter)
; ------------------------------------------------------------------------------
main_loop:
    lda nmi_counter
@wait_frame:
    cmp nmi_counter
    beq @wait_frame

    ; 1. Read Controller Inputs
    jsr read_controller

    ; 2. Update Dog Physics, Movement, and Smooth Camera Tracking
    jsr update_dog

    ; 3. Update Tamagotchi Needs and Items
    jsr update_tamagotchi

    ; 4. Render Sprites to OAM Buffer ($0200)
    jsr render_dog_sprites
    jsr render_item_sprites

    jmp main_loop

; ------------------------------------------------------------------------------
; NMI INTERRUPT HANDLER (Executes once per frame at VBlank)
; ------------------------------------------------------------------------------
nmi_handler:
    pha
    txa
    pha
    tya
    pha

    ; 1. Fast OAM DMA Transfer: Copy $0200-$02FF directly into PPU OAM
    lda #$00
    sta OAMADDR
    lda #>OAM_BUFFER    ; High byte of OAM buffer ($02)
    sta OAMDMA

    ; 2. Column Streaming (if camera crossed an 8-pixel column boundary)
    lda col_draw_flag
    beq @skip_col_draw

    ; Set PPUCTRL with bit 2 = 1 (VRAM address increment = 32 down column)
    lda #%10001100
    sta PPUCTRL

    ; Set PPUADDR to target column (row 0: $2000 + col_dest_lo or $2400 + col_dest_lo)
    lda col_dest_hi
    sta PPUADDR
    lda col_dest_lo
    sta PPUADDR

    ; Compute ROM address: world_cols_data + col_to_draw * 30 using lookup table
    ldx col_to_draw
    lda col_offset_lo, x
    clc
    adc #<world_cols_data
    sta ptr_lo
    lda col_offset_hi, x
    adc #>world_cols_data
    sta ptr_hi

    ; Stream 30 bytes down the column
    ldy #0
@stream_30:
    lda (ptr_lo), y
    sta PPUDATA
    iny
    cpy #30
    bne @stream_30

    lda #0
    sta col_draw_flag

    ; Reset PPUCTRL to horizontal increment (bit 2 = 0)
    lda #%10001000
    sta PPUCTRL

@skip_col_draw:
    ; 3. Update Dynamic HUD in Nametables
    jsr update_hud_vram

    ; 4. Set final PPUCTRL with scroll_nt (Nametable select: bit 0)
    lda #%10001000
    ora scroll_nt
    sta PPUCTRL

    ; 5. Set PPU Scroll to (scroll_x, 0)
    lda PPUSTATUS       ; Reset address/scroll latch
    lda scroll_x
    sta PPUSCROLL
    lda #0
    sta PPUSCROLL

    ; 6. Update APU Sound Synthesizer
    jsr update_apu

    ; Increment frame counter
    inc nmi_counter

    pla
    tay
    pla
    tax
    pla
    rti

; ------------------------------------------------------------------------------
; IRQ / BRK HANDLER (Unused)
; ------------------------------------------------------------------------------
irq_handler:
    rti

; ------------------------------------------------------------------------------
; HARDWARE INTERRUPT VECTORS ($FFFA - $FFFF)
; ------------------------------------------------------------------------------
.segment "VECTORS"
    .word nmi_handler   ; $FFFA: NMI Vector
    .word reset_handler ; $FFFC: Reset Vector
    .word irq_handler   ; $FFFE: IRQ / BRK Vector

; ------------------------------------------------------------------------------
; 8KB CHR-ROM PATTERN TABLE DATA
; ------------------------------------------------------------------------------
.segment "CHARS"
    .incbin "graphics.chr"
