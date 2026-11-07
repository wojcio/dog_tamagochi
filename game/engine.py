"""
Terminal Rendering Engine with flicker-free double buffering and non-blocking input.
"""

import os
import re
import sys
import time
import tty
import termios
import select
import unicodedata

# --- Emoji / East-Asian width helpers -----------------------------------------
# Terminals render emoji and CJK glyphs 2 cells wide, but Python's len() counts
# them as 1. The grid below reserves extra cells for wide chars so ASCII art,
# speech bubbles and HUD lines stay aligned.

_VS16 = '\ufe0f'
# Any CSI sequence found INSIDE drawn text (SGR colors, etc.). draw_text parses
# these into per-cell styles so the grid holds only real characters.
_CSI_RE = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]')

# Codepoints Unicode marks narrow/ambiguous but terminals render fullwidth
# (Emoji_Presentation=Yes). Subset actually used by this game.
_EMOJI_WIDE = {0x26A1, 0x26BD, 0x26F2, 0x26F5, 0x2728, 0x2B50,
               0x2705, 0x274C, 0x2757, 0x2614, 0x2615}

def char_width(ch):
    """Cell width of a single codepoint (best effort for common terminals)."""
    o = ord(ch)
    if unicodedata.combining(ch) or o in (0xFE0F, 0xFE0E, 0x200D, 0x200B):
        return 0
    if unicodedata.east_asian_width(ch) in ('W', 'F'):
        return 2
    if 0x1F000 <= o <= 0x1FAFF:
        return 2
    if o in _EMOJI_WIDE:
        return 2
    return 1

def str_width(text):
    """Terminal cell width of a plain string (no ANSI escapes inside)."""
    total = 0
    last_w = 0
    for ch in text:
        w = char_width(ch)
        if w == 0:
            if ch == _VS16 and last_w == 1:
                total += 1  # VS16 upgrades its base char to fullwidth emoji
                last_w = 2
            continue
        total += w
        last_w = w
    return total

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Foreground standard
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background standard
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Bright background
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"

    # 256 colors helpers
    ORANGE = "\033[38;5;208m"
    BROWN = "\033[38;5;130m"
    LIGHT_BROWN = "\033[38;5;179m"
    DARK_GREEN = "\033[38;5;28m"
    GRASS_GREEN = "\033[38;5;34m"
    SKY_BLUE = "\033[38;5;117m"
    DEEP_SKY = "\033[38;5;75m"
    GOLD = "\033[38;5;220m"
    PINK = "\033[38;5;218m"
    GRAY = "\033[38;5;244m"
    DARK_GRAY = "\033[38;5;238m"
    CREAM = "\033[38;5;229m"
    
    BG_SKY = "\033[48;5;117m"
    BG_GRASS = "\033[48;5;28m"
    BG_DIRT = "\033[48;5;94m"

    @staticmethod
    def fg256(code):
        return f"\033[38;5;{code}m"

    @staticmethod
    def bg256(code):
        return f"\033[48;5;{code}m"


class Terminal:
    # Sentinel marking a grid cell consumed as the 2nd half of a wide char.
    WIDE_CONT = '\x01'

    def __init__(self, width=105, height=28):
        self.target_width = width
        self.target_height = height
        self.orig_termios = None
        self.is_raw = False
        
        # Double buffer grid: each cell is (char, style_str)
        self.buffer = [[' ' for _ in range(self.target_width)] for _ in range(self.target_height)]
        self.style_buffer = [[Colors.RESET for _ in range(self.target_width)] for _ in range(self.target_height)]

        # Diff-render state: the grid last flushed to the screen, so each frame
        # only emits changed cells. None forces a full repaint.
        self.front_buffer = None
        self.front_style = None
        self.prev_size = None

    def invalidate(self):
        """Force a full repaint on the next render() (screen switch, resize, corruption)."""
        self.front_buffer = None
        self.front_style = None
        self.prev_size = None

    def enter_fullscreen(self):
        """Enter raw mode and switch to alternate screen buffer."""
        if sys.stdin.isatty():
            self.orig_termios = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            self.is_raw = True
        
        # Save screen, hide cursor, switch to alternate buffer
        sys.stdout.write("\033[?1049h\033[?25l\033[2J\033[H")
        sys.stdout.flush()
        self.invalidate()  # alt screen is blank; repaint everything

    def exit_fullscreen(self):
        """Restore normal terminal settings."""
        sys.stdout.write("\033[?25h\033[?1049l" + Colors.RESET)
        sys.stdout.flush()
        if self.is_raw and self.orig_termios:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.orig_termios)
            except Exception:
                pass
            self.is_raw = False

    def get_terminal_size(self):
        try:
            sz = os.get_terminal_size()
            return sz.columns, sz.lines
        except Exception:
            return self.target_width, self.target_height

    def clear_buffer(self, bg_char=' ', bg_style=Colors.RESET):
        for y in range(self.target_height):
            for x in range(self.target_width):
                self.buffer[y][x] = bg_char
                self.style_buffer[y][x] = bg_style

    def draw_char(self, x, y, char, style=Colors.RESET):
        if not (0 <= x < self.target_width and 0 <= y < self.target_height):
            return
        if len(char) == 1 and ord(char) < 32:
            return  # control bytes must never enter the grid (see draw_text)
        # Cluster-aware width: handles emoji (VS16) and multi-cell ASCII like '..'
        w = str_width(char) if len(char) != 1 else char_width(char)
        cont = self.WIDE_CONT

        if w == 2 and x + 1 >= self.target_width:
            # No room for the tail cell: a wide base in the last column would
            # render differently in full vs diff mode. Drop it (like clipping).
            return

        if w <= 1 and self.buffer[y][x] == cont:
            # Refuse to paint over the right half of a wide char: that would
            # desynchronize grid columns from screen columns.
            return

        if w == 2 and x >= 1 and self.buffer[y][x - 1] == cont:
            # A new wide char overlapping the tail of an old one: erase that
            # old wide char completely (base + tail).
            self.buffer[y][x - 1] = ' '
            self.style_buffer[y][x - 1] = Colors.RESET
            if x - 2 >= 0:
                self.buffer[y][x - 2] = ' '
                self.style_buffer[y][x - 2] = Colors.RESET

        if w == 2 and x + 1 < self.target_width:
            nxt = self.buffer[y][x + 1]
            nw = str_width(nxt) if len(nxt) != 1 else char_width(nxt)
            if nxt != cont and nw == 2:
                # Next cell is another wide base: our tail will cover it, so
                # erase its orphaned right half too.
                if x + 2 < self.target_width:
                    self.buffer[y][x + 2] = ' '
                    self.style_buffer[y][x + 2] = Colors.RESET

        self.buffer[y][x] = char
        self.style_buffer[y][x] = style
        if w == 2:
            if x + 1 < self.target_width:
                self.buffer[y][x + 1] = cont
                self.style_buffer[y][x + 1] = style
        elif x + 1 < self.target_width and self.buffer[y][x + 1] == cont:
            # Overwrote a wide base char with a narrow one: drop its orphan tail.
            self.buffer[y][x + 1] = ' '
            self.style_buffer[y][x + 1] = Colors.RESET

    def draw_text(self, x, y, text, style=Colors.RESET):
        """Draw text; SGR codes embedded in it become per-cell styles.

        The grid must contain only real characters (never raw ESC bytes), or
        diff rendering would re-emit half a sequence as literal text. Codes
        combine with the `style` argument the way a terminal would render them.
        """
        curr_x = x
        eff = style
        i, n = 0, len(text)
        while i < n:
            ch = text[i]
            if ch == '\x1b':
                m = _CSI_RE.match(text, i)
                if m:
                    code = m.group(0)
                    if code in ('\x1b[0m', '\x1b[m'):
                        eff = Colors.RESET
                    elif not style or style == Colors.RESET:
                        eff = code
                    else:
                        eff = style + code
                    i = m.end()
                    continue
                # Unknown escape: skip the byte rather than corrupt the grid.
                i += 1
                continue
            if ch == '\n':
                y += 1
                curr_x = x
                i += 1
                continue
            w = char_width(ch)
            if w == 0:
                # Variation selector / combining mark: append to previous cell.
                if ch == _VS16 and 0 < curr_x - x and 0 <= curr_x - 1 < self.target_width \
                        and 0 <= y < self.target_height:
                    prev = self.buffer[y][curr_x - 1]
                    if prev not in (self.WIDE_CONT, ' '):
                        if str_width(prev) == 2:
                            # Already a wide base (tail cell exists); VS16
                            # only tweaks text/emoji presentation. Safe to add.
                            self.buffer[y][curr_x - 1] = prev + ch
                        elif char_width(prev) == 1 and curr_x < self.target_width \
                                and self.buffer[y][curr_x] != self.WIDE_CONT:
                            # Widening needs a tail cell; base at last usable
                            # column cannot widen (full/diff would diverge).
                            self.buffer[y][curr_x - 1] = prev + ch
                            self.buffer[y][curr_x] = self.WIDE_CONT
                            self.style_buffer[y][curr_x] = eff
                i += 1
                continue
            if 0 <= curr_x < self.target_width and 0 <= y < self.target_height:
                self.draw_char(curr_x, y, ch, eff)
            curr_x += w
            i += 1

    def draw_sprite(self, x, y, sprite_lines, style=Colors.RESET, transparent_char=' '):
        for row_idx, line in enumerate(sprite_lines):
            py = y + row_idx
            if 0 <= py < self.target_height:
                curr_x = x
                for ch in line:
                    w = char_width(ch) if len(ch) == 1 else max(1, str_width(ch))
                    if ch != transparent_char:
                        if 0 <= curr_x < self.target_width:
                            self.draw_char(curr_x, py, ch, style)
                    curr_x += w

    def draw_colored_sprite(self, x, y, sprite_rows, transparent_char=' '):
        """
        sprite_rows is a list of lists: [[(char, style), (char, style)], ...]
        """
        for row_idx, row in enumerate(sprite_rows):
            py = y + row_idx
            if 0 <= py < self.target_height:
                curr_x = x
                for cell in row:
                    if isinstance(cell, tuple):
                        ch, style = cell
                    else:
                        ch, style = cell, Colors.RESET
                    w = char_width(ch) if len(ch) == 1 else max(1, str_width(ch))
                    if ch != transparent_char:
                        if 0 <= curr_x < self.target_width:
                            self.draw_char(curr_x, py, ch, style)
                    curr_x += w

    def render(self):
        """Flush the frame: emit only cells that changed since the last paint."""
        term_cols, term_lines = self.get_terminal_size()
        too_small = term_cols < self.target_width or term_lines < self.target_height
        resized = self.prev_size != (term_cols, term_lines)

        if too_small or resized or self.front_buffer is None:
            self._render_full(term_cols, term_lines, too_small)
        else:
            ox = max(0, (term_cols - self.target_width) // 2)
            oy = max(0, (term_lines - self.target_height) // 2)
            self._render_diff(ox, oy)

        self.prev_size = (term_cols, term_lines)
        # Remember what is now on screen for the next diff.
        self.front_buffer = [row[:] for row in self.buffer]
        self.front_style = [row[:] for row in self.style_buffer]

    def _render_full(self, term_cols, term_lines, too_small):
        """Repaint the entire grid, clipped to the real terminal size.

        Rows are joined with CR-LF (never a trailing LF) so the cursor can
        never carry a column into the next row on wide terminals, and the
        last row can never scroll the screen — both would corrupt the diff
        state maintained for incremental rendering.
        """
        offset_x = max(0, (term_cols - self.target_width) // 2)
        offset_y = max(0, (term_lines - self.target_height) // 2)
        # Reserve the last row for a warning when the window is too small.
        max_rows = term_lines if not too_small else max(0, term_lines - 1)

        out = ["\033[H"]
        for _ in range(offset_y):
            out.append("\033[K\r\n")

        rows = []
        for y in range(min(self.target_height, max_rows)):
            row = [" "] * offset_x if offset_x > 0 else []

            cells = offset_x
            curr_style = ""
            for x in range(self.target_width):
                ch = self.buffer[y][x]
                if ch == self.WIDE_CONT:
                    continue  # already emitted with its wide base character
                w = str_width(ch) if len(ch) > 1 else char_width(ch)
                if cells + w > term_cols:
                    break
                style = self.style_buffer[y][x]
                if style != curr_style:
                    row.append(style)
                    curr_style = style
                row.append(ch)
                cells += w
            row.append(Colors.RESET + "\033[K")
            rows.append("".join(row))

        out.append("\r\n".join(rows))

        if too_small:
            warn = f" \u26a0 Terminal za ma\u0142y! Powi\u0119ksz okno do {self.target_width}\u00d7{self.target_height} "
            out.append("\r\n" + Colors.BG_BRIGHT_YELLOW + Colors.BOLD
                       + warn[:max(0, term_cols - 1)] + Colors.RESET)

        out.append("\033[J")
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    def _render_diff(self, ox=0, oy=0):
        """Damage-buffer paint: only cells differing from front_buffer are sent.

        Cursor positioning is emitted once per run of changed cells; SGR state
        carries across runs. Wide chars consume their continuation cell, and a
        narrow char replacing a wide one overwrites the orphaned half.
        (ox, oy) are the screen offsets of the centered grid.
        """
        W = self.target_width
        buf, sty = self.buffer, self.style_buffer
        fbuf, fsty = self.front_buffer, self.front_style
        cont = self.WIDE_CONT

        out = []
        cur_y = cur_x = -1   # last cursor position on screen (-1 = unknown)
        style = ""           # SGR state on screen (default after a full paint)

        for y in range(self.target_height):
            brow, bsty = buf[y], sty[y]
            frow, fsty_row = fbuf[y], fsty[y]
            x = 0
            while x < W:
                ch = brow[x]
                if ch == cont or (ch == frow[x] and bsty[x] == fsty_row[x]):
                    x += 1
                    continue

                if cur_y != y + oy or cur_x != x + ox:
                    out.append(f"\033[{y + oy + 1};{x + ox + 1}H")

                while x < W:
                    ch = brow[x]
                    if ch == cont:
                        break  # defensive: never emit a bare continuation
                    if ch == frow[x] and bsty[x] == fsty_row[x]:
                        break
                    cell_style = bsty[x]
                    if cell_style != style:
                        out.append(cell_style)
                        style = cell_style
                    out.append(ch)
                    x += str_width(ch) if len(ch) > 1 else char_width(ch)

                cur_y, cur_x = y + oy, x + ox

        if out:
            out.append(Colors.RESET)
            sys.stdout.write("".join(out))
            sys.stdout.flush()

    def get_input(self):
        """Non-blocking keyboard input reader."""
        if not self.is_raw:
            return []

        keys = []
        while select.select([sys.stdin], [], [], 0)[0]:
            try:
                ch = sys.stdin.read(1)
                if ch == '\033': # Escape sequence
                    if select.select([sys.stdin], [], [], 0.02)[0]:
                        ch2 = sys.stdin.read(1)
                        if ch2 == '[':
                            if select.select([sys.stdin], [], [], 0.02)[0]:
                                ch3 = sys.stdin.read(1)
                                if ch3 == 'A':
                                    keys.append('UP')
                                elif ch3 == 'B':
                                    keys.append('DOWN')
                                elif ch3 == 'C':
                                    keys.append('RIGHT')
                                elif ch3 == 'D':
                                    keys.append('LEFT')
                                elif ch3 == '1' or ch3 == '7':
                                    keys.append('HOME')
                        elif ch2 == '\033':
                            keys.append('ESC')
                    else:
                        keys.append('ESC')
                elif ch == '\n' or ch == '\r':
                    keys.append('ENTER')
                elif ch == ' ':
                    keys.append('SPACE')
                elif ch == '\t':
                    keys.append('TAB')
                elif ch == '\x03': # Ctrl+C
                    keys.append('CTRL_C')
                else:
                    keys.append(ch.lower())
            except Exception:
                break
        return keys
