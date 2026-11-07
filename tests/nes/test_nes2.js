// Headless regression tests for nes2/dog_tamagotchi2.nes in jsnes.
// C global addresses: DATA segment base $300 (cross-checked via ld65 map).
const { NES, Controller } = require('./jsnes.cjs');
const fs = require('fs');
const path = require('path');

const A = {
  dog_x: 0x300, dog_y: 0x302, dog_dir: 0x305, dog_on_ground: 0x306,
  game_mode: 0x30a, ball_cd: 0x30b, eat_timer: 0x30c, worked_flag: 0x30d,
  stat_hunger: 0x312, stat_energy: 0x313, stat_happy: 0x314, stat_bones: 0x315,
  need_timer: 0x316, ball_x: 0x321,
};
const BTN = { UP: Controller.BUTTON_UP, DOWN: Controller.BUTTON_DOWN,
              LEFT: Controller.BUTTON_LEFT, RIGHT: Controller.BUTTON_RIGHT };

const nes = new NES({ onFrame: () => {} });
nes.loadROM(fs.readFileSync(path.join(__dirname, '..', '..', 'nes2', 'dog_tamagotchi2.nes')));

const mem = () => nes.cpu.mem;
const rd = (k) => mem()[A[k]];
const wr = (k, v) => { mem()[A[k]] = v & 0xff; };
const rd16 = (k) => mem()[A[k]] | (mem()[A[k] + 1] << 8);
const wr16 = (k, v) => { mem()[A[k]] = v & 0xff; mem()[A[k] + 1] = (v >> 8) & 0xff; };
const ntAt = (a) => nes.ppu.nameTable[(a >> 10) & 3].tile[a & 0x3ff];

let pass = 0, fail = 0;
function check(name, cond, extra = '') {
  if (cond) { pass++; console.log(`  PASS ${name}`); }
  else { fail++; console.log(`  FAIL ${name} ${extra}`); }
}
function frames(n, fn) { for (let i = 0; i < n; i++) { if (fn) fn(i); nes.frame(); } }
// visible nametable: cam_x >> 8 & 1 selects $2000/$2400 via scroll()
const camBase = () => ((rd16('dog_x') >> 8) & 1) * 0x400;

frames(180);
console.log(`boot: mode=${rd('game_mode')} x=${rd16('dog_x')} ground=${rd('dog_on_ground')} hunger=${rd('stat_hunger')} energy=${rd('stat_energy')}`);

check('T1a grounded', rd('dog_on_ground') === 1);
check('T1b play mode', rd('game_mode') === 0);

// T2 idle: hunger decays, energy stable (worked_flag fix)
const h0 = rd('stat_hunger'), e0 = rd('stat_energy');
frames(600);
check('T2a hunger decays idle', rd('stat_hunger') < h0, `${h0}->${rd('stat_hunger')}`);
check('T2b energy stable idle', rd('stat_energy') === e0, `${e0}->${rd('stat_energy')}`);

// T3 walking drains energy
wr16('dog_x', 200);
const e2 = rd('stat_energy');
frames(300, () => nes.buttonDown(1, BTN.RIGHT));
nes.buttonUp(1, BTN.RIGHT);
check('T3 energy drains walking', rd('stat_energy') < e2, `${e2}->${rd('stat_energy')}`);

// T4 HUD bar tracks hunger (row 2 col 8..12 = $48..$4C, fill tile $7A)
const barFilled = () => { let c = 0; for (let a = 0x48; a <= 0x4c; a++) if (ntAt(a) === 0x7a) c++; return c; };
const b0 = barFilled();
const h3 = rd('stat_hunger');
let guard = 0;
while (rd('stat_hunger') > h3 - 30 && guard++ < 4000) nes.frame();
frames(5);
const b1 = barFilled();
check('T4 HUD bar shrinks', b1 < b0, `b0=${b0} b1=${b1}`);

// T5 eat at bowl (x=48, hold UP)
wr16('dog_x', 48); wr('dog_on_ground', 1);
const h4 = rd('stat_hunger');
frames(240, () => nes.buttonDown(1, BTN.UP));
nes.buttonUp(1, BTN.UP);
const h5 = rd('stat_hunger');
check('T5 UP at bowl refills', h5 > h4 + 20, `${h4}->${h5}`);
check('T5b capped at 100', h5 <= 100);

// T6 bar grows back
frames(5);
check('T6 HUD bar grew back', barFilled() > b1, `${b1}->${barFilled()}`);

// T7 ball kick cooldown - dog pinned against ball at x=300
wr16('ball_x', 300); wr16('dog_x', 290); wr('dog_dir', 0);
let kickFrames = [], prevCd = 0;
nes.buttonDown(1, BTN.RIGHT);
for (let i = 0; i < 300; i++) {
  wr16('dog_x', Math.max(16, rd16('ball_x') - 12));
  const cd = rd('ball_cd');
  if (cd === 30 && prevCd !== 30) kickFrames.push(i);
  prevCd = cd;
  nes.frame();
}
nes.buttonUp(1, BTN.RIGHT);
const gaps = kickFrames.slice(1).map((f, k) => f - kickFrames[k]);
check('T7 ball kicks occur', kickFrames.length >= 3, `kicks=${kickFrames.length}`);
check('T7b all gaps >= 30 frames', gaps.every(g => g >= 30), `gaps=${gaps}`);

// T8 mid-air sleep refused / grounded allowed (buda x 16..60; use x=20)
wr16('dog_x', 20); wr('dog_on_ground', 0); wr16('dog_y', 100); wr('game_mode', 0);
nes.buttonDown(1, BTN.DOWN); frames(4); nes.buttonUp(1, BTN.DOWN); frames(10);
check('T8a mid-air sleep refused', rd('game_mode') === 0, `mode=${rd('game_mode')}`);
wr('dog_on_ground', 1); wr16('dog_y', 152);
nes.buttonDown(1, BTN.DOWN); frames(4); nes.buttonUp(1, BTN.DOWN); frames(10);
check('T8b grounded sleep allowed', rd('game_mode') === 1, `mode=${rd('game_mode')}`);
wr('game_mode', 0);

// T9 scroll keeps HUD rows (stream skips 2-3, bakes 0-1 titles)
wr16('dog_x', 240);
nes.buttonDown(1, BTN.RIGHT);
frames(300);
nes.buttonUp(1, BTN.RIGHT);
const base = camBase();
let barish = 0;
for (let a = base + 0x40; a < base + 0x60; a++) { const t = ntAt(a); if (t === 0x7a || t === 0x7b) barish++; }
check('T9 HUD meters survive scroll', barish >= 6, `meter tiles: ${barish} (base $${base.toString(16)})`);

// T10 biome title row baked as font tiles (>= $80) on visible table after scroll
let titled = 0;
for (let a = base + 0x21; a < base + 0x31; a++) if (ntAt(a) >= 0x80) titled++;
check('T10 biome title present after scroll', titled >= 8, `font tiles: ${titled}`);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
