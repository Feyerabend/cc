
CC				= gcc
CFLAGS		= -Wall
LDFLAGS		=
OBJFILES	= forth.o
TARGET		= forth

all: $(TARGET)

runvm: forth.o
	$(CC) $(CFLAGS) -o forth forth.o $(LDFLAGS)

clean:
	rm -f $(OBJFILES) $(TARGET) *~
