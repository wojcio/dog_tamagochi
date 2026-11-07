#!/usr/bin/env python3
"""
embed_rom.py - Repacks a freshly built .nes ROM into the play*.html page.

The HTML embeds the ROM as `const EMBEDDED_ROM_B64 = "...";` so the game
runs with zero server-side files. Run after every ROM build (the Makefile's
`web` target does this automatically) so the browser copy never goes stale.

Usage: python3 tools/embed_rom.py dog_tamagotchi.nes play.html
"""

import base64
import hashlib
import re
import sys
from pathlib import Path


def main():
    rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dog_tamagotchi.nes")
    html_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("play.html")

    rom = rom_path.read_bytes()
    if not rom.startswith(b"NES\x1a"):
        sys.exit(f"ERROR: {rom_path} does not look like an iNES ROM")

    b64 = base64.b64encode(rom).decode("ascii")
    html = html_path.read_text(encoding="utf-8")

    pattern = re.compile(r'(EMBEDDED_ROM_B64\s*=\s*")[A-Za-z0-9+/=]+(")')
    new_html, count = pattern.subn(lambda m: m.group(1) + b64 + m.group(2), html)
    if count != 1:
        sys.exit(f"ERROR: expected exactly 1 EMBEDDED_ROM_B64 marker in {html_path}, found {count}")

    html_path.write_text(new_html, encoding="utf-8")
    sha = hashlib.sha1(rom).hexdigest()[:12]
    print(f"Embedded {rom_path} ({len(rom)} B, sha1 {sha}) into {html_path}")


if __name__ == "__main__":
    main()
