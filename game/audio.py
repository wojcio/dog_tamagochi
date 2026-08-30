"""
Authentic PC Speaker 8-bit Sound Synthesizer and Audio Player.
Generates pure square-wave retro chiptune SFX in memory using standard Python.
"""

import os
import sys
import wave
import struct
import math
import tempfile
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

class PCSpeakerSoundSystem:
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.temp_dir = tempfile.mkdtemp(prefix="dog_tamagotchi_sfx_")
        self.sfx_files = {}
        self.enabled = True
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._generate_all_sfx()

    def _generate_wave(self, name, duration_sec, freq_func, volume=0.45, pulse_duty=0.5):
        """Generates a square wave audio file mimicking the 8253 PIT / IBM PC Speaker."""
        file_path = os.path.join(self.temp_dir, f"{name}.wav")
        total_samples = int(self.sample_rate * duration_sec)
        
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) # 16-bit PCM for clean compatibility
            wf.setframerate(self.sample_rate)
            
            phase = 0.0
            frames = []
            max_amp = int(32767 * volume)
            
            for i in range(total_samples):
                progress = i / float(total_samples)
                freq = freq_func(progress)
                
                # Advance phase
                phase += freq / float(self.sample_rate)
                phase_mod = phase - math.floor(phase)
                
                # Pure 1-bit PC Speaker Square wave
                val = max_amp if phase_mod < pulse_duty else -max_amp
                
                # Slight envelope decay to avoid clicks
                if progress > 0.85:
                    decay = (1.0 - progress) / 0.15
                    val = int(val * decay)
                elif progress < 0.05:
                    fade_in = progress / 0.05
                    val = int(val * fade_in)
                    
                frames.append(struct.pack('<h', int(val)))
                
            wf.writeframes(b''.join(frames))
            
        self.sfx_files[name] = file_path

    def _generate_all_sfx(self):
        # 1. BARK: Sharp punchy PC speaker bark (320Hz -> 620Hz -> 220Hz)
        def bark_freq(p):
            if p < 0.3:
                return 300.0 + (p / 0.3) * 350.0
            else:
                return 650.0 - ((p - 0.3) / 0.7) * 450.0
        self._generate_wave('bark', 0.11, bark_freq, volume=0.5)

        # 2. JUMP: Classic 8-bit platformer jump slide (180Hz -> 580Hz)
        def jump_freq(p):
            return 180.0 + math.pow(p, 0.7) * 420.0
        self._generate_wave('jump', 0.12, jump_freq, volume=0.4)

        # 3. EAT / BONE: Fast 4-note retro arpeggio pickup
        def eat_freq(p):
            notes = [523.25, 659.25, 783.99, 1046.50] # C5, E5, G5, C6
            idx = min(len(notes) - 1, int(p * len(notes)))
            return notes[idx]
        self._generate_wave('eat', 0.16, eat_freq, volume=0.45)

        # 4. PETTING / LOVE: Sweet warm harmonic arpeggio (A4 -> C#5 -> E5 -> A5)
        def pet_freq(p):
            notes = [440.0, 554.37, 659.25, 880.0]
            idx = min(len(notes) - 1, int(p * len(notes)))
            return notes[idx]
        self._generate_wave('pet', 0.22, pet_freq, volume=0.4)

        # 5. PEE / WATER MARK: Pitch-dropping funny bubble effect
        def pee_freq(p):
            return 700.0 - math.sin(p * 25.0) * 150.0 - p * 300.0
        self._generate_wave('pee', 0.25, pee_freq, volume=0.35)

        # 6. SCARE / BIRD: Fast fluttering chirps
        def scare_freq(p):
            return 800.0 + math.sin(p * 50.0) * 400.0
        self._generate_wave('scare', 0.15, scare_freq, volume=0.35)

        # 7. MENU MOVE: Short high blip
        self._generate_wave('menu_move', 0.035, lambda p: 950.0, volume=0.3)

        # 8. MENU SELECT / POWERUP: Ascending two-tone chime (440Hz -> 880Hz)
        def select_freq(p):
            return 440.0 if p < 0.45 else 880.0
        self._generate_wave('menu_select', 0.14, select_freq, volume=0.45)

        # 9. ALERT / LOW STAT: Classic IBM PC BIOS urgent double beep
        def alert_freq(p):
            if p < 0.4: return 880.0
            if p < 0.6: return 0.0
            return 880.0
        self._generate_wave('alert', 0.18, alert_freq, volume=0.45)

        # 10. SLEEP: Soft lullaby descending notes
        def sleep_freq(p):
            notes = [659.25, 587.33, 523.25, 392.00]
            idx = min(len(notes) - 1, int(p * len(notes)))
            return notes[idx]
        self._generate_wave('sleep', 0.35, sleep_freq, volume=0.3)

        # 11. TRICK: Playful rapid arpeggio
        def trick_freq(p):
            notes = [392.00, 523.25, 659.25, 783.99, 1046.50]
            idx = min(len(notes) - 1, int(p * len(notes)))
            return notes[idx]
        self._generate_wave('trick', 0.22, trick_freq, volume=0.45)

        # 12. LEVEL UP: Majestic victory fanfare
        def lvl_freq(p):
            notes = [523.25, 659.25, 783.99, 659.25, 783.99, 1046.50]
            idx = min(len(notes) - 1, int(p * len(notes)))
            return notes[idx]
        self._generate_wave('level_up', 0.38, lvl_freq, volume=0.5)

        # 13. BUY: Cash register chime (Ka-ching!)
        def buy_freq(p):
            if p < 0.4: return 987.77 # B5
            return 1318.51            # E6
        self._generate_wave('buy', 0.18, buy_freq, volume=0.45)

        # 14. SPLASH: Water splash on beach
        def splash_freq(p):
            return 400.0 + math.sin(p * 40.0) * 200.0 - p * 150.0
        self._generate_wave('splash', 0.15, splash_freq, volume=0.35)

        # 15. CHEER: Agility course finish cheer
        def cheer_freq(p):
            notes = [440.0, 554.37, 659.25, 880.0, 1108.73]
            idx = min(len(notes) - 1, int(p * len(notes)))
            return notes[idx]
        self._generate_wave('cheer', 0.30, cheer_freq, volume=0.45)

    def play(self, sfx_name):
        """Asynchronously plays PC speaker sound without blocking game logic."""
        if not self.enabled:
            return

        file_path = self.sfx_files.get(sfx_name)
        if not file_path or not os.path.exists(file_path):
            return

        self.executor.submit(self._play_file, file_path)

    def _play_file(self, file_path):
        try:
            # macOS built-in ultra-fast low latency player
            subprocess.run(["afplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Fallback to terminal bell
            try:
                sys.stdout.write("\a")
                sys.stdout.flush()
            except Exception:
                pass

    def toggle_mute(self):
        self.enabled = not self.enabled
        return self.enabled

    def cleanup(self):
        try:
            for f in self.sfx_files.values():
                if os.path.exists(f):
                    os.remove(f)
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except Exception:
            pass

# Global singleton audio instance
audio = PCSpeakerSoundSystem()
