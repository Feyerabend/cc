CC = gcc
CFLAGS = -Wall -O2



all: solid wireframe merge

solid: solid.c
	$(CC) $(CFLAGS) -o solid solid.c
	./solid

wireframe: wireframe.c
	$(CC) $(CFLAGS) -o wireframe wireframe.c
	./wireframe

merge: pam7merge.py
	python3 pam7merge.py

clean:
	rm -f solid wireframe *.pam animation.gif