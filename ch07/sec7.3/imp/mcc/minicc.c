/* Mini C compiler for 6502 - simplified but functional
 * Can compile arithmetic, functions, if/while, and variables
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

char *src;
int pos = 0;
int tok_type;
char tok_str[256];
int tok_val;

uint8_t code[65536];
int code_pos = 0x0600;

typedef struct {
    char name[64];
    int addr;
} Func;

Func funcs[64];
int nfuncs = 0;

typedef struct {
    char name[64];
    int offset;
} Var;

Var locals[64];
int nlocals = 0;
int stack_offset = 0;

#define TK_EOF 0
#define TK_NUM 1
#define TK_ID 2
#define TK_INT 3
#define TK_RET 4
#define TK_IF 5
#define TK_ELSE 6
#define TK_WHILE 7

void error(char *msg) {
    printf("Error: %s\n", msg);
    exit(1);
}

void emit(uint8_t b) {
    code[code_pos++] = b;
}

void emit16(uint16_t w) {
    emit(w & 0xFF);
    emit((w >> 8) & 0xFF);
}

void patch16(int addr, uint16_t val) {
    code[addr] = val & 0xFF;
    code[addr+1] = (val >> 8) & 0xFF;
}

void next() {
    while (src[pos] == ' ' || src[pos] == '\t' || src[pos] == '\n' || src[pos] == '\r')
        pos++;
    
    if (src[pos] == 0) {
        tok_type = TK_EOF;
        return;
    }
    
    if (src[pos] >= '0' && src[pos] <= '9') {
        tok_type = TK_NUM;
        tok_val = 0;
        while (src[pos] >= '0' && src[pos] <= '9') {
            tok_val = tok_val * 10 + (src[pos] - '0');
            pos++;
        }
        return;
    }
    
    if ((src[pos] >= 'a' && src[pos] <= 'z') || (src[pos] >= 'A' && src[pos] <= 'Z') || src[pos] == '_') {
        int i = 0;
        while ((src[pos] >= 'a' && src[pos] <= 'z') || 
               (src[pos] >= 'A' && src[pos] <= 'Z') || 
               (src[pos] >= '0' && src[pos] <= '9') ||
               src[pos] == '_') {
            tok_str[i++] = src[pos++];
        }
        tok_str[i] = 0;
        
        if (strcmp(tok_str, "int") == 0) tok_type = TK_INT;
        else if (strcmp(tok_str, "return") == 0) tok_type = TK_RET;
        else if (strcmp(tok_str, "if") == 0) tok_type = TK_IF;
        else if (strcmp(tok_str, "else") == 0) tok_type = TK_ELSE;
        else if (strcmp(tok_str, "while") == 0) tok_type = TK_WHILE;
        else tok_type = TK_ID;
        return;
    }
    
    tok_type = src[pos++];
}

void expect(int c) {
    if (tok_type != c) error("Unexpected token");
    next();
}

void expr();

void primary() {
    if (tok_type == TK_NUM) {
        emit(0xA9); emit(tok_val);  // LDA #immediate
        emit(0x48);                  // PHA (push to stack)
        next();
        return;
    }
    
    if (tok_type == TK_ID) {
        char name[64];
        strcpy(name, tok_str);
        next();
        
        if (tok_type == '(') {
            next();
            int nargs = 0;
            while (tok_type != ')') {
                expr();
                nargs++;
                if (tok_type == ',') next();
            }
            expect(')');
            
            Func *f = NULL;
            for (int i = 0; i < nfuncs; i++) {
                if (strcmp(funcs[i].name, name) == 0) {
                    f = &funcs[i];
                    break;
                }
            }
            
            if (!f) error("Unknown function");
            
            // Set up parameters in zero page before call
            for (int i = nargs - 1; i >= 0; i--) {
                emit(0x68);              // PLA
                emit(0x85); emit(0x10 + i); // STA $10+i
            }
            
            emit(0x20);              // JSR
            emit16(f->addr);
            
            emit(0x48);              // PHA (push return value)
            return;
        }
        
        Var *v = NULL;
        for (int i = 0; i < nlocals; i++) {
            if (strcmp(locals[i].name, name) == 0) {
                v = &locals[i];
                break;
            }
        }
        if (!v) error("Unknown variable");
        
        emit(0xA5); emit(v->offset);  // LDA zero_page
        emit(0x48);                    // PHA
        return;
    }
    
    if (tok_type == '(') {
        next();
        expr();
        expect(')');
        return;
    }
    
    error("Expected expression");
}

void mul() {
    primary();
    while (tok_type == '*' || tok_type == '/') {
        int op = tok_type;
        next();
        primary();
        
        // Pop both operands
        emit(0x68);              // PLA (second operand)
        emit(0x85); emit(0xF0);  // STA $F0
        emit(0x68);              // PLA (first operand)
        emit(0x85); emit(0xF1);  // STA $F1
        
        if (op == '*') {
            // Multiply: result in A
            emit(0xA9); emit(0);     // LDA #0
            emit(0x85); emit(0xF2);  // STA $F2 (result)
            emit(0xA2); emit(8);     // LDX #8 (counter)
            int loop = code_pos;
            emit(0x46); emit(0xF1);  // LSR $F1
            emit(0x90); emit(3);     // BCC +3
            emit(0x18);              // CLC
            emit(0x65); emit(0xF0);  // ADC $F0
            emit(0x85); emit(0xF2);  // STA $F2
            emit(0x06); emit(0xF0);  // ASL $F0
            emit(0xCA);              // DEX
            emit(0xD0);              // BNE loop
            emit(loop - code_pos - 1);
            emit(0xA5); emit(0xF2);  // LDA $F2
        }
        emit(0x48);              // PHA (push result)
    }
}

void add() {
    mul();
    while (tok_type == '+' || tok_type == '-') {
        int op = tok_type;
        next();
        mul();
        
        // Pop both operands
        emit(0x68);              // PLA (second)
        emit(0x85); emit(0xF0);  // STA $F0
        emit(0x68);              // PLA (first)
        
        if (op == '+') {
            emit(0x18);          // CLC
            emit(0x65); emit(0xF0); // ADC $F0
        } else {
            emit(0x38);          // SEC
            emit(0xE5); emit(0xF0); // SBC $F0
        }
        
        emit(0x48);              // PHA (push result)
    }
}

void rel() {
    add();
    if (tok_type == '<' || tok_type == '>' || tok_type == '=' || tok_type == '!') {
        int op = tok_type;
        next();
        if (op == '=' || op == '!') expect('=');
        
        add();
        
        // Pop both operands
        emit(0x68);              // PLA (second)
        emit(0x85); emit(0xF0);  // STA $F0
        emit(0x68);              // PLA (first)
        emit(0x38);              // SEC
        emit(0xE5); emit(0xF0);  // SBC $F0
        
        if (op == '=') {
            emit(0xF0); emit(4);     // BEQ +4
            emit(0xA9); emit(0);     // LDA #0
            emit(0xF0); emit(2);     // BRA +2
            emit(0xA9); emit(1);     // LDA #1
        } else if (op == '!') {
            emit(0xD0); emit(4);     // BNE +4
            emit(0xA9); emit(0);     // LDA #0
            emit(0xF0); emit(2);     // BRA +2
            emit(0xA9); emit(1);     // LDA #1
        } else if (op == '<') {
            emit(0x30); emit(4);     // BMI +4
            emit(0xA9); emit(0);     // LDA #0
            emit(0xF0); emit(2);     // BRA +2
            emit(0xA9); emit(1);     // LDA #1
        }
        
        emit(0x48);              // PHA (push result)
    }
}

void expr() {
    if (tok_type == TK_ID) {
        char name[64];
        strcpy(name, tok_str);
        int save_pos = pos;
        int save_tok = tok_type;
        
        next();
        if (tok_type == '=') {
            next();
            rel();
            
            Var *v = NULL;
            for (int i = 0; i < nlocals; i++) {
                if (strcmp(locals[i].name, name) == 0) {
                    v = &locals[i];
                    break;
                }
            }
            if (!v) error("Unknown variable");
            
            emit(0x68);              // PLA
            emit(0x85); emit(v->offset); // STA zero_page
            emit(0x48);              // PHA (leave on stack)
            return;
        }
        
        pos = save_pos;
        tok_type = save_tok;
        strcpy(tok_str, name);
    }
    
    rel();
}

void stmt();

void block() {
    expect('{');
    while (tok_type != '}')
        stmt();
    expect('}');
}

void stmt() {
    if (tok_type == TK_INT) {
        next();
        expect(TK_ID);
        strcpy(locals[nlocals].name, tok_str);
        locals[nlocals].offset = 0x10 + stack_offset++;
        nlocals++;
        expect(';');
        return;
    }
    
    if (tok_type == TK_RET) {
        next();
        if (tok_type != ';') {
            expr();
            emit(0x68);          // PLA (pop return value into A)
        }
        expect(';');
        emit(0x60);              // RTS
        return;
    }
    
    if (tok_type == TK_IF) {
        next();
        expect('(');
        expr();
        expect(')');
        
        emit(0x68);              // PLA (get condition)
        emit(0xC9); emit(0);     // CMP #0
        emit(0xF0); 
        int jz = code_pos++;
        
        stmt();
        
        if (tok_type == TK_ELSE) {
            emit(0x4C);
            int jmp = code_pos;
            code_pos += 2;
            
            code[jz] = code_pos - jz - 1;
            
            next();
            stmt();
            
            patch16(jmp, code_pos);
        } else {
            code[jz] = code_pos - jz - 1;
        }
        return;
    }
    
    if (tok_type == TK_WHILE) {
        next();
        expect('(');
        
        int loop_start = code_pos;
        expr();
        expect(')');
        
        emit(0x68);              // PLA (get condition)
        emit(0xC9); emit(0);     // CMP #0
        emit(0xF0);
        int jz = code_pos++;
        
        stmt();
        
        emit(0x4C);
        emit16(loop_start);
        
        code[jz] = code_pos - jz - 1;
        return;
    }
    
    if (tok_type == '{') {
        block();
        return;
    }
    
    expr();
    emit(0x68);              // PLA (pop unused expression result)
    expect(';');
}

void function() {
    expect(TK_INT);
    expect(TK_ID);
    
    strcpy(funcs[nfuncs].name, tok_str);
    funcs[nfuncs].addr = code_pos;
    nfuncs++;
    
    nlocals = 0;
    stack_offset = 0;
    
    expect('(');
    while (tok_type != ')') {
        expect(TK_INT);
        expect(TK_ID);
        strcpy(locals[nlocals].name, tok_str);
        locals[nlocals].offset = 0x10 + stack_offset++;
        nlocals++;
        if (tok_type == ',') next();
    }
    expect(')');
    
    block();
}

void compile() {
    // Reserve space for runtime initialization
    code_pos = 0x0610;
    
    next();
    while (tok_type != TK_EOF) {
        function();
    }
    
    // Now generate runtime initialization at $0600
    int saved_pos = code_pos;
    code_pos = 0x0600;
    
    // Initialize stack pointer
    emit(0xA2); emit(0xFF);      // LDX #$FF
    emit(0x9A);                  // TXS
    
    // Find and call main
    Func *main_func = NULL;
    for (int i = 0; i < nfuncs; i++) {
        if (strcmp(funcs[i].name, "main") == 0) {
            main_func = &funcs[i];
            break;
        }
    }
    
    if (main_func) {
        emit(0x20);              // JSR main
        emit16(main_func->addr);
    }
    
    // Exit loop (accumulator has return value)
    emit(0x4C);                  // JMP (infinite loop)
    emit16(code_pos);
    
    code_pos = saved_pos;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: minicc <file.c>\n");
        return 1;
    }
    
    FILE *f = fopen(argv[1], "r");
    if (!f) {
        printf("Cannot open file\n");
        return 1;
    }
    
    fseek(f, 0, SEEK_END);
    int len = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    src = malloc(len + 1);
    fread(src, 1, len, f);
    src[len] = 0;
    fclose(f);
    
    memset(code, 0, sizeof(code));
    
    compile();
    
    FILE *out = fopen("out.bin", "wb");
    fwrite(&code[0x0600], 1, code_pos - 0x0600, out);
    fclose(out);
    
    printf("Compiled %d functions, %d bytes\n", nfuncs, code_pos - 0x0600);
    
    return 0;
}
