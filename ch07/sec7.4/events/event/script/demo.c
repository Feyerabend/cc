#include "eventscript.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>

int main(void) {
    printf("\n");
    printf("  EventScript - TRUE Event Loop Demo\n");
    printf("  With Timers & Continuous Operation\n");
    printf("\n\n");
    
    // Example 1: Basic timer
    printf("> EXAMPLE 1: Simple Timer <\n");
    printf("Program:\n");
    printf("  on \"timeout\" { print \"Timer fired!\" }\n");
    printf("  after 1000ms emit \"timeout\", 42\n\n");
    
    {
        ASTNode **stmts = malloc(2 * sizeof(ASTNode*));
        
        // on "timeout" { print "Timer fired!" }
        ASTNode **h_stmts = malloc(1 * sizeof(ASTNode*));
        h_stmts[0] = ast_print(ast_string("Timer fired!"));
        stmts[0] = ast_on("timeout", ast_block(h_stmts, 1));
        
        // after 1000ms emit "timeout", 42
        stmts[1] = ast_timer(1000, "timeout", ast_number(42));
        
        ASTNode *program = ast_program(stmts, 2);
        
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop_forever(vm);  // TRUE EVENT LOOP - runs indefinitely until manually stopped
        
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\n");
    
    // Example 2: Multiple timers
    printf("> EXAMPLE 2: Multiple Timers <\n");
    printf("Program:\n");
    printf("  on \"tick\" { print \"Tick!\" }\n");
    printf("  on \"tock\" { print \"Tock!\" }\n");
    printf("  after 500ms emit \"tick\", 1\n");
    printf("  after 1000ms emit \"tock\", 2\n");
    printf("  after 1500ms emit \"tick\", 3\n\n");
    
    {
        ASTNode **stmts = malloc(5 * sizeof(ASTNode*));
        
        // on "tick" { print "Tick!" }
        ASTNode **h1_stmts = malloc(1 * sizeof(ASTNode*));
        h1_stmts[0] = ast_print(ast_string("Tick!"));
        stmts[0] = ast_on("tick", ast_block(h1_stmts, 1));
        
        // on "tock" { print "Tock!" }
        ASTNode **h2_stmts = malloc(1 * sizeof(ASTNode*));
        h2_stmts[0] = ast_print(ast_string("Tock!"));
        stmts[1] = ast_on("tock", ast_block(h2_stmts, 1));
        
        // Timers
        stmts[2] = ast_timer(500, "tick", ast_number(1));
        stmts[3] = ast_timer(1000, "tock", ast_number(2));
        stmts[4] = ast_timer(1500, "tick", ast_number(3));
        
        ASTNode *program = ast_program(stmts, 5);
        
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop_forever(vm);
        
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\n");
    
    // Example 3: Event chaining with timers
    printf("> EXAMPLE 3: Event Chaining with Timers <\n");
    printf("Program:\n");
    printf("  on \"start\" { after 500ms emit \"process\", 10 }\n");
    printf("  on \"process\" { print \"Processing..\" }\n");
    printf("  emit \"start\", 0\n\n");
    
    {
        ASTNode **stmts = malloc(3 * sizeof(ASTNode*));
        
        // on "start" { after 500ms emit "process", 10 }
        ASTNode **h1_stmts = malloc(1 * sizeof(ASTNode*));
        h1_stmts[0] = ast_timer(500, "process", ast_number(10));
        stmts[0] = ast_on("start", ast_block(h1_stmts, 1));
        
        // on "process" { print "Processing..." }
        ASTNode **h2_stmts = malloc(1 * sizeof(ASTNode*));
        h2_stmts[0] = ast_print(ast_string("Processing.."));
        stmts[1] = ast_on("process", ast_block(h2_stmts, 1));
        
        // emit "start", 0
        stmts[2] = ast_emit("start", ast_number(0));
        
        ASTNode *program = ast_program(stmts, 3);
        
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop_forever(vm);
        
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\n");
    
    // Example 4: Mix of immediate and delayed events
    printf("> EXAMPLE 4: Mixed Immediate & Timer Events <\n");
    printf("Program:\n");
    printf("  on \"start\" { print \"Starting system..\" }\n");
    printf("  on \"ready\" { print \"System ready!\" }\n");
    printf("  emit \"start\", 0\n");
    printf("  after 1000ms emit \"ready\", 1\n\n");
    
    {
        ASTNode **stmts = malloc(4 * sizeof(ASTNode*));
        
        // on "start" { print "Starting system.." }
        ASTNode **h1_stmts = malloc(1 * sizeof(ASTNode*));
        h1_stmts[0] = ast_print(ast_string("Starting system.."));
        stmts[0] = ast_on("start", ast_block(h1_stmts, 1));
        
        // on "ready" { print "System ready!" }
        ASTNode **h2_stmts = malloc(1 * sizeof(ASTNode*));
        h2_stmts[0] = ast_print(ast_string("System ready!"));
        stmts[1] = ast_on("ready", ast_block(h2_stmts, 1));
        
        // emit "start", 0 (immediate)
        stmts[2] = ast_emit("start", ast_number(0));
        
        // after 1000ms emit "ready", 1 (delayed)
        stmts[3] = ast_timer(1000, "ready", ast_number(1));
        
        ASTNode *program = ast_program(stmts, 4);
        
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop_forever(vm);
        
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\nAll done.\n\n");
    
    return 0;
}
