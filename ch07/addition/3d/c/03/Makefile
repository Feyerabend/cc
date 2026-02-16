CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c99
LDFLAGS = -lm

TARGET = obj_animator
SRC = obj_animator.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET)
	rm -f frame_*.pam
	rm -f *.gif

test: $(TARGET)
	./$(TARGET) test_cube.obj frame 36 800 600

animate: test
	python3 pam_to_gif.py "frame_*.pam" animation.gif 100 0

.PHONY: all clean test animate
