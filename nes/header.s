; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; header.s: 16-Byte iNES Header for Mapper 0 (NROM-256)
; ==============================================================================

.segment "HEADER"

    .byte "NES", $1A    ; Magic string identifying iNES ROM
    .byte 2             ; 2 x 16KB PRG ROM = 32KB
    .byte 1             ; 1 x 8KB CHR ROM = 8KB
    .byte %00000001     ; Mapper 0, Vertical Mirroring (horizontal scrolling support)
    .byte %00000000     ; Mapper 0, NES 2.0 flags disabled
    .byte $00, $00, $00, $00, $00, $00, $00, $00 ; Padding bytes
