; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; dog.s: 16-bit Movement, Camera Tracking, and OAM Sprite Engine (Sprites 1..9)
; ==============================================================================

init_dog:
    lda #32             ; Start in front of Buda
    sta dog_x_lo
    lda #0
    sta dog_x_hi
    lda #GROUND_Y
    sta dog_y
    lda #0
    sta dog_vx
    sta dog_vy
    sta dog_dir         ; 0 = right, 1 = left
    lda #1
    sta dog_on_ground
    lda #0
    sta dog_anim_timer
    sta dog_anim_frame
    sta bark_timer

    ; Initialize camera to 0
    sta cam_x_lo
    sta cam_x_hi
    sta scroll_x
    sta scroll_nt
    sta col_draw_flag
    lda #0
    sta cam_prev_col
    rts

update_dog:
    ; Sleeping mode check
    lda game_mode
    cmp #MODE_SLEEP
    bne @normal_input

    ; Press any button to wake up
    lda gamepad_press
    and #(BTN_A | BTN_B | BTN_START | BTN_UP)
    beq @keep_sleeping
    lda #MODE_PLAY
    sta game_mode
    lda #SFX_TRICK
    jsr play_sfx
    jmp @update_cam

@keep_sleeping:
    lda #4              ; Frame 4 = Sleep
    sta dog_anim_frame
    rts

@normal_input:
    ; --- B BUTTON (BARK / HAU!) ---
    lda gamepad_press
    and #BTN_B
    beq @no_bark
    lda #25
    sta bark_timer
    lda #SFX_BARK
    jsr play_sfx
    lda stat_happy
    cmp #100
    bcs @no_bark
    inc stat_happy
    inc stat_happy
@no_bark:

    lda bark_timer
    beq @check_down
    dec bark_timer

@check_down:
    ; --- DOWN BUTTON (SLEEP IN BUDA) ---
    lda gamepad_press
    and #BTN_DOWN
    beq @check_jump
    ; Buda is located in Screen 0 (x: 16..60)
    lda dog_x_hi
    bne @check_jump
    lda dog_x_lo
    cmp #BUDA_X_MIN
    bcc @check_jump
    cmp #BUDA_X_MAX
    bcs @check_jump
    ; Fall asleep in the Buda!
    lda #MODE_SLEEP
    sta game_mode
    lda #SFX_SLEEP
    jsr play_sfx
    rts

@check_jump:
    ; --- A BUTTON (JUMP) ---
    lda gamepad_press
    and #BTN_A
    beq @check_walk
    lda dog_on_ground
    beq @check_walk     ; Must be grounded to jump
    lda #($100 - JUMP_VELOCITY)
    sta dog_vy
    lda #0
    sta dog_on_ground
    lda #SFX_JUMP
    jsr play_sfx

@check_walk:
    ; --- LEFT / RIGHT CONTROLS (16-BIT X) ---
    lda gamepad_cur
    and #BTN_LEFT
    beq @check_right
    ; Move left
    lda #1
    sta dog_dir

    ; Sub 2 from dog_x (16-bit)
    lda dog_x_lo
    sec
    sbc #RUN_SPEED
    sta dog_x_lo
    lda dog_x_hi
    sbc #0
    sta dog_x_hi

    ; Min boundary: 16
    bmi @clamp_min_x
    bne @advance_anim
    lda dog_x_lo
    cmp #16
    bcs @advance_anim
@clamp_min_x:
    lda #16
    sta dog_x_lo
    lda #0
    sta dog_x_hi
    jmp @advance_anim

@check_right:
    lda gamepad_cur
    and #BTN_RIGHT
    beq @standing_still
    ; Move right
    lda #0
    sta dog_dir

    ; Add 2 to dog_x (16-bit)
    lda dog_x_lo
    clc
    adc #RUN_SPEED
    sta dog_x_lo
    lda dog_x_hi
    adc #0
    sta dog_x_hi

    ; Max boundary: 980 ($03D4)
    cmp #3
    bcc @advance_anim
    bne @clamp_max_x
    lda dog_x_lo
    cmp #$D4
    bcc @advance_anim
@clamp_max_x:
    lda #$D4
    sta dog_x_lo
    lda #3
    sta dog_x_hi
    jmp @advance_anim

@standing_still:
    lda #0
    sta dog_anim_timer
    lda dog_on_ground
    beq @apply_vertical
    lda #0
    sta dog_anim_frame
    jmp @apply_vertical

@advance_anim:
    inc dog_anim_timer
    lda dog_anim_timer
    lsr a
    lsr a
    and #1
    clc
    adc #1              ; Frame 1 or 2
    sta dog_anim_frame

@apply_vertical:
    lda dog_on_ground
    bne @skip_grav

    lda dog_vy
    clc
    adc #GRAVITY
    cmp #MAX_FALL_SPEED
    bcc @store_vy
    bpl @cap_vy
@store_vy:
    sta dog_vy
    jmp @add_y
@cap_vy:
    lda #MAX_FALL_SPEED
    sta dog_vy

@add_y:
    lda dog_y
    clc
    adc dog_vy
    sta dog_y
    lda #3              ; Frame 3 = Jump
    sta dog_anim_frame

@skip_grav:
    jsr check_dog_collision

@update_cam:
    ; Target camera X = dog_x - 116
    lda dog_x_lo
    sec
    sbc #116
    sta math_temp       ; target_lo
    lda dog_x_hi
    sbc #0              ; target_hi

    ; If target < 0: cam_x = 0
    bmi @cam_zero
    ; If target > 768 ($0300): cam_x = 768
    cmp #3
    bcs @cam_max
    ; In range 0..768
    sta cam_x_hi
    lda math_temp
    sta cam_x_lo
    jmp @update_scroll_vars

@cam_zero:
    lda #0
    sta cam_x_lo
    sta cam_x_hi
    jmp @update_scroll_vars

@cam_max:
    lda #0
    sta cam_x_lo
    lda #3
    sta cam_x_hi

@update_scroll_vars:
    lda cam_x_lo
    sta scroll_x
    lda cam_x_hi
    and #$01
    sta scroll_nt

    ; Check if camera crossed an 8-pixel column boundary
    ; cam_col = (cam_x_hi * 32) + (cam_x_lo / 8)
    lda cam_x_lo
    lsr a
    lsr a
    lsr a               ; cam_x_lo / 8 (0..31)
    sta math_temp
    lda cam_x_hi
    asl a
    asl a
    asl a
    asl a
    asl a               ; cam_x_hi * 32 (0, 32, 64, 96)
    ora math_temp       ; total cam_col (0..96)

    cmp cam_prev_col
    beq @done_camera

    bcc @cam_left

    ; Moving right: stream leading column entering right (cam_col + 32)
    sta cam_prev_col
    clc
    adc #32
    cmp #128
    bcc :+
    lda #127
:   sta col_to_draw
    jmp @setup_col_dest

@cam_left:
    ; Moving left: stream leading column entering left (cam_col)
    sta cam_prev_col
    sta col_to_draw

@setup_col_dest:
    lda #1
    sta col_draw_flag

    ; Destination address in VRAM for col_to_draw (rows 0..29):
    ; NT0: $2000 + (col & 31)
    ; NT1: $2400 + (col & 31)
    lda col_to_draw
    and #31
    sta col_dest_lo

    lda col_to_draw
    and #32
    beq :+
    lda #$24
    sta col_dest_hi
    jmp @done_camera
:   lda #$20
    sta col_dest_hi

@done_camera:
    rts

; ------------------------------------------------------------------------------
; RENDER 24x24 ASCII CORGI SPRITES TO OAM (Sprites 1..9: OAM $0204 - $0227)
; Note: Sprite 0 ($0200) is reserved for Sprite 0 Hit!
; ------------------------------------------------------------------------------
render_dog_sprites:
    ; Compute dog screen X = dog_x - cam_x
    lda dog_x_lo
    sec
    sbc cam_x_lo
    sta dog_screen_x

    ; Base tile calculation: dog_anim_frame * 9
    lda dog_anim_frame
    asl a
    asl a
    asl a
    clc
    adc dog_anim_frame
    sta math_temp

    lda dog_dir
    beq :+
    jmp @render_left
:

    ; --- FACING RIGHT (Sprites 1..9: bytes 4 to 39) ---
    ; Row 0: Top row (Tiles 0, 1, 2)
    lda dog_y
    sta OAM_BUFFER + 4
    sta OAM_BUFFER + 8
    sta OAM_BUFFER + 12
    lda #0
    sta OAM_BUFFER + 6
    sta OAM_BUFFER + 10
    sta OAM_BUFFER + 14

    lda math_temp
    sta OAM_BUFFER + 5
    clc
    adc #1
    sta OAM_BUFFER + 9
    clc
    adc #1
    sta OAM_BUFFER + 13

    lda dog_screen_x
    sta OAM_BUFFER + 7
    clc
    adc #8
    sta OAM_BUFFER + 11
    clc
    adc #8
    sta OAM_BUFFER + 15

    ; Row 1: Middle row (Tiles 3, 4, 5)
    lda dog_y
    clc
    adc #8
    sta OAM_BUFFER + 16
    sta OAM_BUFFER + 20
    sta OAM_BUFFER + 24
    lda #0
    sta OAM_BUFFER + 18
    sta OAM_BUFFER + 22
    sta OAM_BUFFER + 26

    lda math_temp
    clc
    adc #3
    sta OAM_BUFFER + 17
    clc
    adc #1
    sta OAM_BUFFER + 21
    clc
    adc #1
    sta OAM_BUFFER + 25

    lda dog_screen_x
    sta OAM_BUFFER + 19
    clc
    adc #8
    sta OAM_BUFFER + 23
    clc
    adc #8
    sta OAM_BUFFER + 27

    ; Row 2: Bottom row (Tiles 6, 7, 8)
    lda dog_y
    clc
    adc #16
    sta OAM_BUFFER + 28
    sta OAM_BUFFER + 32
    sta OAM_BUFFER + 36
    lda #0
    sta OAM_BUFFER + 30
    sta OAM_BUFFER + 34
    sta OAM_BUFFER + 38

    lda math_temp
    clc
    adc #6
    sta OAM_BUFFER + 29
    clc
    adc #1
    sta OAM_BUFFER + 33
    clc
    adc #1
    sta OAM_BUFFER + 37

    lda dog_screen_x
    sta OAM_BUFFER + 31
    clc
    adc #8
    sta OAM_BUFFER + 35
    clc
    adc #8
    sta OAM_BUFFER + 39
    jmp @render_bubble

@render_left:
    ; --- FACING LEFT (Flip X %01000000, swap col 0 and 2) ---
    ; Row 0
    lda dog_y
    sta OAM_BUFFER + 4
    sta OAM_BUFFER + 8
    sta OAM_BUFFER + 12
    lda #%01000000
    sta OAM_BUFFER + 6
    sta OAM_BUFFER + 10
    sta OAM_BUFFER + 14

    lda math_temp
    clc
    adc #2              ; Col 0 gets Tile + 2
    sta OAM_BUFFER + 5
    sec
    sbc #1              ; Col 1 gets Tile + 1
    sta OAM_BUFFER + 9
    sec
    sbc #1              ; Col 2 gets Tile + 0
    sta OAM_BUFFER + 13

    lda dog_screen_x
    sta OAM_BUFFER + 7
    clc
    adc #8
    sta OAM_BUFFER + 11
    clc
    adc #8
    sta OAM_BUFFER + 15

    ; Row 1
    lda dog_y
    clc
    adc #8
    sta OAM_BUFFER + 16
    sta OAM_BUFFER + 20
    sta OAM_BUFFER + 24
    lda #%01000000
    sta OAM_BUFFER + 18
    sta OAM_BUFFER + 22
    sta OAM_BUFFER + 26

    lda math_temp
    clc
    adc #5              ; Col 0 gets Tile + 5
    sta OAM_BUFFER + 17
    sec
    sbc #1
    sta OAM_BUFFER + 21
    sec
    sbc #1
    sta OAM_BUFFER + 25

    lda dog_screen_x
    sta OAM_BUFFER + 19
    clc
    adc #8
    sta OAM_BUFFER + 23
    clc
    adc #8
    sta OAM_BUFFER + 27

    ; Row 2
    lda dog_y
    clc
    adc #16
    sta OAM_BUFFER + 28
    sta OAM_BUFFER + 32
    sta OAM_BUFFER + 36
    lda #%01000000
    sta OAM_BUFFER + 30
    sta OAM_BUFFER + 34
    sta OAM_BUFFER + 38

    lda math_temp
    clc
    adc #8              ; Col 0 gets Tile + 8
    sta OAM_BUFFER + 29
    sec
    sbc #1
    sta OAM_BUFFER + 33
    sec
    sbc #1
    sta OAM_BUFFER + 37

    lda dog_screen_x
    sta OAM_BUFFER + 31
    clc
    adc #8
    sta OAM_BUFFER + 35
    clc
    adc #8
    sta OAM_BUFFER + 39

@render_bubble:
    ; Sprite 10 (OAM $0228 - $022B): Speech bubble / Zzz
    lda bark_timer
    beq @check_sleep_bubble
    lda dog_y
    sec
    sbc #8
    sta OAM_BUFFER + 40
    lda #$2D            ; "HAU!" sprite tile
    sta OAM_BUFFER + 41
    lda #%00000010      ; Palette 2 (Gold)
    sta OAM_BUFFER + 42
    lda dog_screen_x
    clc
    adc #8
    sta OAM_BUFFER + 43
    rts

@check_sleep_bubble:
    lda game_mode
    cmp #MODE_SLEEP
    bne @hide_bubble
    lda dog_y
    sec
    sbc #8
    sta OAM_BUFFER + 40
    lda #$2E            ; "Zzz" sprite tile
    sta OAM_BUFFER + 41
    lda #%00000001      ; Palette 1 (Cyan)
    sta OAM_BUFFER + 42
    lda dog_screen_x
    clc
    adc #8
    sta OAM_BUFFER + 43
    rts

@hide_bubble:
    lda #$FF
    sta OAM_BUFFER + 40
    rts
