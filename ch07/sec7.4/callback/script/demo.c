#include "eventscript.h"
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    printf("\n");
    printf("  EventScript Demo\n");
    printf("  Event-Driven Language with VM\n");
    printf("\n\n");
    
    // Example 1: Simple event emission and handling
    printf("> EXAMPLE 1: Basic Event Handling <\n");
    printf("Program:\n");
    printf("  on \"greet\" { print \"Hello from handler!\" }\n");
    printf("  emit \"greet\", 42\n\n");
    
    {
        ASTNode **stmts = malloc(2 * sizeof(ASTNode*));
        
        // on "greet" { print "Hello from handler!" }
        ASTNode **handler_stmts = malloc(1 * sizeof(ASTNode*));
        handler_stmts[0] = ast_print(ast_string("Hello from handler!"));
        ASTNode *handler_body = ast_block(handler_stmts, 1);
        stmts[0] = ast_on("greet", handler_body);
        
        // emit "greet", 42
        stmts[1] = ast_emit("greet", ast_number(42));
        
        ASTNode *program = ast_program(stmts, 2);
        
        // Compile
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        // Execute
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop(vm);
        
        // Cleanup
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\n");
    
    // Example 2: Multiple events and handlers
    printf("> EXAMPLE 2: Multiple Events <\n");
    printf("Program:\n");
    printf("  on \"start\" { print \"Starting..\" }\n");
    printf("  on \"finish\" { print \"Done!\" }\n");
    printf("  emit \"start\", 0\n");
    printf("  emit \"finish\", 100\n\n");
    
    {
        ASTNode **stmts = malloc(4 * sizeof(ASTNode*));
        
        // on "start" { print "Starting.." }
        ASTNode **h1_stmts = malloc(1 * sizeof(ASTNode*));
        h1_stmts[0] = ast_print(ast_string("Starting..."));
        stmts[0] = ast_on("start", ast_block(h1_stmts, 1));
        
        // on "finish" { print "Done!" }
        ASTNode **h2_stmts = malloc(1 * sizeof(ASTNode*));
        h2_stmts[0] = ast_print(ast_string("Done!"));
        stmts[1] = ast_on("finish", ast_block(h2_stmts, 1));
        
        // emit "start", 0
        stmts[2] = ast_emit("start", ast_number(0));
        
        // emit "finish", 100
        stmts[3] = ast_emit("finish", ast_number(100));
        
        ASTNode *program = ast_program(stmts, 4);
        
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop(vm);
        
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\n");
    
    // Example 3: Event chaining (handler emits new event)
    printf("> EXAMPLE 3: Event Chaining <\n");
    printf("Program:\n");
    printf("  on \"click\" { emit \"process\", 10 }\n");
    printf("  on \"process\" { print \"Processing data..\" }\n");
    printf("  emit \"click\", 1\n\n");
    
    {
        ASTNode **stmts = malloc(3 * sizeof(ASTNode*));
        
        // on "click" { emit "process", 10 }
        ASTNode **h1_stmts = malloc(1 * sizeof(ASTNode*));
        h1_stmts[0] = ast_emit("process", ast_number(10));
        stmts[0] = ast_on("click", ast_block(h1_stmts, 1));
        
        // on "process" { print "Processing data..." }
        ASTNode **h2_stmts = malloc(1 * sizeof(ASTNode*));
        h2_stmts[0] = ast_print(ast_string("Processing data.."));
        stmts[1] = ast_on("process", ast_block(h2_stmts, 1));
        
        // emit "click", 1
        stmts[2] = ast_emit("click", ast_number(1));
        
        ASTNode *program = ast_program(stmts, 3);
        
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop(vm);
        
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\n");
    
    // Example 4: Arithmetic in handlers
    printf("> EXAMPLE 4: Computation in Handlers <\n");
    printf("Program:\n");
    printf("  on \"calculate\" { print 5 + 3 }\n");
    printf("  emit \"calculate\", 0\n\n");
    
    {
        ASTNode **stmts = malloc(2 * sizeof(ASTNode*));
        
        // on "calculate" { print 5 + 3 }
        ASTNode **h_stmts = malloc(1 * sizeof(ASTNode*));
        ASTNode *add_expr = ast_binary(OP_ADD, ast_number(5), ast_number(3));
        h_stmts[0] = ast_print(add_expr);
        stmts[0] = ast_on("calculate", ast_block(h_stmts, 1));
        
        // emit "calculate", 0
        stmts[1] = ast_emit("calculate", ast_number(0));
        
        ASTNode *program = ast_program(stmts, 2);
        
        Bytecode *bc = bytecode_create();
        compile(program, bc);
        
        VM *vm = vm_create(bc);
        vm_run(vm);
        vm_event_loop(vm);
        
        vm_free(vm);
        bytecode_free(bc);
        ast_free(program);
    }
    
    printf("\n\nAll done.\n\n");
    
    return 0;
}
