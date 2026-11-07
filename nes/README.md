# 🐕 Dog Tamagotchi 2D Platformer - Wersja NES (Famicom) 8-bit

Oficjalny port gry **Dog Tamagotchi 2D Platformer** na konsolę **Nintendo Entertainment System (NES / Famicom)**, napisany w **czystym asemblerze CA65 (MOS 6502)**.

---

## 🎮 Informacje Techniczne ROM-u

* **Format:** iNES 1.0 (`.nes`)
* **Mapper:** Mapper 0 (NROM-256)
* **PRG-ROM:** 32 KB (2 banki po 16 KB)
* **CHR-ROM:** 8 KB (512 kafelków 8x8 2BPP: Pattern Table 0 dla tła/HUD, Pattern Table 1 dla sprite'ów)
* **Mirroring:** Wertykalny (dla płynnego przewijania poziomego)
* **Częstotliwość odświeżania:** 60 Hz NTSC (kompatybilny także z 50 Hz PAL)
* **Dźwięk:** 2A03 APU (Square 1, Square 2, Triangle)

---

## 🗺️ Elementy Świata i Rozgrywki na NES

1. **Piesek (Hardware Sprites 16x16 px):**
   - Złożony z 4 sprzętowych duszków NES (2x2 kafelki 8x8) z pełną obsługą przerzucania horyzontalnego (`flip X`).
   - Płynne animacje chodu (klatki Walk 1 i Walk 2), stania (Idle), skoku (Jump) oraz zwinięcia w kłębek podczas snu (Sleep).
   - Dymek szczekania (`HAU!`) oraz ikonka `Zzz` podczas snu.

2. **Otoczenie i Platformy:**
   - **Buda psa z czerwonym dachem i kocykiem:** Położona po lewej stronie planszy. Wciśnięcie `[DÓŁ]` przed wejściem (stojąc na ziemi) układa pieska do snu.
   - **Drewniane platformy:** Dwa poziomy podestów do zręcznościowego wskakiwania.
   - **Miska z karmą:** Stoi obok budy – przytrzymanie `[GÓRA]` w jej pobliżu regeneruje głód psa do 100%.
   - **Hydrant i Drzewo:** Ozdobne elementy parku i ogrodu.
   - **Interaktywna Piłka (Toy Ball):** Piesek może trącać i toczyć piłkę łapkami po trawie, co zwiększa jego wskaźnik szczęścia (jeden kop – jedno szczeknięcie, kopywanie co pół sekundy).

3. **Symulacja Potrzeb Tamagotchi (HUD w czasie rzeczywistym):**
   - **Głód (`HUNGER:`):** Wskaźnik serduszek [♥♥♥♥]. Spada z czasem, odnawiany przy misce z jedzeniem.
   - **Energia (`ENERGY:`):** Wskaźnik błyskawic [⚡⚡⚡⚡]. Zużywa się podczas biegania i skakania. Szybko regeneruje się podczas snu w budzie.
   - **Szczęście (`HAPPY :`):** Spada, gdy piesek jest głodny lub przemęczony; rośnie po szczekaniu, zbieraniu kości i zabawie piłką.
   - **Kości (`BONES :`):** Licznik zebranych smakołyków (00–99).

4. **Autorska Synteza Dźwięku APU (8-bit Chiptune):**
   - **Szczekanie (`HAU!`):** Kanał Square 1 (szybki, agresywny spadek częstotliwości imitujący szczeknięcie).
   - **Skok:** Kanał Square 1 z wbudowanym sprzętowym sweepem wznoszącym.
   - **Zbieranie kości / Jedzenie:** Kanał Square 2 (melodyjne 3-tonowe arpeggio C5 → E5 → G5).
   - **Sen w budzie:** Kanał Triangle (łagodna, usypiająca melodia basowa).
   - **Pobudka i sztuczki:** Podwójny akord fanfary.

---

## 🕹️ Sterowanie na Padzie NES

| Przycisk NES | Akcja |
| :---: | :--- |
| **`D-Pad Lewo / Prawo`** | Bieg w lewo / w prawo (z animacją łapek) |
| **`A`** | Skok na platformy i przeszkody |
| **`B`** | Szczekanie (`HAU!`), płoszenie i radość |
| **`GÓRA` (przy misce 🥣)** | **Jedzenie karmy – regeneracja głodu do 100%** |
| **`DÓŁ` (przy budzie)** | **Wejście do budy i sen regeneracyjny 💤** (tylko na ziemi) |
| **`A / B / START` (w trakcie snu)** | Pobudka z budy |

> Miska z karmą (🥣) stoi tuż obok budy po lewej stronie pierwszej planszy.
> Podejdź i **przytrzymaj `GÓRA`**, aż pasek `GLOD` osiągnie 100%.

---

## 🛠️ Kompilacja i Budowanie

Projekt korzysta z kompilatora `ca65` oraz linkera `ld65` (pakiet `cc65`):

```bash
cd nes
make
```

Polecenie automatycznie wygeneruje:
* `graphics.chr` – 8 KB bank pamięci graficznej CHR z kafelkami tła, fontem i duszkami psa.
* `dog_tamagotchi.nes` – gotowy plik ROM do uruchomienia na dowolnym emulatorze lub programatorze kasetowym (EverDrive N8).
* `play.html` – *(cel `make web`, uruchamiany automatycznie)* strona WWW z wbudowanym ROM-em i emulatorze jsnes – zawsze świeża, nigdy nie wymaga serwera.

Czyste przebudowanie:
```bash
make clean && make
```

Testy regresji ROM-u (headless, jsnes + Node – patrz `tests/nes/README.md`):
```bash
cd ../tests/nes && npm install && npm run setup && npm test
```

---

## 📺 Uruchamianie na Komputerze i Konsoli

Plik `nes/dog_tamagotchi.nes` jest w 100% zgodny ze standardem iNES Mapper 0. Możesz go uruchomić na:
* **macOS:** OpenEmu, Mesen, RetroArch, Nestopia, FCEUX
* **Windows / Linux:** Mesen, FCEUX, RetroArch
* **Prawdziwy NES / Famicom:** Flashcart EverDrive N8 / PowerPak
* **Przeglądarka:** otwórz `play.html` (podwójne kliknięcie) – ROM jest wbudowany w stronę razem z emulatorem jsnes. Klawiatura: strzałki = D-Pad (trzymaj `GÓRA` przy misce!), `Spacja`/`Z` = A, `X`/`B` = B, `Shift` = Select, `Enter` = Start.

Mapowanie klawiszy znajduje się w pliku `play.html`; zachowanie gry weryfikują testy regresji z `tests/nes/`.
