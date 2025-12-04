CC		= gcc
CFLAGS		= -Wall
LDFLAGS		=
OBJFILES	= main.o vm2.o
TARGET		= main

all: $(TARGET)

$(TARGET): $(OBJFILES)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJFILES) $(LDFLAGS)

clean:
	rm -f $(OBJFILES) $(TARGET) *~
