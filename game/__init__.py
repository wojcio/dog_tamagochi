"""🐕 Dog Tamagotchi 2D Platformer — silnik gry terminalowej.

Moduły:
    engine   — terminal ANSI, renderer diff, kolory
    dog      — rasy, sztuczki, sklep, stan psa
    world    — świat, biom, przeszkody, przedmioty
    npc      — NPC (ludzie, gołębie, kot, krab)
    ui       — renderowanie HUD/animacji, menu
    audio    — syntezowane dźwięki (afplay/sox, cisza gdy niedostępne)
    save     — zapisy w ~/.dog_tamagotchi/save.json (atomowy, kwarantanna)
    quests   — codzienne misje (3 dziennie, deterministyczny seed)
"""

__version__ = "1.0.0"
