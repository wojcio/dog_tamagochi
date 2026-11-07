; ==============================================================================
; NESLIB for CC65 - Core NES Runtime Library with Fast Assembly VBlank Streaming
; ==============================================================================

    .export _ppu_wait_nmi, _ppu_wait_frame
    .export _ppu_off, _ppu_on_all, _ppu_on_bg, _ppu_on_spr, _ppu_mask
    .export _oam_clear, _oam_spr, _oam_meta_spr, _oam_hide_rest
    .export _pad_poll, _pad_trigger, _pad_state
    .export _scroll, _vram_adr, _vram_put, _vram_fill, _vram_inc, _vram_write, _vram_read
    .export _pal_all, _pal_bg, _pal_spr, _pal_col, _pal_clear
    .export _sfx_play
    .export _queue_col_stream
    .export _hud_invalidate

    .import _main
    .import _world_cols_bitmap
    .import _world_attr_cols
    .import _stat_hunger, _stat_energy, _stat_happy, _stat_bones
    .import popa, popax
    .importzp sp, sreg, ptr1, ptr2, tmp1, tmp2

PPUCTRL   = $2000
PPUMASK   = $2001
PPUSTATUS = $2002
OAMADDR   = $2003
OAMDATA   = $2004
PPUSCROLL = $2005
PPUADDR   = $2006
PPUDATA   = $2007

OAMDMA    = $4014
JOYPAD1   = $4016
JOYPAD2   = $4017

APU_PULSE1_CTRL = $4000
APU_PULSE1_RAMP = $4001
APU_PULSE1_FTBL = $4002
APU_PULSE1_CTBL = $4003
APU_STATUS      = $4015
APU_FRAME       = $4017

OAM_BUF   = $0200

; ------------------------------------------------------------------------------
; ZERO PAGE VARIABLES FOR NESLIB
; ------------------------------------------------------------------------------
.segment "ZEROPAGE"
nmi_flag:       .res 1
frame_cnt:      .res 1
ppu_ctrl_val:   .res 1
ppu_mask_val:   .res 1
scroll_x_lo:    .res 1
scroll_x_hi:    .res 1
scroll_y:       .res 1
pad_cur:        .res 2
pad_prev:       .res 2
pad_trig:       .res 2
pal_dirty:      .res 1
oam_idx:        .res 1
sfx_timer:      .res 1

col_draw_flag:  .res 1
col_draw_id:    .res 1
col_dest_hi:    .res 1
col_dest_lo:    .res 1
attr_dest_lo:   .res 1
attr_dest_hi:   .res 1
attr_ptr:       .res 2

; HUD change-detection cache (drawn only when a stat actually changes)
hud_prev:       .res 4      ; hunger, energy, happy, bones from last paint
hud_fill:       .res 1
hud_addr:       .res 1
hud_tens:       .res 1
hud_ones:       .res 1

.segment "BSS"
pal_buf:        .res 32

; ------------------------------------------------------------------------------
; INES HEADER (16 bytes)
; ------------------------------------------------------------------------------
.segment "HEADER"
    .byte "NES", $1A
    .byte 2             ; 2 * 16KB = 32KB PRG ROM
    .byte 1             ; 1 * 8KB = 8KB CHR ROM
    .byte %00000001     ; Mapper 0, Vertical Mirroring
    .byte %00000000     ; Mapper 0
    .byte 0,0,0,0,0,0,0,0

; ------------------------------------------------------------------------------
; STARTUP CODE (Reset Handler & CC65 C Initialization)
; ------------------------------------------------------------------------------
.segment "STARTUP"
reset_handler:
    sei
    cld
    ldx #$40
    stx APU_FRAME
    ldx #$FF
    txs
    inx                 ; X = 0
    stx PPUCTRL
    stx PPUMASK
    stx $4010           ; Disable DMC IRQ

    ; Warmup VBlank 1
:   bit PPUSTATUS
    bpl :-

    ; Clear RAM ($0000-$07FF) except stack
    txa
:   sta $0000, x
    sta $0200, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    inx
    bne :-

    ; Warmup VBlank 2
:   bit PPUSTATUS
    bpl :-

    ; Initialize CC65 C Stack to $07FF
    lda #$FF
    sta sp
    lda #$07
    sta sp+1

    ; Clear OAM
    jsr _oam_clear

    ; Init APU sound
    lda #$0F
    sta APU_STATUS

    ; Keep PPU rendering and NMI OFF until ppu_on_all()
    lda #0
    sta ppu_ctrl_val
    sta PPUCTRL
    sta ppu_mask_val
    sta PPUMASK

    ; Run C main()
    jsr _main

@halt:
    jmp @halt

; ------------------------------------------------------------------------------
; NMI HANDLER
; ------------------------------------------------------------------------------
.segment "CODE"
nmi_handler:
    pha
    txa
    pha
    tya
    pha

    ; 1. Fast OAM DMA upload ($0200 -> PPU OAM)
    lda #0
    sta OAMADDR
    lda #>OAM_BUF
    sta OAMDMA

    ; 2. Palettes update if dirty
    lda pal_dirty
    beq @skip_pal
    lda PPUSTATUS
    lda #$3F
    sta PPUADDR
    lda #$00
    sta PPUADDR
    ldx #0
:   lda pal_buf, x
    sta PPUDATA
    inx
    cpx #32
    bne :-
    lda #0
    sta pal_dirty
@skip_pal:

    ; 3. Column Streaming (if camera crossed an 8-pixel column boundary)
    lda col_draw_flag
    bne :+
    jmp @skip_col
:

    ; Set PPUCTRL with bit 2 = 1 (+32 vertical increment)
    lda ppu_ctrl_val
    ora #%00000100
    sta PPUCTRL

    ; Source pointer for this column's 30-row bitmap run
    ldx col_draw_id
    lda col_offset_lo, x
    clc
    adc #<_world_cols_bitmap
    sta ptr1
    lda col_offset_hi, x
    adc #>_world_cols_bitmap
    sta ptr1+1

    ; Segment 1: rows 0-1 (HUD frame + biome title). Titles are baked per
    ; screen into the column data, so streaming them updates the biome name.
    lda col_dest_hi
    sta PPUADDR
    lda col_dest_lo
    sta PPUADDR

    ldy #0
@stream_seg1:
    lda (ptr1), y
    sta PPUDATA
    iny
    cpy #2
    bne @stream_seg1

    ; Segment 2: rows 4-29. Rows 2-3 are skipped: the live meters and bone
    ; counter are painted there by hud_refresh and must not be overwritten.
    lda col_dest_hi
    sta PPUADDR
    lda col_dest_lo
    clc
    adc #128                ; 4 rows x 32 (column offset never carries past $FF)
    sta PPUADDR

    ldy #4
@stream_seg2:
    lda (ptr1), y
    sta PPUDATA
    iny
    cpy #30
    bne @stream_seg2

    lda #0
    sta col_draw_flag

    ; Restore +1 increment
    lda ppu_ctrl_val
    sta PPUCTRL

    ; Check if attribute column needs update: every 4 columns (col_draw_id & 3 == 0)
    lda col_draw_id
    and #$03
    bne @skip_attr

    ; attr_col = (col_draw_id >> 2) & 7
    lda col_draw_id
    lsr
    lsr
    and #$07
    ora #$C0
    sta attr_dest_lo

    ; offset in world_attr_cols = (col_draw_id & $FC) << 1
    lda col_draw_id
    and #$FC
    asl
    clc
    adc #<_world_attr_cols
    sta attr_ptr
    lda #0
    adc #>_world_attr_cols
    sta attr_ptr+1

    ; attr_dest_hi: if col_dest_hi == $24 then $27 else $23
    lda col_dest_hi
    cmp #$24
    beq :+
    lda #$23
    bne :++
:   lda #$27
:   sta attr_dest_hi

    ldy #0
@attr_loop:
    lda PPUSTATUS
    lda attr_dest_hi
    sta PPUADDR
    lda attr_dest_lo
    sta PPUADDR
    lda (attr_ptr), y
    sta PPUDATA
    lda attr_dest_lo
    clc
    adc #8
    sta attr_dest_lo
    iny
    cpy #8
    bne @attr_loop

@skip_attr:

@skip_col:
    ; 3b. HUD meters & bone counter (writes only on change)
    jsr hud_refresh

    ; 4. Update PPUCTRL with scroll nametable
    lda ppu_ctrl_val
    and #%11111100
    sta tmp1
    lda scroll_x_hi
    and #$01
    ora tmp1
    sta PPUCTRL

    ; 5. Set hardware PPU scroll
    lda PPUSTATUS
    lda scroll_x_lo
    sta PPUSCROLL
    lda scroll_y
    sta PPUSCROLL

    ; 6. APU SFX update
    lda sfx_timer
    beq :+
    dec sfx_timer
    bne :+
    lda #$30
    sta APU_PULSE1_CTRL ; Silence SFX
:

    inc frame_cnt
    lda #1
    sta nmi_flag

    pla
    tay
    pla
    tax
    pla
    rti

irq_handler:
    rti

; ------------------------------------------------------------------------------
; COLUMN STREAMING INTERFACE
; ------------------------------------------------------------------------------
_queue_col_stream:
    sta col_draw_id
    and #31
    sta col_dest_lo
    lda col_draw_id
    and #32
    beq :+
    lda #$24
    sta col_dest_hi
    jmp @set_flag
:   lda #$20
    sta col_dest_hi
@set_flag:
    lda #1
    sta col_draw_flag
    rts

; ------------------------------------------------------------------------------
; HUD REFRESH: paints the three meters and the bone counter into BOTH
; nametables, but only when a value actually changed (VBlank-budget friendly).
; Tiles: $7A filled cell, $7B empty cell, $7C right border, $84+'0' digits.
; ------------------------------------------------------------------------------
_hud_invalidate:
    lda #0
    sta hud_prev+0
    sta hud_prev+1
    sta hud_prev+2
    sta hud_prev+3
    rts

hud_refresh:
    lda _stat_hunger
    cmp hud_prev+0
    beq @nrg
    sta hud_prev+0
    jsr @calc_fill
    sta hud_fill
    lda #$48                ; row 2, col 8
    sta hud_addr
    jsr @write_bar
@nrg:
    lda _stat_energy
    cmp hud_prev+1
    beq @hpy
    sta hud_prev+1
    jsr @calc_fill
    sta hud_fill
    lda #$56                ; row 2, col 22
    sta hud_addr
    jsr @write_bar
@hpy:
    lda _stat_happy
    cmp hud_prev+2
    beq @bones
    sta hud_prev+2
    jsr @calc_fill
    sta hud_fill
    lda #$68                ; row 3, col 8
    sta hud_addr
    jsr @write_bar
@bones:
    lda _stat_bones
    cmp hud_prev+3
    beq @done
    sta hud_prev+3
    ldx #$FF                ; divide by 10: X = tens, A = ones
    sec
@div10:
    inx
    sbc #10
    bcs @div10
    adc #10                 ; restore remainder
    clc
    adc #$84
    sta hud_ones
    txa
    clc
    adc #$84
    sta hud_tens

    lda #$20
    sta PPUADDR
    lda #$76                ; row 3, col 22
    sta PPUADDR
    lda hud_tens
    sta PPUDATA
    lda hud_ones
    sta PPUDATA
    lda #$24
    sta PPUADDR
    lda #$76
    sta PPUADDR
    lda hud_tens
    sta PPUDATA
    lda hud_ones
    sta PPUDATA
@done:
    rts

; A = stat 0..100 -> A = bar fill 0..5
@calc_fill:
    ldx #0
@cf:
    cmp #20
    bcc @cf_done
    sec
    sbc #20
    inx
    jmp @cf
@cf_done:
    txa
    rts

; Writes a 6-tile bar (5 cells + right border) at hud_addr in both NTs.
; In: hud_fill (0..5), hud_addr (nametable column offset of the row).
@write_bar:
    lda #$20
    jsr @wb_nt
    lda #$24
@wb_nt:
    sta PPUADDR
    lda hud_addr
    sta PPUADDR
    ldx #0
@wb_cell:
    txa
    cmp hud_fill
    bcs @wb_empty
    lda #$7A
    sta PPUDATA
    jmp @wb_next
@wb_empty:
    lda #$7B
    sta PPUDATA
@wb_next:
    inx
    cpx #5
    bne @wb_cell
    lda #$7C                ; right border
    sta PPUDATA
    rts

; ------------------------------------------------------------------------------
; PPU CONTROL FUNCTIONS
; ------------------------------------------------------------------------------
_ppu_wait_nmi:
    lda #0
    sta nmi_flag
:   lda nmi_flag
    beq :-
    rts

_ppu_wait_frame:
    jmp _ppu_wait_nmi

_ppu_off:
    lda #0
    sta PPUCTRL
    sta ppu_ctrl_val
    sta PPUMASK
    sta ppu_mask_val
    rts

_ppu_on_all:
    lda #%10001000
    sta ppu_ctrl_val
    sta PPUCTRL
    lda #%00011110      ; Show BG & Sprites
    sta ppu_mask_val
    sta PPUMASK
    rts

_ppu_on_bg:
    lda #%10001000
    sta ppu_ctrl_val
    sta PPUCTRL
    lda #%00001110
    sta ppu_mask_val
    sta PPUMASK
    rts

_ppu_on_spr:
    lda #%10001000
    sta ppu_ctrl_val
    sta PPUCTRL
    lda #%00010110
    sta ppu_mask_val
    sta PPUMASK
    rts

_ppu_mask:
    sta ppu_mask_val
    sta PPUMASK
    rts

; ------------------------------------------------------------------------------
; SCROLL FUNCTION: scroll(unsigned int x, unsigned int y)
; ------------------------------------------------------------------------------
_scroll:
    sta scroll_y        ; low byte of y (fastcall: y in AX)
    jsr popax           ; x in AX
    sta scroll_x_lo
    stx scroll_x_hi
    rts

; ------------------------------------------------------------------------------
; VRAM FUNCTIONS
; ------------------------------------------------------------------------------
_vram_adr:
    stx PPUADDR
    sta PPUADDR
    rts

_vram_put:
    sta PPUDATA
    rts

_vram_fill:
    sta ptr1
    stx ptr1+1
    jsr popa
    sta tmp1
    ldx ptr1+1
    ldy ptr1
    beq :+
    inx
:   lda tmp1
@loop:
    sta PPUDATA
    dey
    bne @loop
    dex
    bne @loop
    rts

_vram_inc:
    tax
    beq @horz
    lda ppu_ctrl_val
    ora #%00000100
    sta ppu_ctrl_val
    sta PPUCTRL
    rts
@horz:
    lda ppu_ctrl_val
    and #%11111011
    sta ppu_ctrl_val
    sta PPUCTRL
    rts

_vram_write:
    sta tmp1            ; size low
    stx tmp2            ; size high
    jsr popax           ; src on stack
    sta ptr1
    stx ptr1+1
    ldy #0
@wr_loop:
    lda tmp1
    ora tmp2
    beq @done
    lda (ptr1), y
    sta PPUDATA
    iny
    bne :+
    inc ptr1+1
:   lda tmp1
    bne :+
    dec tmp2
:   dec tmp1
    jmp @wr_loop
@done:
    rts

_vram_read:
    sta tmp1
    stx tmp2
    jsr popax
    sta ptr1
    stx ptr1+1
    lda PPUDATA         ; dummy read
    ldy #0
@rd_loop:
    lda tmp1
    ora tmp2
    beq @done_rd
    lda PPUDATA
    sta (ptr1), y
    iny
    bne :+
    inc ptr1+1
:   lda tmp1
    bne :+
    dec tmp2
:   dec tmp1
    jmp @rd_loop
@done_rd:
    rts

; ------------------------------------------------------------------------------
; PALETTE FUNCTIONS
; ------------------------------------------------------------------------------
_pal_all:
    sta ptr1
    stx ptr1+1
    ldy #0
:   lda (ptr1), y
    sta pal_buf, y
    iny
    cpy #32
    bne :-
    lda #1
    sta pal_dirty

    lda ppu_mask_val
    bne :+
    lda PPUSTATUS
    lda #$3F
    sta PPUADDR
    lda #$00
    sta PPUADDR
    ldy #0
@wr_all:
    lda pal_buf, y
    sta PPUDATA
    iny
    cpy #32
    bne @wr_all
    lda #0
    sta pal_dirty
:   rts

_pal_bg:
    sta ptr1
    stx ptr1+1
    ldy #0
:   lda (ptr1), y
    sta pal_buf, y
    iny
    cpy #16
    bne :-
    lda #1
    sta pal_dirty

    lda ppu_mask_val
    bne :+
    lda PPUSTATUS
    lda #$3F
    sta PPUADDR
    lda #$00
    sta PPUADDR
    ldy #0
@wr_bg:
    lda pal_buf, y
    sta PPUDATA
    iny
    cpy #16
    bne @wr_bg
    lda #0
    sta pal_dirty
:   rts

_pal_spr:
    sta ptr1
    stx ptr1+1
    ldy #0
:   lda (ptr1), y
    sta pal_buf + 16, y
    iny
    cpy #16
    bne :-
    lda #1
    sta pal_dirty

    lda ppu_mask_val
    bne :+
    lda PPUSTATUS
    lda #$3F
    sta PPUADDR
    lda #$10
    sta PPUADDR
    ldy #0
@wr_spr:
    lda pal_buf + 16, y
    sta PPUDATA
    iny
    cpy #16
    bne @wr_spr
    lda #0
    sta pal_dirty
:   rts

_pal_col:
    tay                 ; color
    jsr popa            ; index
    tax
    tya
    sta pal_buf, x
    lda #1
    sta pal_dirty
    rts

_pal_clear:
    lda #$0F
    ldx #0
:   sta pal_buf, x
    inx
    cpx #32
    bne :-
    lda #1
    sta pal_dirty
    rts

; ------------------------------------------------------------------------------
; OAM SPRITE FUNCTIONS
; ------------------------------------------------------------------------------
_oam_clear:
    lda #$FF
    ldx #0
:   sta OAM_BUF, x
    inx
    inx
    inx
    inx
    bne :-
    stx oam_idx
    rts

_oam_spr:
    sta tmp1
    jsr popa            ; tile
    sta tmp2
    jsr popa            ; y
    sta ptr1
    jsr popa            ; x
    sta ptr2

    ldx oam_idx
    cpx #252
    bcs @spr_overflow
    lda ptr1            ; y
    sta OAM_BUF + 0, x
    lda tmp2            ; tile
    sta OAM_BUF + 1, x
    lda tmp1            ; attr
    sta OAM_BUF + 2, x
    lda ptr2            ; x
    sta OAM_BUF + 3, x
    txa
    clc
    adc #4
    sta oam_idx
    tax
    rts
@spr_overflow:
    lda oam_idx
    rts

_oam_meta_spr:
    sta ptr1
    stx ptr1+1
    jsr popa            ; y
    sta tmp1
    jsr popa            ; x
    sta tmp2

    ldx oam_idx
    ldy #0
@meta_loop:
    lda (ptr1), y       ; dx or 128 terminator
    cmp #128
    beq @meta_done
    clc
    adc tmp2            ; spr_x = x + dx
    sta ptr2

    iny
    lda (ptr1), y       ; dy
    clc
    adc tmp1            ; spr_y = y + dy
    sta OAM_BUF + 0, x

    iny
    lda (ptr1), y       ; tile
    sta OAM_BUF + 1, x

    iny
    lda (ptr1), y       ; attr
    sta OAM_BUF + 2, x

    lda ptr2
    sta OAM_BUF + 3, x  ; x

    iny
    inx
    inx
    inx
    inx
    beq @meta_done
    jmp @meta_loop

@meta_done:
    stx oam_idx
    txa
    rts

_oam_hide_rest:
    tax
    lda #$FF
:   sta OAM_BUF, x
    inx
    inx
    inx
    inx
    bne :-
    rts

; ------------------------------------------------------------------------------
; JOYPAD INPUT POLLING
; ------------------------------------------------------------------------------
_pad_poll:
    tax                 ; pad number (0 or 1)
    lda pad_cur, x
    sta pad_prev, x

    lda #1
    sta JOYPAD1
    lda #0
    sta JOYPAD1

    ldy #8
@pad_loop:
    lda JOYPAD1, x
    and #$03
    cmp #$01
    ror tmp1
    dey
    bne @pad_loop

    lda tmp1
    sta pad_cur, x

    ; Compute trigger = (cur ^ prev) & cur
    eor pad_prev, x
    and pad_cur, x
    sta pad_trig, x

    lda pad_cur, x
    rts

_pad_trigger:
    tax
    lda pad_trig, x
    rts

_pad_state:
    tax
    lda pad_cur, x
    rts

; ------------------------------------------------------------------------------
; APU SOUND SYNTHESIZER
; ------------------------------------------------------------------------------
_sfx_play:
    cmp #1              ; 1 = Bark
    bne @check_jump_sfx
    lda #%10011111      ; Duty 50%, volume 15
    sta APU_PULSE1_CTRL
    lda #%10001011      ; Sweep down
    sta APU_PULSE1_RAMP
    lda #$40
    sta APU_PULSE1_FTBL
    lda #$08
    sta APU_PULSE1_CTBL
    lda #15
    sta sfx_timer
    rts

@check_jump_sfx:
    cmp #2              ; 2 = Jump
    bne @check_eat_sfx
    lda #%10011100      ; Duty 50%, volume 12
    sta APU_PULSE1_CTRL
    lda #%10000010      ; Sweep up
    sta APU_PULSE1_RAMP
    lda #$90
    sta APU_PULSE1_FTBL
    lda #$08
    sta APU_PULSE1_CTBL
    lda #12
    sta sfx_timer
    rts

@check_eat_sfx:
    cmp #3              ; 3 = Eat / Bone
    bne @done_sfx
    lda #%10001111
    sta APU_PULSE1_CTRL
    lda #%00000000
    sta APU_PULSE1_RAMP
    lda #$20
    sta APU_PULSE1_FTBL
    lda #$08
    sta APU_PULSE1_CTBL
    lda #10
    sta sfx_timer

@done_sfx:
    rts

; ------------------------------------------------------------------------------
; COLUMN OFFSET LOOKUP TABLES (128 entries for col * 30)
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

; ------------------------------------------------------------------------------
; HARDWARE VECTORS & CHR ROM
; ------------------------------------------------------------------------------
.segment "VECTORS"
    .word nmi_handler
    .word reset_handler
    .word irq_handler

.segment "CHARS"
    .incbin "graphics2.chr"
