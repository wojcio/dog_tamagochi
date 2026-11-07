---
title: "🐕 Dog Tamagotchi 2D Platformer - Konsolowy Symulator Psa"
date: 2026-08-30
tags:
  - gamedev
  - python
  - ascii-art
  - tamagotchi
  - retro
  - pc-speaker
  - platformer
  - biomes
  - tricks
  - agility
  - sleep
aliases:
  - Dog Tamagotchi
  - Piesek ASCII
type: project
status: completed
tech_stack:
  - Python 3.9+
  - ANSI Escape Sequences (Double Buffering)
  - PCM Wave Synthesis (1-bit PC Speaker)
  - Raw Termios / TTY
---

# 🐕 Dog Tamagotchi 2D Platformer (Wersja Kompletna)

> [!abstract] Podsumowanie Projektu
> Rozbudowany, konsolowy symulator psa **Tamagotchi** połączony z dynamiczną **platformówką 2D w kolorowym ASCII Art**. Świat gry rozciąga się na **8 zróżnicowanych biomów**, zawiera płynny **cykl dnia i nocy**, **system sztuczek z poziomami XP**, **sklepik z akcesoriami u Pana Ogrodnika**, **drabinki parkourowe na drzewa i dachy**, **mechanikę regeneracyjnego snu w budzie**, **pływanie w rzece**, **przechodzenie przez ulicę na pasach** oraz **tor przeszkód Agility** z inteligentnym stoperem czasu. Całość udźwiękowiona jest autorskim syntezatorem fal prostokątnych **PC Speaker (8-bit chiptune)**.

---

## 🚀 Instalacja i Uruchomienie

Wymagania: **Python 3.9+**, terminal un*x-owy (macOS / Linux), terminal ≥ 100×24.
Zapisy trafiają do `~/.dog_tamagotchi/save.json`.

```bash
# Opcja 1 (rekomendowana): instalacja pakietu z komendą `piesek`
pip install -e .
piesek

# Opcja 2: bez instalacji, prosto z repozytorium
python3 main.py
```

Tryb developerski (`pip install -e .`) linkuje kod z repozytorium – zmiany w
plikach są widoczne natychmiast, bez reinstalacji. Pakiet instaluje wyłącznie
grę pythonową (`game/` + `main.py`); katalogi `nes/` i `nes2/` to osobne
projekty cc65 budowane przez `make` (szczegóły w ich README).

Testy:
```bash
python3 tests/test_render_diff.py        # silnik renderowania (emulator VT)
python3 tests/test_biomes.py             # 8 biomów: pływanie, ruch uliczny, NPC, zapis v2
python3 tests/run_pty_zone_walk.py       # żywy test pty: adopcja + przemarsz przez wszystkie biomy
cd tests/nes && npm install && npm run setup && npm test   # ROM-y NES (jsnes)
```

---

## 🛏️ Mechanika Snu i Regeneracji w Budzie `[Z] / [Q]`

> [!tip] Jak Odnowić Energię i Usunąć Zmęczenie:
> 1. **Powrót do Domu:** Piesek musi podejść do swojej budy `🏠` w Ogrodzie (początek mapy, `x: 3–17`).
> 2. **Kocyk i Sen:** Wciśnięcie klawisza **`[Z]`** lub **`[Q]`** kładzie pieska na miękkim kocyku w budzie.
> 3. **Szybka Regeneracja:** Podczas snu energia `⚡` szybko wraca do **100%**, regeneruje się szczęście i odtwarzana jest spokojna 8-bitowa kołysanka.
> 4. **Pobudka:** Po pełnym naładowaniu energii piesek automatycznie się budzi radosnym komunikatem: `⚡ Wypoczęty i gotowy na sztuczki! ☀️`.
> 5. **Zabezpieczenie:** Próba zaśnięcia poza budą wyświetla przypomnienie: *"Muszę wrócić do budy 🏠, żeby się wyspać!"*.

---

## 🗺️ 8 Połączonych Biomów Świata (840 kolumn szerokości)

```text
                \ | /                                  .---.
               --(☀)--                                 (  ☁  )
                / | \                                  `---'
 [ OGRÓD & DOM ]   [ LAS 🌲 ]    [   RZEKA 🌊   ]  [ PARK MIEJSKI ]   [ PSI PARK 🎾 ]    [   ULICA 🚗   ]   [ SŁONECZNA PLAŻA ]    [ TOR AGILITY ]
┌──────────┐                 ,~~.                            ┌─┴─────┐
│ SKLEPIK 🦴│    ▲   |≡|≈   ( ● )  ~≈~🛶(===)~≈~  🦆    │PSI PARK│   ▄──────▄   /----\  ⛱️
│ 🎩🎀🕶️👑 │   ▲▲▲ /===\  ~≈~    ~≈~🪨  ~≈~     ⛲   └───┬─────┘  🚗 ║ZEBRA║  /______\   ╔════════╗
└──────────┘  ▲▲▲ | | 🐿️ ~≈~🦆 kamienie ~≈~🪨   🌉    ●●●[]  ⚽  🚓 ▀▀▀▀▀▀   |  [___/ ] |  ║ 🏁START║  ||||  [====]  ( ⭕ )  ║ 🏆META ║
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
 w  🌸 W  v   ·W·pine·   ~≈~ kaczki ~≈~   ~≈strumień~≈   🎾 W W 🎾 W   ▂█▂pasy▂█▂░   ░▒ piasek ░▒ ~≈~   =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_
 x:0          105         210              315             420          525           630             735          840
```

1. 🏡 **Ogród & Dom (x: 0–105):** Buda z kocykiem do snu `🏠`, miski z karmą `🥣`, hydrant `🚰` oraz stragan **Sklepiku u Pana Ogrodnika `👨‍🌾`**.
2. 🌲 **Las (x: 105–210):** Parkour po koronach sosien `▲`, przewrócone kłody z kośćmi w korze, muchomory `🍄`, paprocie, **Leśniczy** na spacerze, **wiewiórki** `🐿️` (obszczekaj je!) oraz świetliki `✦` nocą między drzewami.
3. 🌊 **Rzeka (x: 210–315):** Pływaj! Wejdź do wody między brzegami — piesek płynie `🏊` (wolniej, pluska łapkami, po wyjściu trzęsie mokrym futrem `💦`). Sucha trasa prowadzi po kamieniach i liściach grążeli, **dryfująca kłoda** wiezie psa na drugą stronę, kaczki `🦆` przepływają rzekę, a ryba `🐟` czeka na środku.
4. 🌳 **Park Miejski & Mostek (x: 315–420):** Dębowa aleja, fontanna tryskająca wodą `⛲`, wysoki drewniany mostek nad strumieniem `🌉`, pikniki i spacerowicze.
5. 🎾 **Psi Park / Wybieg dla Psów (x: 420–525):** Ogrodzenie z bramą, **Aleja 6 Hydrantów** (oznacz wszystkie klawiszem `S` → bonus +5🦴 +20 XP!), dołek z piłkami, tunel oraz **psie kumple** (Burek, Luna, Azor) — obszczekaj ich `B`, a zaproszą Cię do wspólnych zoomies 🎾💨.
6. 🚗 **Ulica (x: 525–630):** Jeżdżą samochody! Sygnalizacja cyklicznie zatrzymuje je na **zebrze** — przejdź po pasach przy zielonem świetle, a dostaniesz +5 XP za bezpieczne przejście 🚸. Samochód tylko straszy (`BZZZ!`, −5 szczęścia), bez gryzienia. Koty obserwują z płotu, wiewiórka próbuje przebiec przez jezdnię.
7. 🏖️ **Słoneczna Plaża dla Psów (x: 630–735):** Złocisty piasek `░▒░`, kolorowe parasole `⛱️`, leżaki, szum morskich fal `~≈~` oraz uciekające kraby `🦀`!
8. 🏆 **Tor Przeszkód Agility (x: 735–840):** Brama startowa `[🏁 START]`, płotki `[====]`, tyczki do slalomu `🚩`, obręcz `( ⭕ )`, brama mety `[🏆 META]` oraz stoper z automatycznym resetem przy cofnięciu się za linię startu.

---


## 🐶 Grywalne Rasy Psów

| Rasa | Ikona | Styl i cechy charakterystyczne |
| :--- | :---: | :--- |
| **Corgi** | 🦊 | Krótkie łapki, biały brzuszek, merdający kuper, radosny charakter |
| **Jamnik** | 🌭 | Podłużny tułów (`=`), niska sylwetka, sprytny tropiciel |
| **Seter Irlandzki** | 🐕 | Głęboki mahoniowy kolor (`ANSI 166/208`), powiewny pióropusz na ogonie (`~>`) i łapach |
| **Shiba Inu (Pieseł)** | 🐺 | Złocisty odcień, pyszczek `(•ᴥ•)`, zakręcony ogon `@`, *much wow* |
| **Pudel** | 🐩 | Kędzierzawa fryzurka `888`, różowe akcenty, elegancja |

---

## ☀️ Cykl Dnia i Nocy (Day / Night Cycle)

Płynna zmiana pór dnia wpływająca na atmosferę, paletę kolorów i oświetlenie:
- 🌅 **Świt / Poranek:** Różowo-złociste niebo, budzący się park.
- ☀️ **Słoneczne Południe:** Jasny błękit nieba, żywe kolory trawy i kwiatów.
- 🌇 **Zachód Słońca:** Pomarańczowo-bursztynowa łuna, latarnie powoli rozbłyskają.
- 🌙 **Gwiaździsta Noc:** Głęboki granat nieba, świecący księżyc `🌙`, migoczące gwiazdy `✦ ★ *` oraz automatycznie świecące latarnie `💡`.

---

## 🎪 Akademia Sztuczek & Poziomy XP `[T]`

Piesek zdobywa punkty doświadczenia (XP) za spacery, jedzenie, pieszczoty, sztuczki i ukończenie toru agility:

| Klawisz | Sztuczka | Wymagany Poziom | Opis i Animacja |
| :---: | :--- | :---: | :--- |
| **`1`** | **Siad!** 🧘 | Poz. 1 | Piesek grzecznie siada i macha ogonkiem |
| **`2`** | **Daj łapę!** 🐾 | Poz. 2 | Wyciąga przednią łapkę z uśmiechem |
| **`3`** | **Turlaj się!** 🌀 | Poz. 3 | Dynamiczny obrót 360° na trawie |
| **`4`** | **Superskok!** 🦘 | Poz. 4 | Wysoki skok akrobatyczny z wyskoku |
| **`5`** | **Zdechł pies!** 🎭 | Poz. 5 | Komiczne leżenie łapkami w górę `(x_x)` |

---

## 👨‍🌾 Sklepik u Pana Ogrodnika `[K]`

Gracz zbiera **Psie Kostki `🦴`** (zjadanie przysmaków, wykonywanie sztuczek, rekordy agility) i może kupować oraz zakładać stylowe nakrycia głowy widoczne bezpośrednio na sprite'ie psa:

* 🎩 **Cylinder Gentelmana** (5 🦴)
* 🎀 **Różowa Kokardka** (4 🦴)
* 🕶️ **Stylowe Okulary Thug Life** (6 🦴)
* 👑 **Złota Korona Króla Parku** (10 🦴)
* 🧣 **Ciepły Szalik** (4 🦴)

---

## 📋 Codzienne Zadania `[R]`

Każdego dnia piesek dostaje **3 losowe zadania** (nowy zestaw o północy 🌅) z nagrodami w kostkach 🦴 i XP. Obok klasyków (karmienie, głaskanie, sztuczki, piłka) pojawiły się zadania terenowe dla nowych biomów:

| Zadanie | Biom | Cel |
| :--- | :--- | :--- |
| 🐿️ Obszczekaj wiewiórki | Las / Ulica | 2–4 sztuki |
| 🏊 Popływaj w rzece | Rzeka | 2–5 wejść do wody |
| 🚸 Przejdź przez pasy | Ulica | 2–4 bezpieczne przejścia |
| 🎾 Baw się z psimi kumplami | Psi Park | 2–3 sesje zoomies |

---

## ⌨️ Pełna Klawiszologia

| Klawisz | Akcja |
| :---: | :--- |
| **`←` / `→`** lub **`A` / `D`** | Poruszanie się w lewo / w prawo |
| **`↑` / `W`** lub **`Spacja`** | Skok na platformy, dachy i gałęzie |
| **`↓` / `S` (na platformie)** | Zeskoczenie z platformy w dół |
| **`B` / `H`** | Szczekanie (`HAU! HAU!`) — płoszy wiewiórki 🐿️, zaprasza psie kumple do zabawy 🎾, robi plusk nad rzeką |
| **`↑` / `W` / `Spacja` (w wodzie)** | Pluskanie łapkami w stylu dowolnym 🏊 — na powierzchni skok zamienia się w wesołe plum! |
| **`Z` / `Q` (przy budzie)** | **Położenie się spać w budzie i regeneracja energii 💤** |
| **`T`** | Otwarcie / zamknięcie menu Akademii Sztuczek |
| **`1` – `5`** | Bezpośrednie wykonanie sztuczki |
| **`K`** | Otwarcie / zamknięcie Sklepiku z nakryciami głowy |
| **`E`** | Poproszenie spacerowicza o pogłaskanie (`♥`) |
| **`S` (na ziemi)** | Oznaczenie terenu / Zrobienie siku (`💧`) |
| **`M`** | Wyciszenie / włączenie dźwięków PC Speakera 🔊/🔇 |
| **`P`** | Pauza |
| **`ESC`** | Powrót do menu wyboru rasy / Wyjście |

---

## 📐 Viewport i Porównanie z Klasykami (ZZT / Super ZZT)

| Parametr | **ZZT (1991)** | **Super ZZT (1992)** | **Dog Tamagotchi (Ten Projekt)** |
| :--- | :---: | :---: | :---: |
| **Rozmiar okna / Terminala** | `80 × 25` | `80 × 25` | **`105 × 28`** *(panoramiczny)* |
| **Rozmiar Viewportu Świata** | `60 × 25` *(statyczny)* | `40 × 25` *(scrolling)* | **`105 × 20`** *(płynny 2D scrolling)* |
| **Całkowita szerokość świata** | 60 kafli | 96 kafli | **`840` kolumn** *(8 biomów)* |
| **Układ panelu HUD** | Po prawej (`20 × 25`) | Po prawej (`40 × 25`) | **Na dole ekranu (`105 × 8`)** |
| **Paleta kolorów** | 16 kolorów DOS | 16 kolorów DOS | **256 kolorów ANSI** |
| **Buforowanie klatek** | Zapis do VRAM B800h | Zapis do VRAM B800h | **ANSI Double Buffering (0 migotania)** |
