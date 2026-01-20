#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "symbol_table.h"
#include "ast.h"


// init global variables and procedures
Variable *global_vars = NULL;
Procedure *procedures = NULL;

void addGlobal(int id, const char *name, int type_id) {
    Variable *new_var = malloc(sizeof(Variable));
    new_var->id = id;
    strncpy(new_var->name, name, sizeof(new_var->name) - 1);
    new_var->type_id = type_id;
    new_var->next = global_vars;
    global_vars = new_var;
}

void addProcedure(int id, const char *name) {
    Procedure *new_proc = malloc(sizeof(Procedure));
    new_proc->id = id;
    strncpy(new_proc->name, name, sizeof(new_proc->name) - 1);
    new_proc->local_vars = NULL;
    new_proc->next = procedures;
    procedures = new_proc;
}

// given a procedure ID, add a local variable to that procedure
void addLocalToProcedure(int proc_id, int var_id, const char *name, int type_id) {
    Procedure *proc = procedures;
    while (proc && proc->id != proc_id) {
        proc = proc->next;
    }
    if (proc) {
        Variable *new_var = malloc(sizeof(Variable));
        new_var->id = var_id;
        strncpy(new_var->name, name, sizeof(new_var->name) - 1);
        new_var->type_id = type_id;
        new_var->next = proc->local_vars;
        proc->local_vars = new_var;
    }
}


Variable *findVariable(const char *proc_name, const char *var_name) {
    // search for procedure by name
    Procedure *proc = procedures;
    while (proc) {
        if (strcmp(proc->name, proc_name) == 0) {
            // procedure found, search local variables
            Variable *local_var = proc->local_vars;
            while (local_var) {
                if (strcmp(local_var->name, var_name) == 0) {
                    return local_var; // return local variable, if found
                }
                local_var = local_var->next;
            }
            break; // procedure found but variable not, stop
        }
        proc = proc->next;
    }

    // if not found in procedure's local scope, search global space
    Variable *vars = global_vars;
    while (vars) {
        if (strcmp(vars->name, var_name) == 0) {
            return vars; // return global variable if found
        }
        vars = vars->next;
    }

    // variable not found
    return NULL;
}


void saveSymbolTable(const char *filename) {
    FILE *file = fopen(filename, "w");
    if (!file) {
        perror("Failed to open file");
        exit(EXIT_FAILURE);
    }

    // global variables
    Variable *var = global_vars;
    while (var) {
        fprintf(file, "GLOBAL_VARIABLE ID: %d Name: %s Type: %d\n", var->id, var->name, var->type_id);
        var = var->next;
    }

    // procedures and their local variables
    Procedure *proc = procedures;
    while (proc) {
        fprintf(file, "PROCEDURE ID: %d Name: %s\n", proc->id, proc->name);
        Variable *local_var = proc->local_vars;
        while (local_var) {
            fprintf(file, "  LOCAL_VARIABLE ID: %d Name: %s Type: %d\n", local_var->id, local_var->name, local_var->type_id);
            local_var = local_var->next;
        }
        proc = proc->next;
    }

    fclose(file);
}


void parseSymbolTable(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Failed to open file");
        exit(EXIT_FAILURE);
    }

    char line[256];
    while (fgets(line, sizeof(line), file)) {
        if (strncmp(line, "GLOBAL_VARIABLE", 15) == 0) {
            int id, type_id;
            char name[16];
            sscanf(line, "GLOBAL_VARIABLE ID: %d Name: %s Type: %d", &id, name, &type_id);
            addGlobal(id, name, type_id);
        } else if (strncmp(line, "PROCEDURE", 9) == 0) {
            int id;
            char name[16];
            sscanf(line, "PROCEDURE ID: %d Name: %s", &id, name);
            addProcedure(id, name);
        } else if (strncmp(line, "  LOCAL_VARIABLE", 16) == 0) {
            int id, type_id;
            char name[16];
            sscanf(line, "  LOCAL_VARIABLE ID: %d Name: %s Type: %d", &id, name, &type_id);
            addLocalToProcedure(procedures->id, id, name, type_id);
        }
    }

    fclose(file);
}


void printSymbolTable() {
    printf("Global Variables:\n");
    Variable *var = global_vars;
    while (var) {
        printf("  ID: %d, Name: %s, Type: %d\n", var->id, var->name, var->type_id);
        var = var->next;
    }

    printf("Procedures:\n");
    Procedure *proc = procedures;
    while (proc) {
        printf("  ID: %d, Name: %s\n", proc->id, proc->name);
        Variable *local_var = proc->local_vars;
        while (local_var) {
            printf("    Local Variable - ID: %d, Name: %s, Type: %d\n", local_var->id, local_var->name, local_var->type_id);
            local_var = local_var->next;
        }
        proc = proc->next;
    }
}

void freeGlobalVars() {
    Variable *var = global_vars;
    while (var) {
        Variable *next = var->next;
        free(var);
        var = next;
    }
    global_vars = NULL;
}

void freeLocalVars(Variable *local_vars) {
    Variable *var = local_vars;
    while (var) {
        Variable *next = var->next;
        free(var);
        var = next;
    }
}

void freeProcedures() {
    Procedure *proc = procedures;
    while (proc) {
        Procedure *next = proc->next;
        freeLocalVars(proc->local_vars);
        free(proc);
        proc = next;
    }
    procedures = NULL;
}

void freeSymbolTable() {
    freeGlobalVars();
    freeProcedures();
}


int generateSymbolId() {
    static int current_id = 0;
    return ++current_id;
}

void buildSymbolTableFromAST(ASTNode *node, int currentProcedureID) {
    if (!node) return;

    switch (node->type) {
        case NODE_CONST_DECL:
        case NODE_VAR_DECL: {
            // add variable (or constant) to symbol table
            int id = generateSymbolId();
            int type_id = (node->type == NODE_CONST_DECL) ? 2 : 1; // 2 for constant, 1 for variable
            if (currentProcedureID == -1) {
                addGlobal(id, node->value, type_id);
            } else {
                addLocalToProcedure(currentProcedureID, id, node->value, type_id);
            }
            break;
        }
        case NODE_PROC_DECL: {
            // add procedure to symbol table
            int id = generateSymbolId();
            addProcedure(id, node->value);
            currentProcedureID = id; // update current procedure ID for scope
            break;
        }
        default:
            // ignore other nodes for symbol table purposes
            break;
    }

    // traverse children recursively
    for (int i = 0; i < node->childCount; i++) {
        buildSymbolTableFromAST(node->children[i], currentProcedureID);
    }
}

// wrapper to build symbol table
void buildSymbolTable(ASTNode *root) {
    if (!root) return;

    // start with global scope (no procedure)
    buildSymbolTableFromAST(root, -1);
}
