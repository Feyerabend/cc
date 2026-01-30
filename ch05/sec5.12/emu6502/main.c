/*
 * Main driver for fake6502 emulator with interactive monitor
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include "fake6502.h"

// Memory map:
// $0000-$00FF: Zero page (including runtime temps at $00F0-$00FF)
// $0100-$01FF: Stack
// $0200-$03FF: Variables
// $0400-$07FF: Arrays
// $0800-$EFFF: Program code
// $F000-$F0FF: I/O area
// $F001: Console output
// $F002: Console input (status)
// $F003: Console input (data)

#define RAM_SIZE 65536
#define CODE_START 0x0800
#define CONSOLE_OUT 0xF001
#define CONSOLE_IN_STATUS 0xF002
#define CONSOLE_IN_DATA 0xF003
#define MAX_BREAKPOINTS 16

static uint8_t RAM[RAM_SIZE];
static int running = 1;
static int cycles = 0;
static int monitor_mode = 1;  // Start in monitor mode
static int trace_mode = 0;

// Breakpoint management
static uint16_t breakpoints[MAX_BREAKPOINTS];
static int num_breakpoints = 0;

// Opcode mnemonics table
static const char *mnemonics[256] = {
    "BRK","ORA","JAM","SLO","NOP","ORA","ASL","SLO","PHP","ORA","ASL","ANC","NOP","ORA","ASL","SLO",
    "BPL","ORA","JAM","SLO","NOP","ORA","ASL","SLO","CLC","ORA","NOP","SLO","NOP","ORA","ASL","SLO",
    "JSR","AND","JAM","RLA","BIT","AND","ROL","RLA","PLP","AND","ROL","ANC","BIT","AND","ROL","RLA",
    "BMI","AND","JAM","RLA","NOP","AND","ROL","RLA","SEC","AND","NOP","RLA","NOP","AND","ROL","RLA",
    "RTI","EOR","JAM","SRE","NOP","EOR","LSR","SRE","PHA","EOR","LSR","ALR","JMP","EOR","LSR","SRE",
    "BVC","EOR","JAM","SRE","NOP","EOR","LSR","SRE","CLI","EOR","NOP","SRE","NOP","EOR","LSR","SRE",
    "RTS","ADC","JAM","RRA","NOP","ADC","ROR","RRA","PLA","ADC","ROR","ARR","JMP","ADC","ROR","RRA",
    "BVS","ADC","JAM","RRA","NOP","ADC","ROR","RRA","SEI","ADC","NOP","RRA","NOP","ADC","ROR","RRA",
    "NOP","STA","NOP","SAX","STY","STA","STX","SAX","DEY","NOP","TXA","ANE","STY","STA","STX","SAX",
    "BCC","STA","JAM","SHA","STY","STA","STX","SAX","TYA","STA","TXS","TAS","SHY","STA","SHX","SHA",
    "LDY","LDA","LDX","LAX","LDY","LDA","LDX","LAX","TAY","LDA","TAX","LXA","LDY","LDA","LDX","LAX",
    "BCS","LDA","JAM","LAX","LDY","LDA","LDX","LAX","CLV","LDA","TSX","LAS","LDY","LDA","LDX","LAX",
    "CPY","CMP","NOP","DCP","CPY","CMP","DEC","DCP","INY","CMP","DEX","SBX","CPY","CMP","DEC","DCP",
    "BNE","CMP","JAM","DCP","NOP","CMP","DEC","DCP","CLD","CMP","NOP","DCP","NOP","CMP","DEC","DCP",
    "CPX","SBC","NOP","ISC","CPX","SBC","INC","ISC","INX","SBC","NOP","SBC","CPX","SBC","INC","ISC",
    "BEQ","SBC","JAM","ISC","NOP","SBC","INC","ISC","SED","SBC","NOP","ISC","NOP","SBC","INC","ISC"
};

// Addressing mode info: 0=impl, 1=imm, 2=zp, 3=zpx, 4=zpy, 5=abs, 6=absx, 7=absy, 8=ind, 9=indx, 10=indy, 11=rel, 12=acc
static const uint8_t addr_modes[256] = {
    0,9,0,9,2,2,2,2,0,1,12,1,5,5,5,5,
    11,10,0,10,3,3,3,3,0,7,0,7,6,6,6,6,
    5,9,0,9,2,2,2,2,0,1,12,1,5,5,5,5,
    11,10,0,10,3,3,3,3,0,7,0,7,6,6,6,6,
    0,9,0,9,2,2,2,2,0,1,12,1,5,5,5,5,
    11,10,0,10,3,3,3,3,0,7,0,7,6,6,6,6,
    0,9,0,9,2,2,2,2,0,1,12,1,8,5,5,5,
    11,10,0,10,3,3,3,3,0,7,0,7,6,6,6,6,
    1,9,1,9,2,2,2,2,0,1,0,1,5,5,5,5,
    11,10,0,10,3,3,4,4,0,7,0,7,6,6,7,7,
    1,9,1,9,2,2,2,2,0,1,0,1,5,5,5,5,
    11,10,0,10,3,3,4,4,0,7,0,7,6,6,7,7,
    1,9,1,9,2,2,2,2,0,1,0,1,5,5,5,5,
    11,10,0,10,3,3,3,3,0,7,0,7,6,6,6,6,
    1,9,1,9,2,2,2,2,0,1,0,1,5,5,5,5,
    11,10,0,10,3,3,3,3,0,7,0,7,6,6,6,6
};

static const uint8_t instr_lengths[13] = {1, 2, 2, 2, 2, 3, 3, 3, 3, 2, 2, 2, 1};

// Read from memory
uint8_t read6502(uint16_t address) {
    if (address == CONSOLE_IN_STATUS) {
        return 0;
    }
    if (address == CONSOLE_IN_DATA) {
        return 0;
    }
    return RAM[address];
}

// Write to memory
void write6502(uint16_t address, uint8_t value) {
    if (address == CONSOLE_OUT) {
        putchar(value);
        fflush(stdout);
        return;
    }
    RAM[address] = value;
}

// Load binary file into memory at specified address
int load_binary(const char *filename, uint16_t start_addr) {
    FILE *f = fopen(filename, "rb");
    if (!f) {
        fprintf(stderr, "Error: Cannot open file '%s'\n", filename);
        return -1;
    }
    
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    if (size <= 0 || size > 65536 - start_addr) {
        fprintf(stderr, "Error: Invalid file size %ld\n", size);
        fclose(f);
        return -1;
    }
    
    size_t bytes_read = fread(&RAM[start_addr], 1, size, f);
    fclose(f);
    
    if ((long)(bytes_read) != size) {
        fprintf(stderr, "Error: Read %zu bytes, expected %ld\n", bytes_read, size);
        return -1;
    }
    
    printf("Loaded %ld bytes at $%04X\n", size, start_addr);
    return (int)size;
}

// Disassemble one instruction
int disassemble_instruction(uint16_t addr, char *buffer, size_t bufsize) {
    uint8_t opcode = RAM[addr];
    uint8_t mode = addr_modes[opcode];
    int len = instr_lengths[mode];
    
    const char *mnemonic = mnemonics[opcode];
    
    char operand[32] = "";
    uint8_t b1 = (addr + 1 < RAM_SIZE) ? RAM[addr + 1] : 0;
    uint8_t b2 = (addr + 2 < RAM_SIZE) ? RAM[addr + 2] : 0;
    uint16_t word = b1 | (b2 << 8);
    
    switch (mode) {
        case 0:  // Implied
            strcpy(operand, "");
            break;
        case 1:  // Immediate
            snprintf(operand, sizeof(operand), "#$%02X", b1);
            break;
        case 2:  // Zero page
            snprintf(operand, sizeof(operand), "$%02X", b1);
            break;
        case 3:  // Zero page,X
            snprintf(operand, sizeof(operand), "$%02X,X", b1);
            break;
        case 4:  // Zero page,Y
            snprintf(operand, sizeof(operand), "$%02X,Y", b1);
            break;
        case 5:  // Absolute
            snprintf(operand, sizeof(operand), "$%04X", word);
            break;
        case 6:  // Absolute,X
            snprintf(operand, sizeof(operand), "$%04X,X", word);
            break;
        case 7:  // Absolute,Y
            snprintf(operand, sizeof(operand), "$%04X,Y", word);
            break;
        case 8:  // Indirect
            snprintf(operand, sizeof(operand), "($%04X)", word);
            break;
        case 9:  // (Indirect,X)
            snprintf(operand, sizeof(operand), "($%02X,X)", b1);
            break;
        case 10: // (Indirect),Y
            snprintf(operand, sizeof(operand), "($%02X),Y", b1);
            break;
        case 11: // Relative
            {
                int8_t offset = (int8_t)b1;
                uint16_t target = addr + 2 + offset;
                snprintf(operand, sizeof(operand), "$%04X", target);
            }
            break;
        case 12: // Accumulator
            strcpy(operand, "A");
            break;
    }
    
    // Format the full instruction
    char bytes[16] = "";
    for (int i = 0; i < len; i++) {
        char tmp[8];
        snprintf(tmp, sizeof(tmp), "%02X ", RAM[addr + i]);
        strcat(bytes, tmp);
    }
    
    snprintf(buffer, bufsize, "$%04X: %-9s%-4s %-12s", 
             addr, bytes, mnemonic, operand);
    
    return len;
}

// Display registers
void display_registers(void) {
    printf("PC=$%04X  SP=$%02X  A=$%02X  X=$%02X  Y=$%02X  ", PC, SP, A, X, Y);
    
    uint8_t flags = getP();
    printf("P=$%02X [", flags);
    printf("%c", (flags & 0x80) ? 'N' : 'n');
    printf("%c", (flags & 0x40) ? 'V' : 'v');
    printf("-");
    printf("-");
    printf("%c", (flags & 0x08) ? 'D' : 'd');
    printf("%c", (flags & 0x04) ? 'I' : 'i');
    printf("%c", (flags & 0x02) ? 'Z' : 'z');
    printf("%c", (flags & 0x01) ? 'C' : 'c');
    printf("]\n");
}

// Dump memory region
void dump_memory(uint16_t start, uint16_t end) {
    for (uint16_t addr = start; addr <= end; addr += 16) {
        printf("%04X: ", addr);
        for (int i = 0; i < 16 && addr + i <= end; i++) {
            printf("%02X ", RAM[addr + i]);
        }
        printf(" ");
        for (int i = 0; i < 16 && addr + i <= end; i++) {
            uint8_t c = RAM[addr + i];
            printf("%c", (c >= 32 && c < 127) ? c : '.');
        }
        printf("\n");
    }
}

// Breakpoint management
int add_breakpoint(uint16_t addr) {
    if (num_breakpoints >= MAX_BREAKPOINTS) {
        printf("Error: Maximum breakpoints (%d) reached\n", MAX_BREAKPOINTS);
        return -1;
    }
    
    // Check if already exists
    for (int i = 0; i < num_breakpoints; i++) {
        if (breakpoints[i] == addr) {
            printf("Breakpoint already set at $%04X\n", addr);
            return -1;
        }
    }
    
    breakpoints[num_breakpoints++] = addr;
    printf("Breakpoint %d set at $%04X\n", num_breakpoints, addr);
    return 0;
}

void clear_breakpoint(uint16_t addr) {
    for (int i = 0; i < num_breakpoints; i++) {
        if (breakpoints[i] == addr) {
            // Shift remaining breakpoints down
            for (int j = i; j < num_breakpoints - 1; j++) {
                breakpoints[j] = breakpoints[j + 1];
            }
            num_breakpoints--;
            printf("Breakpoint cleared at $%04X\n", addr);
            return;
        }
    }
    printf("No breakpoint at $%04X\n", addr);
}

void list_breakpoints(void) {
    if (num_breakpoints == 0) {
        printf("No breakpoints set\n");
        return;
    }
    printf("Breakpoints:\n");
    for (int i = 0; i < num_breakpoints; i++) {
        printf("  %d: $%04X\n", i + 1, breakpoints[i]);
    }
}

int check_breakpoint(uint16_t addr) {
    for (int i = 0; i < num_breakpoints; i++) {
        if (breakpoints[i] == addr) {
            return 1;
        }
    }
    return 0;
}

// Parse hex number
int parse_hex(const char *str, uint32_t *value) {
    char *endptr;
    *value = strtoul(str, &endptr, 16);
    return (*endptr == '\0');
}

// Monitor command processor
void process_monitor_command(char *cmd) {
    // Trim whitespace
    while (isspace(*cmd)) cmd++;
    if (*cmd == '\0') return;
    
    char *arg1 = NULL;
    char *arg2 = NULL;
    
    // Split into tokens
    char *token = strtok(cmd, " \t\n");
    if (!token) return;
    
    arg1 = strtok(NULL, " \t\n");
    arg2 = strtok(NULL, " \t\n");
    
    // Process commands
    if (strcmp(token, "s") == 0 || strcmp(token, "step") == 0) {
        // Step one instruction
        if (RAM[PC] == 0x00) {
            printf("Already at BRK instruction\n");
            return;
        }
        
        char disasm[128];
        disassemble_instruction(PC, disasm, sizeof(disasm));
        printf("%s\n", disasm);
        
        int instr_cycles = step6502();
        cycles += instr_cycles;
        
        display_registers();
        
    } else if (strcmp(token, "c") == 0 || strcmp(token, "cont") == 0 || 
               strcmp(token, "continue") == 0) {
        // Continue execution until breakpoint or BRK
        monitor_mode = 0;
        printf("Continuing execution..\n");
        
    } else if (strcmp(token, "r") == 0 || strcmp(token, "run") == 0) {
        // Run from current PC
        monitor_mode = 0;
        printf("Running..\n");
        
    } else if (strcmp(token, "b") == 0 || strcmp(token, "break") == 0) {
        // Set breakpoint
        if (!arg1) {
            list_breakpoints();
        } else {
            uint32_t addr;
            if (parse_hex(arg1, &addr) && addr < RAM_SIZE) {
                add_breakpoint((uint16_t)addr);
            } else {
                printf("Invalid address: %s\n", arg1);
            }
        }
        
    } else if (strcmp(token, "bc") == 0 || strcmp(token, "clear") == 0) {
        // Clear breakpoint
        if (!arg1) {
            printf("Usage: bc <address>\n");
        } else {
            uint32_t addr;
            if (parse_hex(arg1, &addr) && addr < RAM_SIZE) {
                clear_breakpoint((uint16_t)addr);
            } else {
                printf("Invalid address: %s\n", arg1);
            }
        }
        
    } else if (strcmp(token, "d") == 0 || strcmp(token, "disasm") == 0) {
        // Disassemble
        uint16_t start = PC;
        int count = 10;
        
        if (arg1) {
            uint32_t addr;
            if (parse_hex(arg1, &addr) && addr < RAM_SIZE) {
                start = (uint16_t)addr;
            }
        }
        if (arg2) {
            count = atoi(arg2);
            if (count <= 0) count = 10;
        }
        
        uint16_t addr = start;
        for (int i = 0; i < count; i++) {
            // Stop if we've wrapped around
            if (addr < start && i > 0) break;
            
            char disasm[128];
            int len = disassemble_instruction(addr, disasm, sizeof(disasm));
            
            // Mark PC and breakpoints
            char marker = ' ';
            if (addr == PC) marker = '>';
            else if (check_breakpoint(addr)) marker = '*';
            
            printf("%c %s\n", marker, disasm);
            addr += len;
        }
        
    } else if (strcmp(token, "m") == 0 || strcmp(token, "mem") == 0) {
        // Memory dump
        uint16_t start = 0;
        uint16_t end = 0xFF;
        
        if (arg1) {
            uint32_t addr;
            if (parse_hex(arg1, &addr) && addr < RAM_SIZE) {
                start = (uint16_t)addr;
                end = start + 0xFF;
            }
        }
        if (arg2) {
            uint32_t addr;
            if (parse_hex(arg2, &addr)) {
                if (addr >= 0x10000) {
                    end = 0xFFFF;
                } else {
                    end = (uint16_t)addr;
                }
            }
        }
        
        dump_memory(start, end);
        
    } else if (strcmp(token, "w") == 0 || strcmp(token, "write") == 0) {
        // Write to memory
        if (!arg1 || !arg2) {
            printf("Usage: w <address> <value>\n");
        } else {
            uint32_t addr, value;
            if (parse_hex(arg1, &addr) && parse_hex(arg2, &value) && 
                addr < RAM_SIZE && value <= 0xFF) {
                RAM[addr] = (uint8_t)value;
                printf("$%04X = $%02X\n", (uint16_t)addr, (uint8_t)value);
            } else {
                printf("Invalid address or value\n");
            }
        }
        
    } else if (strcmp(token, "reg") == 0 || strcmp(token, "regs") == 0) {
        // Display registers
        display_registers();
        
    } else if (strcmp(token, "t") == 0 || strcmp(token, "trace") == 0) {
        // Toggle trace mode
        trace_mode = !trace_mode;
        printf("Trace mode %s\n", trace_mode ? "ON" : "OFF");
        
    } else if (strcmp(token, "reset") == 0) {
        // Reset CPU
        reset6502();
        PC = CODE_START;
        cycles = 0;
        printf("CPU reset\n");
        display_registers();
        
    } else if (strcmp(token, "q") == 0 || strcmp(token, "quit") == 0) {
        // Quit
        running = 0;
        printf("Exiting..\n");
        
    } else if (strcmp(token, "h") == 0 || strcmp(token, "help") == 0 || 
               strcmp(token, "?") == 0) {
        // Help
        printf("\nMonitor Commands:\n");
        printf("  s, step           - Execute one instruction\n");
        printf("  c, continue       - Continue execution until breakpoint\n");
        printf("  b [addr]          - Set breakpoint (or list if no addr)\n");
        printf("  bc <addr>         - Clear breakpoint\n");
        printf("  d [addr] [count]  - Disassemble (default: PC, 10 lines)\n");
        printf("  m [start] [end]   - Dump memory\n");
        printf("  w <addr> <value>  - Write to memory\n");
        printf("  reg               - Display registers\n");
        printf("  t                 - Toggle trace mode\n");
        printf("  reset             - Reset CPU\n");
        printf("  q, quit           - Exit emulator\n");
        printf("  h, help, ?        - Show this help\n");
        printf("\nNotes:\n");
        printf("  - All addresses and values are in hexadecimal\n");
        printf("  - '>' marks current PC, '*' marks breakpoints\n");
        printf("  - BRK ($00) stops execution automatically\n\n");
        
    } else {
        printf("Unknown command: %s (type 'h' for help)\n", token);
    }
}

// Interactive monitor loop
void run_monitor(void) {
    char input[256];
    
    printf("\n* 6502 Monitor *\n");
    printf("Type 'h' for help\n\n");
    
    display_registers();
    
    // Disassemble current instruction
    char disasm[128];
    disassemble_instruction(PC, disasm, sizeof(disasm));
    printf("> %s\n\n", disasm);
    
    while (running) {
        printf("$> ");
        fflush(stdout);
        
        if (!fgets(input, sizeof(input), stdin)) {
            break;
        }
        
        process_monitor_command(input);
        
        // If we exited monitor mode, break to continue execution
        if (!monitor_mode) {
            break;
        }
    }
}

// Main emulator loop
void run_emulator(int max_cycles, int initial_trace) {
    cycles = 0;
    trace_mode = initial_trace;
    
    printf("\nStarting 6502 emulation\n");
    display_registers();
    printf("\n");
    
    while (running && (max_cycles <= 0 || cycles < max_cycles)) {
        // Check for monitor mode
        if (monitor_mode) {
            run_monitor();
            if (!running) break;
            continue;
        }
        
        // Check for breakpoint
        if (check_breakpoint(PC)) {
            printf("\nBreakpoint hit at $%04X\n", PC);
            monitor_mode = 1;
            continue;
        }
        
        // Check for BRK instruction
        if (RAM[PC] == 0x00) {
            printf("\nProgram ended (BRK at $%04X)\n", PC);
            monitor_mode = 1;
            continue;
        }
        
        // Trace if enabled
        if (trace_mode) {
            char disasm[128];
            disassemble_instruction(PC, disasm, sizeof(disasm));
            printf("%s  ", disasm);
            display_registers();
        }
        
        // Execute instruction
        int instruction_cycles = step6502();
        cycles += instruction_cycles;
        
        // Safety check
        if (cycles > 100000000) {
            fprintf(stderr, "\nError: Exceeded maximum cycles (possible infinite loop)\n");
            monitor_mode = 1;
        }
    }
    
    if (running) {
        printf("\nEmulation complete\n");
        printf("Total cycles: %d\n", cycles);
        display_registers();
    }
}

void print_usage(const char *program) {
    printf("Usage: %s [options] <binary_file>\n", program);
    printf("Options:\n");
    printf("  -m          Start in monitor mode (default)\n");
    printf("  -r          Run immediately (no monitor)\n");
    printf("  -t          Trace execution (show each instruction)\n");
    printf("  -c <cycles> Maximum cycles to execute\n");
    printf("  -h          Show this help\n");
    printf("\nExample:\n");
    printf("  %s program.bin       # Start in monitor\n", program);
    printf("  %s -r program.bin    # Run immediately\n", program);
    printf("  %s -t program.bin    # Run with trace\n", program);
}

int main(int argc, char *argv[]) {
    char *filename = NULL;
    int initial_trace = 0;
    int max_cycles = 0;
    
    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-m") == 0) {
            monitor_mode = 1;
        } else if (strcmp(argv[i], "-r") == 0) {
            monitor_mode = 0;
        } else if (strcmp(argv[i], "-t") == 0) {
            initial_trace = 1;
        } else if (strcmp(argv[i], "-c") == 0 && i + 1 < argc) {
            max_cycles = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (argv[i][0] != '-') {
            filename = argv[i];
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }
    
    if (!filename) {
        fprintf(stderr, "Error: No input file specified\n\n");
        print_usage(argv[0]);
        return 1;
    }
    
    // Init memory
    memset(RAM, 0, RAM_SIZE);
    
    // Load program
    if (load_binary(filename, CODE_START) < 0) {
        return 1;
    }
    
    // Init CPU
    reset6502();
    PC = CODE_START;
    
    printf("CPU initialised\n");
    
    // Run emulator
    run_emulator(max_cycles, initial_trace);
    
    printf("\nDone.\n");
    return 0;
}
