; ==============================================================================
; 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES EDITION (CA65)
; constants.inc: PPU, APU, Hardware Registers, Controller, and World Constants
; ==============================================================================

; --- PPU REGISTERS ---
PPUCTRL   = $2000
PPUMASK   = $2001
PPUSTATUS = $2002
OAMADDR   = $2003
OAMDATA   = $2004
PPUSCROLL = $2005
PPUADDR   = $2006
PPUDATA   = $2007
OAMDMA    = $4014

; --- APU REGISTERS ---
SQ1_VOL    = $4000
SQ1_SWEEP  = $4001
SQ1_LO     = $4002
SQ1_HI     = $4003

SQ2_VOL    = $4004
SQ2_SWEEP  = $4005
SQ2_LO     = $4006
SQ2_HI     = $4007

TRI_LINEAR = $4008
TRI_LO     = $400A
TRI_HI     = $400B

NOISE_VOL  = $400C
NOISE_LO   = $400E
NOISE_HI   = $400F

DMC_FREQ   = $4010
DMC_RAW    = $4011
DMC_START  = $4012
DMC_LEN    = $4013

APU_STATUS = $4015
APU_FRAME  = $4017

; --- CONTROLLER REGISTERS & BUTTON MASKS ---
JOYPAD1    = $4016
JOYPAD2    = $4017

BTN_A      = %10000000
BTN_B      = %01000000
BTN_SELECT = %00100000
BTN_START  = %00010000
BTN_UP     = %00001000
BTN_DOWN   = %00000100
BTN_LEFT   = %00000010
BTN_RIGHT  = %00000001

; --- GAME & PHYSICS CONSTANTS ---
GRAVITY         = 1
MAX_FALL_SPEED  = 4
JUMP_VELOCITY   = 5
RUN_SPEED       = 2

GROUND_Y        = 152   ; Dog bottom (Y+24) lands on row 22 (Y=176)
BUDA_X_MIN      = 16    ; Buda entrance area
BUDA_X_MAX      = 60

WORLD_WIDTH     = 1024  ; 4 Biomes (4 x 256 px)
MAX_DOG_X       = 980
MAX_CAM_X       = 768   ; 1024 - 256

MAX_NEED_VAL    = 100

; Game modes
MODE_PLAY       = 0
MODE_SLEEP      = 1
MODE_PAUSED     = 2

; Sound effect IDs
SFX_NONE        = 0
SFX_BARK        = 1
SFX_JUMP        = 2
SFX_EAT         = 3
SFX_SLEEP       = 4
SFX_WHINE       = 5
SFX_TRICK       = 6
