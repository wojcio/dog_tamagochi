#!/usr/bin/env python3
"""Live pty smoke test: boot the real game in a 30x105 pty, adopt a dog,
teleport it through Las -> Rzeka (swim) -> Psi Park -> Ulica (cars), and
assert the world/zone/HUD machinery all renders. Logs go to LOG file."""
import os, pty, sys, time, tty, fcntl, termios, struct, signal, select

REPO = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(REPO, "pty_zone_log.txt")
CAP = os.path.join(REPO, "pty_capture.txt")

CHILD = r'''
import os, sys, time
sys.path.insert(0, %(repo)r)
LOGPATH = %(log)r
import game.dog as dogmod
import main as m

log_f = open(LOGPATH, "w", buffering=1)
ticks = {"n": 0}

# Schedule: (first tick at which to teleport, x, y)
SCHED = [
    (20, 150.0, 16.0),   # Las
    (60, 262.0, 16.0),   # Rzeka water -> swim entry
    (150, 298.0, 16.0),  # east bank -> swim exit
    (170, 450.0, 16.0),  # Psi Park
    (200, 558.0, 16.0),  # Ulica (wait for cars)
]

orig = dogmod.Dog.update_physics
def patched(self, world):
    r = orig(self, world)
    n = ticks["n"]; ticks["n"] += 1
    for t, x, y in SCHED:
        if n == t:
            self.x = x; self.y = y; self.vx = 0.0; self.vy = 0.0
            self.swimming = False
    if True:  # update_physics only runs inside the live game loop
        z = world.zone_at(self.x + self.width / 2)
        log_f.write("%%d %%s swim=%%s wet=%%d cars=%%d state=%%s\n" %%
                    (n, z["name"], self.swimming, self.wet_timer,
                     len(world.cars), self.state))
    if n >= 420:
        log_f.write("DONE\n"); log_f.close()
        os._exit(0)
    return r

dogmod.Dog.update_physics = patched
try:
    m.main()
except SystemExit:
    pass
except BaseException:
    import traceback
    log_f.write(traceback.format_exc())
os._exit(0)
''' % {"repo": REPO, "log": LOG}

env = dict(os.environ)
home = os.path.join(REPO, "pty_home")
os.makedirs(home, exist_ok=True)
env["HOME"] = home
env["PATH"] = "/usr/bin:/bin"          # no afplay/sox -> audio goes silent
env["TERM"] = "xterm-256color"

pid, fd = pty.fork()
if pid == 0:
    os.execve(sys.executable, [sys.executable, "-c", CHILD], env)

# parent: configure window size 30 rows x 105 cols
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 105, 0, 0))

def drain(seconds):
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.1)
        if fd in r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                return False
            if not data:
                return False
            with open(CAP, "ab") as f:
                f.write(data)
    return True

open(CAP, "wb").close()
time.sleep(1.5)
drain(1.0)
os.write(fd, b"\n")          # breed select (corgi default)
drain(1.0)
for ch in "Azorek":          # type slowly so every key lands in its own poll
    os.write(fd, ch.encode())
    drain(0.15)
os.write(fd, b"\r")          # confirm name
drain(2.0)
os.write(fd, b"\r")          # safety re-confirm in case the first ENTER raced
drain(17.0)                  # let the tick schedule run out (420 ticks @30fps)

try:
    os.kill(pid, signal.SIGKILL)
except ProcessLookupError:
    pass
os.waitpid(pid, 0)
try:
    os.close(fd)
except OSError:
    pass

log = open(LOG).read() if os.path.exists(LOG) else ""
cap = open(CAP, "rb").read().decode("utf-8", "replace")

fails = []
def check(name, cond):
    print(("  [OK] " if cond else "  [FAIL] ") + name)
    if not cond:
        fails.append(name)

print("== Live pty zone walk ==")
for zone in ("Las", "Rzeka", "Psi Park", "Ulica", "Ogród"):
    check(f"HUD saw zone {zone}", zone in log)
check("swimming happened", "swim=True" in log)
check("wet afterwards", any(l.split(" wet=")[1].split()[0] != "0"
                           for l in log.splitlines() if " wet=" in l))
check("cars spawned on Ulica", any(int(l.split("cars=")[1].split()[0]) >= 1
                                  for l in log.splitlines() if "cars=" in l))
check("swim sprite state rendered", "state=swim" in log)
check("capture has real screen output", len(cap) > 50_000)
check("dog name adopted", "AZOREK" in cap.upper() or "Azorek" in cap)
check("schedule completed", "DONE" in log)

if fails:
    print("PTY TEST FAILURES:", fails)
    print("---- log tail ----")
    print("\n".join(log.splitlines()[-12:]))
    sys.exit(1)

# Clean run artifacts on success (keep them on failure for debugging).
import shutil
for p in (LOG, CAP):
    try:
        os.remove(p)
    except OSError:
        pass
shutil.rmtree(home, ignore_errors=True)
print("PTY ZONE WALK PASS [OK]")
