# Makefile for Huffman Coding Compression and Decompression

CC = gcc
CFLAGS = -Wall -O2

all: compress decompress

compress: compress.c
	$(CC) $(CFLAGS) compress.c -o compress

decompress: decompress.c
	$(CC) $(CFLAGS) decompress.c -o decompress

clean:
	rm -f compress decompress
