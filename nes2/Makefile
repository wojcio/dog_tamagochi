CC65 = cc65
CA65 = ca65
LD65 = ld65

TARGET = dog_tamagotchi2.nes
CC65_PATH = /opt/homebrew/opt/cc65/share/cc65

all: $(TARGET) web

graphics2.chr: tools/make_chr2.py
	python3 tools/make_chr2.py graphics2.chr

world2_data.h world2_data.c: tools/make_world2.py
	python3 tools/make_world2.py

neslib.o: neslib.s graphics2.chr
	$(CA65) neslib.s -o neslib.o

main.s: main.c neslib.h nesdoug.h world2_data.h
	$(CC65) -O -t nes -I . main.c -o main.s

main.o: main.s
	$(CA65) main.s -o main.o

nesdoug.s: nesdoug.c nesdoug.h neslib.h
	$(CC65) -O -t nes -I . nesdoug.c -o nesdoug.s

nesdoug.o: nesdoug.s
	$(CA65) nesdoug.s -o nesdoug.o

world2_data.s: world2_data.c world2_data.h
	$(CC65) -O -t nes -I . world2_data.c -o world2_data.s

world2_data.o: world2_data.s
	$(CA65) world2_data.s -o world2_data.o

$(TARGET): nes.cfg neslib.o main.o nesdoug.o world2_data.o
	$(LD65) -C nes.cfg neslib.o main.o nesdoug.o world2_data.o $(CC65_PATH)/lib/none.lib -o $(TARGET)
	@echo "========================================================="
	@echo "🎮 SUCCESS: Built $(TARGET) (NES2 C Edition with Bitmaps)!"
	@echo "========================================================="

# Refresh the base64 ROM embedded in the browser page so play2.html never rots
web: $(TARGET)
	python3 tools/embed_rom.py $(TARGET) play2.html

clean:
	rm -f neslib.o main.o nesdoug.o world2_data.o main.s nesdoug.s world2_data.s $(TARGET) graphics2.chr world2_data.h world2_data.c

.PHONY: all clean web
