/*
 * Main runner for 6502 tail-recursive Fibonacci
 * 
 * Compile:
 *   gcc -o run6502 main.c fake6502.c -I.
 * 
 * Usage:
 *   python3 asm.py fib_tail.asm fib.bin
 *   ./run6502 fib.bin
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "fake6502.h"

// 64KB memory
static uint8_t memory[65536];

// Memory interface for fake6502
uint8_t read6502(uint16_t address) {
    return memory[address];
}

void write6502(uint16_t address, uint8_t value) {
    memory[address] = value;
}

// Load binary ROM file into memory at specified address
int load_rom(const char *filename, uint16_t load_addr) {
    FILE *f = fopen(filename, "rb");
    if (!f) {
        fprintf(stderr, "Error: Cannot open %s\n", filename);
        return -1;
    }
    
    // Get file size
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    // Read into memory
    size_t bytes_read = fread(&memory[load_addr], 1, size, f);
    fclose(f);
    
    printf("Loaded %zu bytes at $%04X\n", bytes_read, load_addr);
    return bytes_read;
}

int main(int argc, char *argv[]) {
    const char *rom_file = "fib.bin";
    
    if (argc > 1) {
        rom_file = argv[1];
    }
    
    printf("6502 Tail-Recursive Fibonacci Emulator\n");
    printf("=======================================\n\n");
    
    // Clear memory
    memset(memory, 0, sizeof(memory));
    
    // Load ROM at $8000
    if (load_rom(rom_file, 0x8000) < 0) {
        return 1;
    }
    
    // Initialize CPU
    reset6502();
    
    printf("\nStarting execution...\n");
    printf("Initial state: PC=$%04X A=$%02X X=$%02X Y=$%02X SP=$%02X\n",
           PC, A, X, Y, SP);
    
    // Run until we hit the halt loop (PC loops back to same address)
    int max_steps = 100000;
    int steps = 0;
    uint16_t last_pc = 0;
    int halt_count = 0;
    
    while (steps < max_steps) {
        uint16_t current_pc = PC;
        
        // Check if we're in a halt loop (JMP to self)
        if (current_pc == last_pc) {
            halt_count++;
            if (halt_count > 2) {
                printf("\nHalted at PC=$%04X (infinite loop detected)\n", PC);
                break;
            }
        } else {
            halt_count = 0;
        }
        
        last_pc = current_pc;
        
        // Execute one instruction
        step6502();
        steps++;
        
        // Optional: trace execution (uncomment for debugging)
        // printf("[$%04X] A=%02X X=%02X Y=%02X SP=%02X\n", 
        //        current_pc, A, X, Y, SP);
    }
    
    printf("Executed %d instructions\n\n", steps);
    
    // Display result
    uint8_t result = memory[0x0200];
    printf("Results:\n");
    printf("--------\n");
    printf("F(10) = %d (stored at $0200)\n", result);
    printf("\nFinal CPU state:\n");
    printf("  PC = $%04X\n", PC);
    printf("  A  = $%02X (%d)\n", A, A);
    printf("  X  = $%02X (%d)\n", X, X);
    printf("  Y  = $%02X (%d)\n", Y, Y);
    printf("  SP = $%02X\n", SP);
    printf("  P  = $%02X (", getP());
    uint8_t p = getP();
    printf("%c%c-%c%c%c%c)\n",
           (p & 0x80) ? 'N' : 'n',
           (p & 0x40) ? 'V' : 'v',
           (p & 0x08) ? 'D' : 'd',
           (p & 0x04) ? 'I' : 'i',
           (p & 0x02) ? 'Z' : 'z',
           (p & 0x01) ? 'C' : 'c');
    
    // Verify result
    printf("\nVerification:\n");
    printf("F(10) should be 55\n");
    if (result == 55) {
        printf("✓ PASS: Result is correct!\n");
        return 0;
    } else {
        printf("✗ FAIL: Expected 55, got %d\n", result);
        return 1;
    }
}

