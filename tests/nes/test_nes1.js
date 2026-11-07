// Headless regression tests for nes/dog_tamagotchi.nes in jsnes.
// ZP addresses from ca65 listing (post-fix build).
const { NES, Controller } = require('./jsnes.cjs');
const fs = require('fs');
const path = require('path');

const ZP = {
  game_mode: 0x02, gamepad_cur: 0x03, gamepad_press: 0x05,
  dog_x_lo: 0x06, dog_x_hi: 0x07, dog_y: 0x08, dog_on_ground: 0x0c,
  stat_hunger: 0x1a, stat_energy: 0x1b, stat_happy: 0x1c, stat_bones: 0x1d,
  tamagotchi_tick: 0x1e, scroll_nt: 0x14, worked_flag: 0x22, eat_timer: 0x23, toyball_cd: 0x24,
  toyball_x_lo: 0x35, toyball_x_hi: 0x36, toyball_vx: 0x38,
};
const BTN = { UP: Controller.BUTTON_UP, DOWN: Controller.BUTTON_DOWN,
              LEFT: Controller.BUTTON_LEFT, RIGHT: Controller.BUTTON_RIGHT,
              A: Controller.BUTTON_A };

const nes = new NES({ onFrame: () => {} });
nes.loadROM(fs.readFileSync(path.join(__dirname, '..', '..', 'nes', 'dog_tamagotchi.nes')));

const ram = () => nes.cpu.mem;
const rd = (k) => ram()[ZP[k]];
const wr = (k, v) => { ram()[ZP[k]] = v; };
const dogX = () => rd('dog_x_hi') * 256 + rd('dog_x_lo');
const setDogX = (v) => { wr('dog_x_hi', (v >> 8) & 0xff); wr('dog_x_lo', v & 0xff); };
const ntAt = (a) => nes.ppu.nameTable[(a >> 10) & 3].tile[a & 0x3ff];
const ntSlice = (a, b) => { const out = []; for (let i = a; i < b; i++) out.push(ntAt(i)); return out; };

let pass = 0, fail = 0;
function check(name, cond, extra = '') {
  if (cond) { pass++; console.log(`  PASS ${name}`); }
  else { fail++; console.log(`  FAIL ${name} ${extra}`); }
}

function frames(n, fn) {
  for (let i = 0; i < n; i++) { if (fn) fn(i); nes.frame(); }
}

// Boot
frames(180);
console.log(`boot: mode=${rd('game_mode')} x=${dogX()} ground=${rd('dog_on_ground')} hunger=${rd('stat_hunger')} energy=${rd('stat_energy')}`);

// T1: boot integrity
check('T1a grounded after boot', rd('dog_on_ground') === 1);
check('T1b play mode', rd('game_mode') === 0);

// T2: idle - hunger decays, energy must NOT drain (worked_flag fix)
const h0 = rd('stat_hunger'), e0 = rd('stat_energy');
frames(600); // 10s -> ~5 hunger ticks
const h1 = rd('stat_hunger'), e1 = rd('stat_energy');
check('T2a hunger decays idle', h1 < h0, `${h0}->${h1}`);
check('T2b energy stable idle', e1 === e0, `${e0}->${e1}`);

// T3: walking drains energy
wr('dog_x_lo', 200); wr('dog_x_hi', 0);
const e2 = rd('stat_energy');
frames(300, () => nes.buttonDown(1, BTN.RIGHT));
nes.buttonUp(1, BTN.RIGHT);
const e3 = rd('stat_energy');
check('T3 energy drains while walking', e3 < e2, `${e2}->${e3}`);

// T4: HUD bar tracks hunger in nametable (col 8..13 row 2 = $48..$4D), ']' at $5E? no: $48+6=$4E
const barFilled = () => ntSlice(0x48, 0x4e).filter(t => t === 0x80).length;
const b0 = barFilled();
const h2 = rd('stat_hunger');
while (rd('stat_hunger') > h2 - 34) nes.frame(); // let hunger fall ~2 bars
frames(5);
const b1 = barFilled();
check('T4 HUD bar shrinks with hunger', b1 < b0, `${b0}->${b1}`);
check('T4b HUD right bracket intact', ntAt(0x4e) === 0x5d, 'got $' + ntAt(0x4e).toString(16));

// T5: eat at bowl (x=72, hold UP)
wr('dog_x_lo', 72); wr('dog_x_hi', 0); wr('dog_on_ground', 1);
const h3 = rd('stat_hunger');
frames(240, () => nes.buttonDown(1, BTN.UP));
nes.buttonUp(1, BTN.UP);
const h4 = rd('stat_hunger');
check('T5 UP at bowl refills hunger', h4 > h3 + 20, `${h3}->${h4}`);
check('T5b hunger capped at 100', h4 <= 100);

// T6: bar grows back after eating
frames(5);
check('T6 HUD bar grew back', barFilled() > b1, `${b1}->${barFilled()}`);

// T7: ball kick cooldown - hold the dog against the ball; kicks must be
// spaced >= 30 frames apart (old build: kick + SFX every single frame)
setDogX(630); wr('toyball_x_lo', 648 & 0xff); wr('toyball_x_hi', 2); wr('toyball_vx', 0);
wr('dog_dir', 0);
let kickFrames = [], prevCd = 0;
nes.buttonDown(1, BTN.RIGHT);
for (let i = 0; i < 300; i++) {
  const bx = rd('toyball_x_hi') * 256 + rd('toyball_x_lo');
  setDogX(bx - 10);                       // dog stays pressed against the ball
  const cd = rd('toyball_cd');
  if (cd === 30 && prevCd !== 30) kickFrames.push(i);
  prevCd = cd;
  nes.frame();
}
nes.buttonUp(1, BTN.RIGHT);
const gaps = kickFrames.slice(1).map((f, k) => f - kickFrames[k]);
check('T7 ball kicks occur', kickFrames.length >= 3, `kicks=${kickFrames.length}`);
check('T7b all gaps >= 30 frames', gaps.every(g => g >= 30), `gaps=${gaps}`);

// T8: mid-air sleep refused, grounded sleep allowed
setDogX(40); wr('dog_on_ground', 0); wr('dog_y', 100);
wr('game_mode', 0);
nes.buttonDown(1, BTN.DOWN); frames(4); nes.buttonUp(1, BTN.DOWN);
frames(10);
check('T8a mid-air sleep refused', rd('game_mode') === 0, `mode=${rd('game_mode')}`);
wr('dog_on_ground', 1); wr('dog_y', 152);
nes.buttonDown(1, BTN.DOWN); frames(4); nes.buttonUp(1, BTN.DOWN);
frames(10);
check('T8b grounded sleep allowed', rd('game_mode') === 1, `mode=${rd('game_mode')}`);

// T9: scrolling keeps HUD meters intact (stream skips rows 2-3)
// walk right across a screen boundary, then check HUD row still has bar tiles
wr('game_mode', 0);
setDogX(240);
nes.buttonDown(1, BTN.RIGHT);
frames(300);
nes.buttonUp(1, BTN.RIGHT);
const base = rd('scroll_nt') * 0x400; // visible nametable after scroll
const row2 = ntSlice(base + 0x40, base + 0x60);
const barish = row2.filter(t => t === 0x80 || t === 0x81).length;
check('T9 HUD row survives scroll', barish >= 6, `bar-tiles in row2: ${barish} (base $${base.toString(16)})`);
check('T9b brackets survive scroll', ntAt(base + 0x4e) === 0x5d && ntAt(base + 0x5d) === 0x5d,
      `$4e=${ntAt(base + 0x4e).toString(16)} $5d=${ntAt(base + 0x5d).toString(16)}`);

// T10: biome title row (row 1, col 2..) is text on the visible table after scroll
const printable = ntSlice(base + 0x22, base + 0x30).every(t => (t >= 0x20 && t <= 0x7e) || t >= 0x80);
check('T10 title row is text after scroll', printable, ntSlice(base + 0x22, base + 0x30).map(t => t.toString(16)).join(' '));

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
