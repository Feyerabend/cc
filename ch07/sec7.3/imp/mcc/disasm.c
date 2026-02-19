/* Simple 6502 disassembler */
#include <stdio.h>
#include <stdint.h>

char *opcodes[256] = {
    "BRK","ORA","","","","ORA","ASL","","PHP","ORA","ASL","","","ORA","ASL","",
    "BPL","ORA","","","","ORA","ASL","","CLC","ORA","","","","ORA","ASL","",
    "JSR","AND","","","BIT","AND","ROL","","PLP","AND","ROL","","BIT","AND","ROL","",
    "BMI","AND","","","","AND","ROL","","SEC","AND","","","","AND","ROL","",
    "RTI","EOR","","","","EOR","LSR","","PHA","EOR","LSR","","JMP","EOR","LSR","",
    "BVC","EOR","","","","EOR","LSR","","CLI","EOR","","","","EOR","LSR","",
    "RTS","ADC","","","","ADC","ROR","","PLA","ADC","ROR","","JMP","ADC","ROR","",
    "BVS","ADC","","","","ADC","ROR","","SEI","ADC","","","","ADC","ROR","",
    "","STA","","","STY","STA","STX","","DEY","","TXA","","STY","STA","STX","",
    "BCC","STA","","","STY","STA","STX","","TYA","STA","TXS","","","STA","","",
    "LDY","LDA","LDX","","LDY","LDA","LDX","","TAY","LDA","TAX","","LDY","LDA","LDX","",
    "BCS","LDA","","","LDY","LDA","LDX","","CLV","LDA","TSX","","LDY","LDA","LDX","",
    "CPY","CMP","","","CPY","CMP","DEC","","INY","CMP","DEX","","CPY","CMP","DEC","",
    "BNE","CMP","","","","CMP","DEC","","CLD","CMP","","","","CMP","DEC","",
    "CPX","SBC","","","CPX","SBC","INC","","INX","SBC","NOP","","CPX","SBC","INC","",
    "BEQ","SBC","","","","SBC","INC","","SED","SBC","","","","SBC","INC",""
};

int modes[256] = {
    1,7,0,0,0,3,3,0,1,2,1,0,0,4,4,0, // 0
    6,8,0,0,0,5,5,0,1,9,0,0,0,9,9,0, // 1
    4,7,0,0,3,3,3,0,1,2,1,0,4,4,4,0, // 2
    6,8,0,0,0,5,5,0,1,9,0,0,0,9,9,0, // 3
    1,7,0,0,0,3,3,0,1,2,1,0,4,4,4,0, // 4
    6,8,0,0,0,5,5,0,1,9,0,0,0,9,9,0, // 5
    1,7,0,0,0,3,3,0,1,2,1,0,10,4,4,0, // 6
    6,8,0,0,0,5,5,0,1,9,0,0,0,9,9,0, // 7
    0,7,0,0,3,3,3,0,1,0,1,0,4,4,4,0, // 8
    6,8,0,0,5,5,5,0,1,9,1,0,0,9,0,0, // 9
    2,7,2,0,3,3,3,0,1,2,1,0,4,4,4,0, // A
    6,8,0,0,5,5,5,0,1,9,1,0,9,9,9,0, // B
    2,7,0,0,3,3,3,0,1,2,1,0,4,4,4,0, // C
    6,8,0,0,0,5,5,0,1,9,0,0,0,9,9,0, // D
    2,7,0,0,3,3,3,0,1,2,1,0,4,4,4,0, // E
    6,8,0,0,0,5,5,0,1,9,0,0,0,9,9,0  // F
};

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: disasm <file>\n");
        return 1;
    }
    
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 1;
    
    uint8_t mem[65536];
    int len = fread(mem, 1, 65536, f);
    fclose(f);
    
    int pc = 0;
    while (pc < len) {
        uint8_t op = mem[pc];
        printf("%04X: %02X ", 0x0600 + pc, op);
        
        int mode = modes[op];
        char *name = opcodes[op];
        
        if (mode == 0 || name[0] == 0) {
            printf("???\n");
            pc++;
            continue;
        }
        
        if (mode == 1) { // Implied
            printf("      %s\n", name);
            pc++;
        } else if (mode == 2) { // Immediate
            printf("%02X    %s #$%02X\n", mem[pc+1], name, mem[pc+1]);
            pc += 2;
        } else if (mode == 3) { // Zero page
            printf("%02X    %s $%02X\n", mem[pc+1], name, mem[pc+1]);
            pc += 2;
        } else if (mode == 4) { // Absolute
            uint16_t addr = mem[pc+1] | (mem[pc+2] << 8);
            printf("%02X %02X %s $%04X\n", mem[pc+1], mem[pc+2], name, addr);
            pc += 3;
        } else if (mode == 5) { // Zero page,X
            printf("%02X    %s $%02X,X\n", mem[pc+1], name, mem[pc+1]);
            pc += 2;
        } else if (mode == 6) { // Relative
            int8_t offset = (int8_t)mem[pc+1];
            printf("%02X    %s $%04X\n", mem[pc+1], name, 0x0600 + pc + 2 + offset);
            pc += 2;
        } else if (mode == 9) { // Absolute,Y
            uint16_t addr = mem[pc+1] | (mem[pc+2] << 8);
            printf("%02X %02X %s $%04X,Y\n", mem[pc+1], mem[pc+2], name, addr);
            pc += 3;
        } else {
            printf("      %s\n", name);
            pc++;
        }
    }
    
    return 0;
}
