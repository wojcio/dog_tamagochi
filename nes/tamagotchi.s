; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; tamagotchi.s: Multi-Biome Needs, Collectibles across 4 Biomes, and Dual-NT HUD
; ==============================================================================

init_tamagotchi:
    lda #80
    sta stat_hunger
    sta stat_energy
    lda #90
    sta stat_happy
    lda #3              ; Start with 3 bones like in Python
    sta stat_bones
    lda #0
    sta tamagotchi_tick

    ; Collectibles across the 4 Biomes:
    ; Bone 1: Ogrod (world X: 88, Y: 88)
    lda #88
    sta item1_x_lo
    lda #0
    sta item1_x_hi
    lda #88
    sta item1_y
    lda #1
    sta item1_active

    ; Bone 2: Park on the Mostek (world X: 410, Y: 48) -> 410 = $019A
    lda #$9A
    sta item2_x_lo
    lda #1
    sta item2_x_hi
    lda #48
    sta item2_y
    lda #1
    sta item2_active

    ; Toy Ball: Sunny Beach (world X: 640, Y: 152) -> 640 = $0280
    lda #$80
    sta toyball_x_lo
    lda #2
    sta toyball_x_hi
    lda #152
    sta toyball_y
    lda #0
    sta toyball_vx
    rts

update_tamagotchi:
    ; Check if sleeping
    lda game_mode
    cmp #MODE_SLEEP
    bne @normal_needs

    inc tamagotchi_tick
    lda tamagotchi_tick
    and #$03
    bne @check_pickups

    lda stat_energy
    cmp #100
    bcs @fully_rested
    inc stat_energy
    lda stat_happy
    cmp #100
    bcs @check_pickups
    inc stat_happy
    jmp @check_pickups

@fully_rested:
    lda #100
    sta stat_energy
    lda #MODE_PLAY
    sta game_mode
    lda #SFX_TRICK
    jsr play_sfx
    jmp @check_pickups

@normal_needs:
    inc tamagotchi_tick
    lda tamagotchi_tick
    cmp #120
    bcc @check_pickups
    lda #0
    sta tamagotchi_tick

    ; Drain hunger
    lda stat_hunger
    beq @drain_energy
    dec stat_hunger

@drain_energy:
    lda gamepad_cur
    and #(BTN_LEFT | BTN_RIGHT | BTN_A)
    beq @check_sad
    lda stat_energy
    beq @check_sad
    dec stat_energy

@check_sad:
    lda stat_hunger
    cmp #20
    bcs @check_pickups
    lda stat_happy
    beq @check_pickups
    dec stat_happy

@check_pickups:
    ; --- CHECK BONE 1 (Ogrod) ---
    lda item1_active
    beq @check_bone2
    lda dog_x_hi
    cmp item1_x_hi
    bne @check_bone2
    lda dog_x_lo
    sec
    sbc item1_x_lo
    bpl :+
    eor #$FF
    clc
    adc #1
:   cmp #16
    bcs @check_bone2
    lda dog_y
    sec
    sbc item1_y
    bpl :+
    eor #$FF
    clc
    adc #1
:   cmp #16
    bcs @check_bone2

    ; Pickup Bone 1!
    lda #0
    sta item1_active
    inc stat_bones
    lda stat_happy
    clc
    adc #10
    cmp #100
    bcc :+
    lda #100
:   sta stat_happy
    lda #SFX_EAT
    jsr play_sfx

@check_bone2:
    ; --- CHECK BONE 2 (Park Mostek) ---
    lda item2_active
    beq @check_ball
    lda dog_x_hi
    cmp item2_x_hi
    bne @check_ball
    lda dog_x_lo
    sec
    sbc item2_x_lo
    bpl :+
    eor #$FF
    clc
    adc #1
:   cmp #16
    bcs @check_ball
    lda dog_y
    sec
    sbc item2_y
    bpl :+
    eor #$FF
    clc
    adc #1
:   cmp #16
    bcs @check_ball

    ; Pickup Bone 2!
    lda #0
    sta item2_active
    inc stat_bones
    lda stat_happy
    clc
    adc #10
    cmp #100
    bcc :+
    lda #100
:   sta stat_happy
    lda #SFX_EAT
    jsr play_sfx

@check_ball:
    ; --- TOY BALL (Beach) ---
    lda dog_x_hi
    cmp toyball_x_hi
    bne @ball_physics
    lda dog_x_lo
    sec
    sbc toyball_x_lo
    bpl :+
    eor #$FF
    clc
    adc #1
:   cmp #16
    bcs @ball_physics

    ; Kick ball
    lda dog_dir
    beq @kick_r
    lda #($100 - 3)
    sta toyball_vx
    jmp @ball_sfx
@kick_r:
    lda #3
    sta toyball_vx
@ball_sfx:
    lda #SFX_JUMP
    jsr play_sfx
    lda stat_happy
    cmp #100
    bcs @ball_physics
    inc stat_happy

@ball_physics:
    lda toyball_vx
    beq @done_ball
    clc
    adc toyball_x_lo
    sta toyball_x_lo
    lda toyball_x_hi
    adc #0
    sta toyball_x_hi

    ; Decelerate
    lda tamagotchi_tick
    and #$03
    bne @done_ball
    lda toyball_vx
    bmi @b_neg
    dec toyball_vx
    jmp @done_ball
@b_neg:
    inc toyball_vx

@done_ball:
    rts

; ------------------------------------------------------------------------------
; RENDER ITEM SPRITES TO OAM RELATIVE TO CAMERA
; ------------------------------------------------------------------------------
render_item_sprites:
    ; Bone 1 (Sprite 10)
    lda item1_active
    beq @hide_b1
    ; Compute screen X = item_x - cam_x
    lda item1_x_lo
    sec
    sbc cam_x_lo
    sta math_temp       ; diff_lo
    lda item1_x_hi
    sbc cam_x_hi        ; diff_hi
    bne @hide_b1        ; Off-screen if high byte != 0
    lda math_temp
    cmp #248
    bcs @hide_b1

    lda item1_y
    sta OAM_BUFFER + 44
    lda #$2F            ; Bone sprite tile
    sta OAM_BUFFER + 45
    lda #%00000010      ; Palette 2 (Gold)
    sta OAM_BUFFER + 46
    lda math_temp
    sta OAM_BUFFER + 47
    jmp @check_b2_spr
@hide_b1:
    lda #$FF
    sta OAM_BUFFER + 44

@check_b2_spr:
    ; Bone 2 (Sprite 12)
    lda item2_active
    beq @hide_b2
    lda item2_x_lo
    sec
    sbc cam_x_lo
    sta math_temp
    lda item2_x_hi
    sbc cam_x_hi
    bne @hide_b2
    lda math_temp
    cmp #248
    bcs @hide_b2

    lda item2_y
    sta OAM_BUFFER + 48
    lda #$2F
    sta OAM_BUFFER + 49
    lda #%00000010
    sta OAM_BUFFER + 50
    lda math_temp
    sta OAM_BUFFER + 51
    jmp @check_ball_spr
@hide_b2:
    lda #$FF
    sta OAM_BUFFER + 48

@check_ball_spr:
    ; Toy Ball (Sprite 13)
    lda toyball_x_lo
    sec
    sbc cam_x_lo
    sta math_temp
    lda toyball_x_hi
    sbc cam_x_hi
    bne @hide_ball
    lda math_temp
    cmp #248
    bcs @hide_ball

    lda toyball_y
    sta OAM_BUFFER + 52
    lda #$30            ; Ball sprite tile
    sta OAM_BUFFER + 53
    lda #%00000010
    sta OAM_BUFFER + 54
    lda math_temp
    sta OAM_BUFFER + 55
    rts
@hide_ball:
    lda #$FF
    sta OAM_BUFFER + 52
    rts

; ------------------------------------------------------------------------------
; UPDATE DYNAMIC HUD METERS IN VRAM (DUAL NAMETABLE UPDATE)
; Updates both NT0 ($2048..) and NT1 ($2448..) so HUD never flickers on scroll!
; ------------------------------------------------------------------------------
update_hud_vram:
    ; Precalculate bar values
    lda stat_hunger
    jsr @calc_bar
    lda math_temp
    sta hunger_bar_val

    lda stat_energy
    jsr @calc_bar
    lda math_temp
    sta energy_bar_val

    lda stat_happy
    jsr @calc_bar
    lda math_temp
    sta happy_bar_val

    ; 1. Update GLOD Bar in NT0 ($2048)
    lda PPUSTATUS
    lda #$20
    sta PPUADDR
    lda #$48
    sta PPUADDR
    jsr @write_glod_bar

    ; Update GLOD Bar in NT1 ($2448)
    lda #$24
    sta PPUADDR
    lda #$48
    sta PPUADDR
    jsr @write_glod_bar

    ; 2. Update ENER Bar in NT0 ($2057)
    lda #$20
    sta PPUADDR
    lda #$57
    sta PPUADDR
    jsr @write_ener_bar

    ; Update ENER Bar in NT1 ($2457)
    lda #$24
    sta PPUADDR
    lda #$57
    sta PPUADDR
    jsr @write_ener_bar

    ; 3. Update SZCZ Bar in NT0 ($2068)
    lda #$20
    sta PPUADDR
    lda #$68
    sta PPUADDR
    jsr @write_szcz_bar

    ; Update SZCZ Bar in NT1 ($2468)
    lda #$24
    sta PPUADDR
    lda #$68
    sta PPUADDR
    jsr @write_szcz_bar

    ; 4. Update KOSCI Digits in NT0 ($2078)
    lda #$20
    sta PPUADDR
    lda #$78
    sta PPUADDR
    jsr @write_bones_digits

    ; Update KOSCI Digits in NT1 ($2478)
    lda #$24
    sta PPUADDR
    lda #$78
    sta PPUADDR
    jsr @write_bones_digits
    rts

@write_glod_bar:
    lda hunger_bar_val
    sta math_temp
    ldx #6
:   lda math_temp
    beq @g_emp
    dec math_temp
    lda #$80            ; █
    jmp :+
@g_emp:
    lda #$81            ; ░
:   sta PPUDATA
    dex
    bne :--
    rts

@write_ener_bar:
    lda energy_bar_val
    sta math_temp
    ldx #6
:   lda math_temp
    beq @e_emp
    dec math_temp
    lda #$80
    jmp :+
@e_emp:
    lda #$81
:   sta PPUDATA
    dex
    bne :--
    rts

@write_szcz_bar:
    lda happy_bar_val
    sta math_temp
    ldx #6
:   lda math_temp
    beq @s_emp
    dec math_temp
    lda #$80
    jmp :+
@s_emp:
    lda #$81
:   sta PPUDATA
    dex
    bne :--
    rts

@write_bones_digits:
    lda stat_bones
    ldx #0
@div10:
    cmp #10
    bcc @tens_done
    sec
    sbc #10
    inx
    jmp @div10
@tens_done:
    pha
    txa
    clc
    adc #$30
    sta PPUDATA
    pla
    clc
    adc #$30
    sta PPUDATA
    rts

@calc_bar:
    cmp #84
    bcs @b6
    cmp #67
    bcs @b5
    cmp #50
    bcs @b4
    cmp #34
    bcs @b3
    cmp #17
    bcs @b2
    cmp #5
    bcs @b1
    lda #0
    sta math_temp
    rts
@b6: lda #6
    sta math_temp
    rts
@b5: lda #5
    sta math_temp
    rts
@b4: lda #4
    sta math_temp
    rts
@b3: lda #3
    sta math_temp
    rts
@b2: lda #2
    sta math_temp
    rts
@b1: lda #1
    sta math_temp
    rts
