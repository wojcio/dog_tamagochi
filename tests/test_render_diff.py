#!/usr/bin/env python3
"""
Equivalence tests for the diff renderer (damage buffer) in game/engine.py.

Two strategies, both replaying output through a minimal VT emulator:

1. Equivalence: the same animated scene is fed to a terminal forced to full
   repaint every frame and one using incremental diffs; the emulated screens
   must be identical after every frame.
2. Buffer-match: incremental output is replayed and the emulated screen is
   compared cell-by-cell against the terminal's back buffer every frame.

Also asserts unchanged scenes emit zero bytes and reports bandwidth savings.

Run:  python3 tests/test_render_diff.py
"""

import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.engine import Terminal, Colors, char_width, str_width
from game.dog import Dog
from game.world import World
from game.ui import Renderer


class VTEmulator:
    """Minimal ANSI replay: CUP addressing, erase ops, wide chars, autowrap."""

    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.grid = [[' '] * cols for _ in range(rows)]
        self.row = self.col = 0
        self.pending = False   # deferred-wrap flag after filling the last column

    def _put(self, ch):
        w = str_width(ch) if len(ch) > 1 else char_width(ch)
        if w == 0:
            # Zero-width codepoint (VS16/combining): attach to previous cell.
            if self.row < self.rows and self.col > 0:
                prev = self.grid[self.row][self.col - 1]
                if prev != '\x01':
                    merged = prev + ch
                    self.grid[self.row][self.col - 1] = merged
                    # VS16 upgrades a narrow base to 2 columns (macOS terminals).
                    if ch == '\ufe0f' and str_width(merged) == 2 and not self.pending:
                        if self.col < self.cols:
                            self.grid[self.row][self.col] = '\x01'
                        self.col += 1
                        if self.col >= self.cols:
                            self.pending = True
            return
        if self.pending:
            self.row += 1
            self.col = 0
            self.pending = False
        if self.row >= self.rows:
            return
        w = max(1, w)
        self.grid[self.row][self.col] = ch
        if w == 2 and self.col + 1 < self.cols:
            self.grid[self.row][self.col + 1] = '\x01'   # implicit right half
        self.col += w
        if self.col >= self.cols:
            self.pending = True

    def feed(self, data):
        i, n = 0, len(data)
        while i < n:
            c = data[i]
            if c == '\x1b' and i + 1 < n and data[i + 1] == '[':
                j = i + 2
                while j < n and '\x30' <= data[j] <= '\x3f':
                    j += 1
                if j >= n:
                    break
                final, params = data[j], data[i + 2:j]
                if final == 'H':
                    p = params.split(';') if params else []
                    self.row = (int(p[0]) - 1) if p and p[0] else 0
                    self.col = (int(p[1]) - 1) if len(p) > 1 and p[1] else 0
                    self.row = min(self.row, self.rows - 1)
                    self.col = min(self.col, self.cols - 1)
                    self.pending = False
                elif final == 'J':
                    if '2' in params:
                        self.grid = [[' '] * self.cols for _ in range(self.rows)]
                    else:
                        if self.row < self.rows:
                            for cc in range(min(self.col, self.cols), self.cols):
                                self.grid[self.row][cc] = ' '
                        for rr in range(self.row + 1, self.rows):
                            self.grid[rr] = [' '] * self.cols
                elif final == 'K':
                    if self.row < self.rows:
                        for cc in range(min(self.col, self.cols), self.cols):
                            self.grid[self.row][cc] = ' '
                i = j + 1            # SGR and other CSI: parsed, ignored
            elif c == '\n':
                # LF keeps the column and any deferred-wrap state (xterm semantics)
                self.row += 1
                i += 1
            elif c == '\r':
                self.col = 0
                self.pending = False
                i += 1
            elif c in ('\x07', '\x08'):
                i += 1
            else:
                self._put(c)
                i += 1

    def snapshot(self):
        return [row[:] for row in self.grid]


class FakeTerm(Terminal):
    def __init__(self, cols, rows):
        super().__init__(105, 28)
        self._size = (cols, rows)

    def get_terminal_size(self):
        return self._size


def render_capture(term):
    """Call term.render(), capturing the emitted bytes."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        term.render()
    finally:
        sys.stdout = old
    return buf.getvalue()


def mutate_scene(world, dog, f):
    """Deterministic animation: walking dog, bubbles, day/night, accessories."""
    dog.anim_tick = f
    world.time_tick = f
    world.day_time = (f * 0.004) % 1.0            # cycles through day/night
    dog.x = 8 + (f % 60) * 0.9                    # walks right, wraps
    dog.y = 16.0
    dog.state = ["idle", "walk", "walk", "bark", "pee", "sleep"][f % 6]
    dog.on_ground = True
    if f % 20 == 0:
        dog.say(f"Test! 🦴💧 frame {f % 3}", Colors.BRIGHT_CYAN, 25)
    if f % 37 == 0:
        dog.inventory = ["crown", "bow"]
        dog.equipped_item = ["crown", None, "bow"][f // 37 % 3]


def draw_scene(term, rend, world, dog):
    term.clear_buffer()
    rend.render_world_and_hud(world, dog, [], [], [], [])


def run_equivalence(name, cols, rows, frames):
    """Full-repaint reference vs incremental diff must build identical screens."""
    t_full, t_diff = FakeTerm(cols, rows), FakeTerm(cols, rows)
    em_full, em_diff = VTEmulator(cols, rows), VTEmulator(cols, rows)
    world = World(420, 22)
    dog = Dog("corgi", x=10.0, y=16.0, name="Burek")
    dog.days_together = 3
    rend_full, rend_diff = Renderer(t_full), Renderer(t_diff)

    b_full = b_diff = 0
    for f in range(frames):
        mutate_scene(world, dog, f)

        draw_scene(t_full, rend_full, world, dog)
        t_full.invalidate()                       # force the full-repaint path
        out = render_capture(t_full)
        em_full.feed(out)
        b_full += len(out.encode("utf-8"))

        draw_scene(t_diff, rend_diff, world, dog)  # incremental from frame 1 on
        out = render_capture(t_diff)
        em_diff.feed(out)
        b_diff += len(out.encode("utf-8"))

        if em_full.snapshot() != em_diff.snapshot():
            for y in range(rows):
                for x in range(cols):
                    a = em_full.grid[y][x]
                    b = em_diff.grid[y][x]
                    if a != b:
                        raise AssertionError(
                            f"[{name}] frame {f}: screen diverged at ({y},{x}): "
                            f"full={a!r} diff={b!r}")
    ratio = (1 - b_diff / b_full) * 100 if b_full else 0
    print(f"  [{name}] {frames} frames identical | "
          f"{b_full:>8} B full vs {b_diff:>7} B diff  ({ratio:.0f}% less output)")


def run_buffer_match(cols, rows, frames):
    """Incremental output replayed must equal the terminal buffer every frame."""
    t = FakeTerm(cols, rows)
    em = VTEmulator(cols, rows)
    world = World(420, 22)
    dog = Dog("setter", x=10.0, y=16.0, name="Dżek")
    rend = Renderer(t)
    oy = max(0, rows - 28) // 2
    ox = max(0, cols - 105) // 2

    total = 0
    for f in range(frames):
        mutate_scene(world, dog, f)
        draw_scene(t, rend, world, dog)
        out = render_capture(t)
        em.feed(out)
        total += len(out.encode("utf-8"))

        snap = em.snapshot()
        for y in range(28):
            exp_row = t.buffer[y]
            got_row = snap[y + oy]
            for x in range(105):
                if exp_row[x] != got_row[x + ox]:
                    raise AssertionError(
                        f"frame {f} ({y},{x}): buffer={exp_row[x]!r} "
                        f"screen={got_row[x + ox]!r}")
    print(f"  [buffer-match {cols}x{rows}] {frames} frames match | {total} B total")


def main():
    print("== diff-render equivalence ==")
    run_equivalence("exact 105x28", 105, 28, 150)
    run_equivalence("offset 115x30", 115, 30, 90)
    run_buffer_match(105, 28, 150)
    run_buffer_match(115, 30, 90)

    # Static scene: repainting unchanged content must emit nothing at all.
    t = FakeTerm(105, 28)
    world = World(420, 22)
    dog = Dog("shiba", x=10.0, y=16.0)
    dog.anim_tick = 5
    rend = Renderer(t)
    draw_scene(t, rend, world, dog)
    render_capture(t)                      # first paint (full)
    out_static = render_capture(t)         # identical scene again
    assert out_static == "", f"static repaint emitted {len(out_static)} bytes"
    print("  [static] unchanged frame emitted 0 bytes")

    print("\nALL DIFF-RENDER TESTS PASS [OK]")


if __name__ == "__main__":
    main()
