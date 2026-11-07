# 🧪 NES headless regression tests

Both ROMs (`nes/` asm edition and `nes2/` C edition) are booted in the
**jsnes** emulator under Node, driven with scripted controller input, and
asserted against live emulator state (zero-page / DATA RAM + nametables).
No GUI, no manual clicking — `npm test` proves the gameplay fixes.

## Setup & run

```bash
cd tests/nes
npm install
npm run setup     # copies the jsnes UMD bundle to jsnes.cjs (package is type:module)
npm test          # runs test_nes1.js then test_nes2.js
```

Build the ROMs first if they changed (`make` in `nes/` and `nes2/`).

## What is covered

| Test | Asserts |
|------|---------|
| T1 | boot: dog grounded, play mode |
| T2 | idle: hunger decays, **energy stays stable** (worked-flag fix) |
| T3 | walking drains energy |
| T4 | HUD bar tiles shrink as hunger drops (+ `]` bracket intact) |
| T5/T6 | **hold UP at the food bowl → hunger refills**, bar redraws |
| T7 | **ball kick cooldown ≥ 30 frames** (no SFX machine-gunning) |
| T8 | **sleep refused mid-air**, allowed when grounded at the buda |
| T9 | scrolling does not trash the HUD meters (stream skips rows 2–3) |
| T10 | biome title row survives/updates across screen boundaries |

## Notes

- Symbol addresses are taken from the current builds:
  - `test_nes1.js`: zero-page labels via `ca65 -l` listing of `nes/main.s`
  - `test_nes2.js`: C globals in DATA segment, base `$300` (cross-checked
    with an `ld65 -m` map file)
  If you add/reorder variables, refresh those tables from a fresh listing.
- jsnes controllers are 1-indexed: `nes.buttonDown(1, ...)`.
- RAM peek: `nes.cpu.mem[addr]`; nametables: `nes.ppu.nameTable[i].tile`.
