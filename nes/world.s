; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; world.s: 4-Biome World Loader, Collision Engine, and Column Streaming Data
; ==============================================================================

load_world_nametable:
    ; 1. Load Screen 0 (Ogrod) into Nametable 0 ($2000 - $23FF)
    lda PPUSTATUS
    lda #$20
    sta PPUADDR
    lda #$00
    sta PPUADDR

    lda #<screen_0_data
    sta ptr_lo
    lda #>screen_0_data
    sta ptr_hi

    ldx #4              ; 4 pages = 1024 bytes
    ldy #0
@loop_nt0:
    lda (ptr_lo), y
    sta PPUDATA
    iny
    bne @loop_nt0
    inc ptr_hi
    dex
    bne @loop_nt0

    ; 2. Load Screen 1 (Park) into Nametable 1 ($2400 - $27FF)
    lda PPUSTATUS
    lda #$24
    sta PPUADDR
    lda #$00
    sta PPUADDR

    lda #<screen_1_data
    sta ptr_lo
    lda #>screen_1_data
    sta ptr_hi

    ldx #4
    ldy #0
@loop_nt1:
    lda (ptr_lo), y
    sta PPUDATA
    iny
    bne @loop_nt1
    inc ptr_hi
    dex
    bne @loop_nt1

    rts

; ------------------------------------------------------------------------------
; MULTI-BIOME PLATFORM & GROUND COLLISION
; Checks 16-bit dog world X (dog_x_hi:dog_x_lo) and 8-bit Y (dog_y)
; ------------------------------------------------------------------------------
check_dog_collision:
    ; 1. Floor ground collision across the entire 1024 px world
    lda dog_y
    cmp #GROUND_Y
    bcc @check_platforms
    lda #GROUND_Y
    sta dog_y
    lda #0
    sta dog_vy
    lda #1
    sta dog_on_ground
    rts

@check_platforms:
    ; Only land when falling downward (dog_vy >= 0)
    lda dog_vy
    bpl :+
    jmp @in_air
:

    ; Determine which screen the dog is in (dog_x_hi = 0, 1, 2, or 3)
    lda dog_x_hi
    beq @screen0_plats
    cmp #1
    beq @screen1_plats
    cmp #2
    beq @screen2_plats
    jmp @screen3_plats

; --- BIOME 0: OGROD (x: 0..255) ---
@screen0_plats:
    ; Platform 1: x = 56..136, y = 88
    lda dog_y
    cmp #88
    bcc @s0_p2
    cmp #(88 + 5)
    bcs @s0_p2
    lda dog_x_lo
    cmp #56
    bcc @s0_p2
    cmp #136
    bcs @s0_p2
    lda #88
    sta dog_y
    lda #0
    sta dog_vy
    lda #1
    sta dog_on_ground
    rts

@s0_p2:
    ; Platform 2: x = 120..224, y = 64
    lda dog_y
    cmp #64
    bcc @in_air
    cmp #(64 + 5)
    bcs @in_air
    lda dog_x_lo
    cmp #120
    bcc @in_air
    cmp #224
    bcs @in_air
    lda #64
    sta dog_y
    lda #0
    sta dog_vy
    lda #1
    sta dog_on_ground
    rts

; --- BIOME 1: PARK MIEJSKI (x: 256..511) ---
@screen1_plats:
    ; Wysoki Mostek: x = 336..496 (x_lo: 80..240), y = 72
    lda dog_y
    cmp #72
    bcc @in_air
    cmp #(72 + 5)
    bcs @in_air
    lda dog_x_lo
    cmp #80             ; 256 + 80 = 336
    bcc @in_air
    cmp #240            ; 256 + 240 = 496
    bcs @in_air
    lda #72
    sta dog_y
    lda #0
    sta dog_vy
    lda #1
    sta dog_on_ground
    rts

; --- BIOME 2: SŁONECZNA PLAŻA (x: 512..767) ---
@screen2_plats:
    ; Leżaki: x = 544..624 (x_lo: 32..112), y = 88
    lda dog_y
    cmp #88
    bcc @in_air
    cmp #(88 + 5)
    bcs @in_air
    lda dog_x_lo
    cmp #32
    bcc @in_air
    cmp #112
    bcs @in_air
    lda #88
    sta dog_y
    lda #0
    sta dog_vy
    lda #1
    sta dog_on_ground
    rts

; --- BIOME 3: TOR AGILITY (x: 768..1023) ---
@screen3_plats:
    ; Agility Płotek: x = 840..900 (x_lo: 72..132), y = 88
    lda dog_y
    cmp #88
    bcc @in_air
    cmp #(88 + 5)
    bcs @in_air
    lda dog_x_lo
    cmp #72
    bcc @in_air
    cmp #132
    bcs @in_air
    lda #88
    sta dog_y
    lda #0
    sta dog_vy
    lda #1
    sta dog_on_ground
    rts

@in_air:
    lda #0
    sta dog_on_ground
    rts

; ------------------------------------------------------------------------------
; BINARY DATA FOR 4-BIOME WORLD
; ------------------------------------------------------------------------------
.segment "RODATA"
col_offset_lo:
    .repeat 128, i
        .byte <(i * 30)
    .endrepeat

col_offset_hi:
    .repeat 128, i
        .byte >(i * 30)
    .endrepeat

screen_0_data:
    .incbin "screen_0.bin"

screen_1_data:
    .incbin "screen_1.bin"

world_cols_data:
    .incbin "world_cols.bin"
