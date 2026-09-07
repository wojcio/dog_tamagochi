# ==============================================================================
# 🐕 DOG TAMAGOTCHI 2D PLATFORMER - NES MAKEFILE
# Targets: ca65 / ld65 (cc65 suite) -> dog_tamagotchi.nes (NROM-256)
# ==============================================================================

CA65 = ca65
LD65 = ld65
PYTHON = python3

TARGET = dog_tamagotchi.nes
CFG = nes.cfg

SOURCES = main.s header.s
OBJECTS = main.o header.o
INCLUDES = constants.inc input.s apu.s ppu.s world.s dog.s tamagotchi.s
CHR = graphics.chr
WORLD_DATA = screen_0.bin screen_1.bin world_cols.bin

all: $(TARGET)

$(CHR): tools/make_chr.py
	$(PYTHON) tools/make_chr.py $(CHR)

$(WORLD_DATA): tools/make_world.py
	$(PYTHON) tools/make_world.py

header.o: header.s
	$(CA65) header.s -o header.o

main.o: main.s $(INCLUDES) $(CHR) $(WORLD_DATA)
	$(CA65) main.s -o main.o

$(TARGET): $(CFG) header.o main.o
	$(LD65) -C $(CFG) header.o main.o -o $(TARGET)
	@echo "========================================================="
	@echo "🎮 SUCCESS: Built $(TARGET) for Nintendo NES!"
	@echo "========================================================="

clean:
	rm -f $(OBJECTS) $(TARGET) $(CHR) $(WORLD_DATA)

.PHONY: all clean
