"""
Terminal Rendering Engine with flicker-free double buffering and non-blocking input.
"""

import os
import sys
import time
import tty
import termios
import select

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
    def __init__(self, width=105, height=28):
        self.target_width = width
        self.target_height = height
        self.orig_termios = None
        self.is_raw = False
        
        # Double buffer grid: each cell is (char, style_str)
        self.buffer = [[' ' for _ in range(self.target_width)] for _ in range(self.target_height)]
        self.style_buffer = [[Colors.RESET for _ in range(self.target_width)] for _ in range(self.target_height)]

    def enter_fullscreen(self):
        """Enter raw mode and switch to alternate screen buffer."""
        if sys.stdin.isatty():
            self.orig_termios = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            self.is_raw = True
        
        # Save screen, hide cursor, switch to alternate buffer
        sys.stdout.write("\033[?1049h\033[?25l\033[2J\033[H")
        sys.stdout.flush()

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
        if 0 <= x < self.target_width and 0 <= y < self.target_height:
            self.buffer[y][x] = char
            self.style_buffer[y][x] = style

    def draw_text(self, x, y, text, style=Colors.RESET):
        curr_x = x
        for ch in text:
            if ch == '\n':
                y += 1
                curr_x = x
                continue
            if 0 <= curr_x < self.target_width and 0 <= y < self.target_height:
                self.buffer[y][curr_x] = ch
                self.style_buffer[y][curr_x] = style
            curr_x += 1

    def draw_sprite(self, x, y, sprite_lines, style=Colors.RESET, transparent_char=' '):
        for row_idx, line in enumerate(sprite_lines):
            py = y + row_idx
            if 0 <= py < self.target_height:
                for col_idx, ch in enumerate(line):
                    px = x + col_idx
                    if 0 <= px < self.target_width:
                        if ch != transparent_char:
                            self.buffer[py][px] = ch
                            self.style_buffer[py][px] = style

    def draw_colored_sprite(self, x, y, sprite_rows, transparent_char=' '):
        """
        sprite_rows is a list of lists: [[(char, style), (char, style)], ...]
        """
        for row_idx, row in enumerate(sprite_rows):
            py = y + row_idx
            if 0 <= py < self.target_height:
                for col_idx, cell in enumerate(row):
                    if isinstance(cell, tuple):
                        ch, style = cell
                    else:
                        ch, style = cell, Colors.RESET
                    px = x + col_idx
                    if 0 <= px < self.target_width:
                        if ch != transparent_char:
                            self.buffer[py][px] = ch
                            self.style_buffer[py][px] = style

    def render(self):
        """Flushes the entire frame at once."""
        term_cols, term_lines = self.get_terminal_size()
        offset_x = max(0, (term_cols - self.target_width) // 2)
        offset_y = max(0, (term_lines - self.target_height) // 2)

        out = ["\033[H"]
        for _ in range(offset_y):
            out.append("\033[K\n")

        for y in range(self.target_height):
            if offset_x > 0:
                out.append(" " * offset_x)
            
            curr_style = ""
            for x in range(self.target_width):
                style = self.style_buffer[y][x]
                ch = self.buffer[y][x]
                if style != curr_style:
                    out.append(style)
                    curr_style = style
                out.append(ch)
            out.append(Colors.RESET + "\033[K\n")

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
