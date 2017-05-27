default: build upload

build:
	avr-gcc -g -Os -mmcu=attiny84 -c noisEE.c
	avr-gcc -g -mmcu=attiny84 -o noisEE.elf noisEE.o
	avr-objcopy -j .text -j .data -O ihex noisEE.elf noisEE.hex

upload:
	avrdude -c avrispmkII -p attiny84 -P usb -U "flash:w:noisEE.hex:i"
