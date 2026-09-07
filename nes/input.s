; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; input.s: Controller 1 Strobe, Read, and Edge-Triggered Button Detection
; ==============================================================================

; Reads Controller 1 into gamepad_cur, and calculates gamepad_press
; gamepad_press contains buttons that were JUST pressed this frame.
read_controller:
    ; Save previous buttons
    lda gamepad_cur
    sta gamepad_prev

    ; Latch controller state: write 1 then 0 to $4016
    lda #$01
    sta JOYPAD1
    lda #$00
    sta JOYPAD1

    ; Read 8 button states serially into A
    ldx #$08
@read_loop:
    lda JOYPAD1
    lsr a           ; Bit 0 into Carry
    rol gamepad_cur ; Rotate Carry into gamepad_cur
    dex
    bne @read_loop

    ; Calculate newly pressed buttons: cur AND (NOT prev)
    lda gamepad_prev
    eor #$FF            ; Invert prev
    and gamepad_cur     ; AND with cur
    sta gamepad_press   ; Buttons that transitioned 0 -> 1

    rts
