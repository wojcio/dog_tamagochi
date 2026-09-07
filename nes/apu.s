; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; apu.s: NES Sound Synthesizer Engine (Square 1, Square 2, Triangle, Noise)
; ==============================================================================

init_apu:
    ; Enable Square 1, Square 2, Triangle, Noise
    lda #%00001111
    sta APU_STATUS

    ; Set 4-step sequence mode, inhibit IRQ ($4017)
    lda #$40
    sta APU_FRAME

    ; Silence all channels initially
    lda #$30            ; Volume 0, disable envelope
    sta SQ1_VOL
    sta SQ2_VOL
    sta NOISE_VOL

    lda #$80            ; Triangle linear counter halt
    sta TRI_LINEAR

    lda #0
    sta sfx_playing
    sta sfx_timer
    sta sfx_step
    rts

; Trigger a sound effect
; Input: A = SFX ID (SFX_BARK, SFX_JUMP, SFX_EAT, SFX_SLEEP, etc.)
play_sfx:
    sta sfx_playing
    lda #0
    sta sfx_step
    lda #1
    sta sfx_timer       ; Begin on next update
    rts

; Update APU sound effects (called once every 60Hz frame)
update_apu:
    lda sfx_playing
    bne @has_sfx
    rts

@has_sfx:
    dec sfx_timer
    beq @advance_step
    rts

@advance_step:
    lda sfx_playing
    cmp #SFX_BARK
    bne @not_bark
    jmp @do_bark
@not_bark:
    cmp #SFX_JUMP
    bne @not_jump
    jmp @do_jump
@not_jump:
    cmp #SFX_EAT
    bne @not_eat
    jmp @do_eat
@not_eat:
    cmp #SFX_SLEEP
    bne @not_sleep
    jmp @do_sleep
@not_sleep:
    cmp #SFX_TRICK
    bne @not_trick
    jmp @do_trick
@not_trick:
    jmp @stop_sfx

; ------------------------------------------------------------------------------
; SFX: BARK ("HAU! HAU!") - 2-step punchy pitch drop
; ------------------------------------------------------------------------------
@do_bark:
    lda sfx_step
    bne @bark_step1

    ; Step 0: High pitch bite
    lda #%10011111      ; Duty 50%, constant volume 15 (max)
    sta SQ1_VOL
    lda #$90            ; High frequency
    sta SQ1_LO
    lda #$01
    sta SQ1_HI
    lda #$08            ; Duration: 8 frames
    sta sfx_timer
    inc sfx_step
    rts

@bark_step1:
    cmp #1
    beq @bark_step1_exec
    jmp @stop_sfx
@bark_step1_exec:
    ; Step 1: Lower pitch throat sound
    lda #%10011010      ; Volume 10
    sta SQ1_VOL
    lda #$E0            ; Lower frequency
    sta SQ1_LO
    lda #$02
    sta SQ1_HI
    lda #$06            ; Duration: 6 frames
    sta sfx_timer
    inc sfx_step
    rts

; ------------------------------------------------------------------------------
; SFX: JUMP - Smooth rising sweep slide
; ------------------------------------------------------------------------------
@do_jump:
    lda sfx_step
    beq @jump_step0
    jmp @stop_sfx

@jump_step0:
    lda #%10011011      ; Duty 50%, volume 11
    sta SQ1_VOL
    lda #%10001110      ; Hardware sweep: enable, period 1, shift 6 (pitch rises!)
    sta SQ1_SWEEP
    lda #$80
    sta SQ1_LO
    lda #$03
    sta SQ1_HI
    lda #$0C            ; Duration: 12 frames
    sta sfx_timer
    inc sfx_step
    rts

; ------------------------------------------------------------------------------
; SFX: EAT / BONE PICKUP - Ascending 3-tone arpeggio (C5 -> E5 -> G5)
; ------------------------------------------------------------------------------
@do_eat:
    lda sfx_step
    cmp #0
    beq @eat_note0
    cmp #1
    beq @eat_note1
    cmp #2
    beq @eat_note2
    jmp @stop_sfx

@eat_note0:
    lda #%10011100      ; Square 2, volume 12
    sta SQ2_VOL
    lda #$D5            ; C5 note
    sta SQ2_LO
    lda #$00
    sta SQ2_HI
    lda #$05
    sta sfx_timer
    inc sfx_step
    rts

@eat_note1:
    lda #$A9            ; E5 note
    sta SQ2_LO
    lda #$00
    sta SQ2_HI
    lda #$05
    sta sfx_timer
    inc sfx_step
    rts

@eat_note2:
    lda #$8E            ; G5 note
    sta SQ2_LO
    lda #$00
    sta SQ2_HI
    lda #$07
    sta sfx_timer
    inc sfx_step
    rts

; ------------------------------------------------------------------------------
; SFX: SLEEP - Soft descending Triangle waves
; ------------------------------------------------------------------------------
@do_sleep:
    lda sfx_step
    cmp #0
    beq @sleep_n0
    cmp #1
    beq @sleep_n1
    cmp #2
    beq @sleep_n2
    jmp @stop_sfx

@sleep_n0:
    lda #%11111111      ; Triangle enable
    sta TRI_LINEAR
    lda #$A0            ; Note 1
    sta TRI_LO
    lda #$01
    sta TRI_HI
    lda #$12            ; Duration 18 frames
    sta sfx_timer
    inc sfx_step
    rts

@sleep_n1:
    lda #$F0            ; Note 2 (lower)
    sta TRI_LO
    lda #$01
    sta TRI_HI
    lda #$14
    sta sfx_timer
    inc sfx_step
    rts

@sleep_n2:
    lda #$50            ; Note 3 (even lower)
    sta TRI_LO
    lda #$02
    sta TRI_HI
    lda #$18
    sta sfx_timer
    inc sfx_step
    rts

; ------------------------------------------------------------------------------
; SFX: TRICK - Cheerful rapid double chord
; ------------------------------------------------------------------------------
@do_trick:
    lda sfx_step
    cmp #0
    beq @trick_n0
    cmp #1
    beq @trick_n1
    jmp @stop_sfx

@trick_n0:
    lda #%10011100
    sta SQ1_VOL
    lda #$70
    sta SQ1_LO
    lda #$00
    sta SQ1_HI
    lda #$06
    sta sfx_timer
    inc sfx_step
    rts

@trick_n1:
    lda #$38            ; Octave jump
    sta SQ1_LO
    lda #$00
    sta SQ1_HI
    lda #$0A
    sta sfx_timer
    inc sfx_step
    rts

; Silence channels when sound finishes
@stop_sfx:
    lda #$30            ; Silence Square 1
    sta SQ1_VOL
    lda #$08            ; Disable sweep
    sta SQ1_SWEEP

    lda #$30            ; Silence Square 2
    sta SQ2_VOL

    lda #$80            ; Silence Triangle
    sta TRI_LINEAR

    lda #0
    sta sfx_playing
    sta sfx_step
    sta sfx_timer
    rts
