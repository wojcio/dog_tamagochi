# 🐕 Dog Tamagotchi 2D Platformer – NES2 (Edycja C & Bitmap Pixel Art)

Druga, bogatsza graficznie wersja portu NES: napisana w **C (cc65)** z
bitmapową grafiką w stylu Super Mario Bros, płynnym przewijaniem wielu biomów
i strumieniowaniem atrybutów w VBlank.

* **Format:** iNES 1.0, Mapper 0 (NROM-256), 32 KB PRG + 8 KB CHR
* **Runtime:** neslib (własny runtime assembly z NMI w `neslib.s`) + nesdoug
* **HUD:** migawany w przerwaniu NMI ze sprawdzaniem zmian (`hud_refresh`) –
  liczniki kości i paski potrzeb odświeżają się tylko, gdy wartość drgnie

---

## 🕹️ Sterowanie

| Klawisz NES | Akcja |
| :---: | :--- |
| **`D-Pad Lewo / Prawo`** | Bieg (camera scroll przez 4 biomy) |
| **`A`** | Skok |
| **`B`** | Szczekanie `HAU!` |
| **`GÓRA` (przy misce 🥣)** | **Jedzenie – regeneracja głodu** (miska stoi przy budzie, kol. 6 mapy) |
| **`DÓŁ` (przy budzie, na ziemi)** | Sen 💤 – regeneracja energii (pies budzi się sam przy 100%) |
| **`A / B / START / GÓRA` (we śnie)** | Pobudka |

Piłka do zabawy: jedno kopnięcie = jeden dźwięk (30-klatkowa przerwa),
tak jak w wersji Pythonowej.

## 🛠️ Budowanie

Wymaga `cc65` (brew install cc65):

```bash
cd nes2
make            # buduje ROM i odświeża play2.html (cel web)
```

Wyniki: `dog_tamagotchi2.nes` + `play2.html` (strona z wbudowanym ROM-em,
działa offline z dysku).

Klawiatura w przeglądarce: strzałki = D-Pad (`GÓRA` = karmienie), `Spacja`/`Z` = A,
`X`/`B` = B, `Shift` = Select, `Enter` = Start. WASD też działa (Uwaga: `W` = A/skok).

## 🧪 Testy

Zarówno ten ROM, jak i wersja `nes/`, przechodzą testy regresji headless
(jsnes + Node, sterowanie skryptem + asercje na RAM i nametable):

```bash
cd ../tests/nes && npm install && npm run setup && npm test
```
