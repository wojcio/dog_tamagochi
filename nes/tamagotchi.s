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
    ; Throttle eating SFX repeat
    lda eat_timer
    beq @no_eat_tick
    dec eat_timer
@no_eat_tick:
    ; Ball kick cooldown
    lda toyball_cd
    beq @no_ball_tick
    dec toyball_cd
@no_ball_tick:

    ; Check if sleeping
    lda game_mode
    cmp #MODE_SLEEP
    bne @normal_needs

    inc tamagotchi_tick
    lda tamagotchi_tick
    and #$03
    bne @sleep_done

    lda stat_energy
    cmp #100
    bcs @fully_rested
    inc stat_energy
    lda stat_happy
    cmp #100
    bcs @sleep_done
    inc stat_happy
    jmp @sleep_done

@fully_rested:
    lda #100
    sta stat_energy
    lda #MODE_PLAY
    sta game_mode
    lda #SFX_TRICK
    jsr play_sfx
@sleep_done:
    jmp @check_pickups

@normal_needs:
    ; --- EAT AT THE BOWL (hold UP near the buda, screen 0; every frame) ---
    lda gamepad_cur
    and #BTN_UP
    beq @needs_gate
    lda dog_on_ground
    beq @needs_gate
    lda dog_x_hi              ; bowl lives in screen 0 (world x < 256)
    bne @needs_gate
    lda dog_x_lo
    cmp #BOWL_X_MIN
    bcc @needs_gate
    cmp #BOWL_X_MAX
    bcs @needs_gate
    lda stat_hunger
    cmp #100
    bcs @needs_gate
    clc
    adc #6
    cmp #100
    bcc @bowl_fed
    lda #100
@bowl_fed:
    sta stat_hunger
    lda eat_timer
    bne @needs_gate
    lda #32
    sta eat_timer
    lda #SFX_EAT
    jsr play_sfx

@needs_gate:
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
    ; Drain only if the dog actually ran or jumped in this window
    ; (the old check sampled keys exactly at the 120-tick boundary).
    lda worked_flag
    beq @check_sad
    lda #0
    sta worked_flag
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
    ; --- TOY BALL (Beach; 30-frame kick cooldown stops SFX spam and
    ;     push-walking the ball while standing on it) ---
    lda toyball_cd
    bne @ball_physics

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
    lda #30
    sta toyball_cd        ; one bark per kick (parity with Python fix)
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
    ; --- GLOD Bar (row 2, col 8) in NT0 $2048 / NT1 $2448 ---
    lda stat_hunger
    jsr @calc_bar
    lda math_temp
    cmp hud_cache+0
    beq @hud_ener
    sta hud_cache+0
    sta bar_fill
    lda #$48
    jsr @write_bar_both

@hud_ener:
    ; --- ENER Bar (row 2, col 23) ---
    lda stat_energy
    jsr @calc_bar
    lda math_temp
    cmp hud_cache+1
    beq @hud_szcz
    sta hud_cache+1
    sta bar_fill
    lda #$57
    jsr @write_bar_both

@hud_szcz:
    ; --- SZCZ Bar (row 3, col 8) ---
    lda stat_happy
    jsr @calc_bar
    lda math_temp
    cmp hud_cache+2
    beq @hud_bones
    sta hud_cache+2
    sta bar_fill
    lda #$68
    jsr @write_bar_both

@hud_bones:
    ; --- KOSCI digits (row 3, col 24) ---
    lda stat_bones
    cmp hud_cache+3
    beq @hud_done
    sta hud_cache+3
    ldx #$FF                ; divide by 10: X = tens, A = ones
    sec
@div10:
    inx
    sbc #10
    bcs @div10
    adc #10                 ; restore remainder
    clc
    adc #$30
    sta energy_bar_val      ; ones digit tile (ZP reused as scratch)
    txa
    clc
    adc #$30
    sta hunger_bar_val      ; tens digit tile (ZP reused as scratch)

    lda #$20
    sta PPUADDR
    lda #$78
    sta PPUADDR
    lda hunger_bar_val
    sta PPUDATA
    lda energy_bar_val
    sta PPUDATA
    lda #$24
    sta PPUADDR
    lda #$78
    sta PPUADDR
    lda hunger_bar_val
    sta PPUDATA
    lda energy_bar_val
    sta PPUDATA
@hud_done:
    rts

; Writes one 7-tile bar (6 cells + ']' bracket) into both nametables.
; In: A = nametable column offset of first cell; bar_fill = 0..6.
@write_bar_both:
    sta math_temp
    lda #$20
    jsr @write_bar_nt
    lda #$24
@write_bar_nt:
    sta PPUADDR
    lda math_temp
    sta PPUADDR
    ldx #0
@cell:
    txa
    cmp bar_fill
    bcs @cell_empty
    lda #$80                ; █
    sta PPUDATA
    jmp @cell_next
@cell_empty:
    lda #$81                ; ░
    sta PPUDATA
@cell_next:
    inx
    cpx #6
    bne @cell
    lda #$5D                ; ']' (the old code clobbered this with ░)
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
