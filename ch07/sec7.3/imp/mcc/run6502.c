/* Test harness for running 6502 compiled code */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "fake6502.h"

uint8_t memory[65536];

uint8_t read6502(uint16_t address) {
    return memory[address];
}

void write6502(uint16_t address, uint8_t value) {
    memory[address] = value;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: run6502 <binary>\n");
        return 1;
    }
    
    memset(memory, 0, 65536);
    
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) {
        fprintf(stderr, "Cannot open: %s\n", argv[1]);
        return 1;
    }
    
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    fread(&memory[0x0600], 1, size, fp);
    fclose(fp);
    
    // Start at beginning of program (runtime initialization)
    memory[0xFFFC] = 0x00;
    memory[0xFFFD] = 0x06;
    
    reset6502();
    
    printf("Running 6502 code starting at $0600...\n");
    printf("Initial: PC=%04X A=%02X X=%02X Y=%02X SP=%02X\n", 
           PC, A, X, Y, SP);
    
    int cycles = 0;
    int max_cycles = 1000000;
    
    while (cycles < max_cycles) {
        uint8_t opcode = read6502(PC);
        
        if (opcode == 0x00) {
            printf("BRK encountered at PC=%04X\n", PC);
            break;
        }
        
        int ticks = step6502();
        cycles += ticks;
        
        if (PC == 0xFFFF || PC == 0x0000) {
            printf("PC went to invalid address: %04X\n", PC);
            break;
        }
    }
    
    printf("\nFinal: PC=%04X A=%02X X=%02X Y=%02X SP=%02X\n", 
           PC, A, X, Y, SP);
    printf("Total cycles: %d\n", cycles);
    
    return 0;
}
