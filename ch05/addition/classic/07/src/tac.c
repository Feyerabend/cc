#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ast.h"
#include "symbol_table.h"
#include "tac.h"


// global list of TAC instructions
TAC *tac_head = NULL;
TAC *tac_tail = NULL;

// counter for generating temporary variables
int temp_counter = 0;
int label_counter = 0;


// -- Memory management --

// struct allocated temporary strings
typedef struct TempStorage {
    char *str;
    struct TempStorage *next;
} TempStorage;

// head of the list
TempStorage *temp_storage_head = NULL;

// track allocated strings
void registerTemp(char *str) {
    TempStorage *node = malloc(sizeof(TempStorage));
    if (!node) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    node->str = str;
    node->next = temp_storage_head;
    temp_storage_head = node;
}

// a new temporary variable
char *newTemp() {
    char *temp = malloc(16);
    if (!temp) {
        fprintf(stderr, "[ERROR] Memory allocation failed in newTemp()\n");
        exit(EXIT_FAILURE);
    }

    snprintf(temp, 16, "t%d", temp_counter++);
    printf("[DEBUG] Allocated new temp: %s\n", temp);
    
    registerTemp(temp);
    
    return temp;
}

// a new label
char *newLabel() {
    char *label = malloc(16);
    if (!label) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    snprintf(label, 16, "L%d", label_counter++);
    registerTemp(label);
    return label;
}

// free all registered temporary variables
void freeAllTemps() {
    printf("FREE ALL TEMPS\n");
    TempStorage *current = temp_storage_head;
    while (current) {
        TempStorage *next = current->next;
        free(current->str);  // allocated string
        free(current);       // node itself
        current = next;
    }
    temp_storage_head = NULL;
    printf("FREED ALL TEMPS\n");
}

// --- TAC memory ---
void freeTAC() {
    freeAllTemps();
    printf("[DEBUG] Freeing TAC instructions\n");
    TAC *current = tac_head;
    while (current) {
        TAC *next = current->next;
        free(current->op);
        if (current->arg1) free(current->arg1);
        if (current->arg2) free(current->arg2);
        if (current->result) free(current->result);
        free(current);
        current = next;
    }
    tac_head = tac_tail = NULL;
    temp_counter = 0;  // Reset temp counter
    label_counter = 0; // Reset label counter
    printf("[DEBUG] Freed TAC instructions\n");
}

// --- TAC generation ---

void emitTAC(const char *op, const char *arg1, const char *arg2, const char *result) {
    // Debug: Verify all inputs before using strdup
    printf("[DEBUG] emitTAC: op=%s, arg1=%s, arg2=%s, result=%s\n",
           op, arg1 ? arg1 : "NULL", arg2 ? arg2 : "NULL", result ? result : "NULL");

    TAC *new_tac = malloc(sizeof(TAC));
    if (!new_tac) {
        fprintf(stderr, "[ERROR] Memory allocation failed for TAC instruction\n");
        exit(EXIT_FAILURE);
    }

    new_tac->op = strdup(op);
    if (!new_tac->op) {
        fprintf(stderr, "[ERROR] Memory allocation failed for TAC op\n");
        exit(EXIT_FAILURE);
    }

    new_tac->arg1 = arg1 ? strdup(arg1) : NULL;
    if (arg1 && !new_tac->arg1) {
        fprintf(stderr, "[ERROR] Memory allocation failed for TAC arg1\n");
        exit(EXIT_FAILURE);
    }

    new_tac->arg2 = arg2 ? strdup(arg2) : NULL;
    if (arg2 && !new_tac->arg2) {
        fprintf(stderr, "[ERROR] Memory allocation failed for TAC arg2\n");
        exit(EXIT_FAILURE);
    }

    new_tac->result = result ? strdup(result) : NULL;
    if (result && !new_tac->result) {
        fprintf(stderr, "[ERROR] Memory allocation failed for TAC result\n");
        exit(EXIT_FAILURE);
    }

    new_tac->next = NULL;

    if (!tac_head) {
        tac_head = tac_tail = new_tac;
    } else {
        tac_tail->next = new_tac;
        tac_tail = new_tac;
    }

    // Debug: Confirm instruction added
    printf("[DEBUG] TAC added: %s %s %s %s\n",
           new_tac->op,
           new_tac->arg1 ? new_tac->arg1 : "NULL",
           new_tac->arg2 ? new_tac->arg2 : "NULL",
           new_tac->result ? new_tac->result : "NULL");
}


char *generateTAC(ASTNode *node, const char *proc_name) {

    if (!node) {
        printf("[DEBUG] NULL node encountered in generateTAC\n");
        return NULL;
    }

    printf("[DEBUG] Processing AST Node: Type=%d, Value=%s\n",
           node->type, node->value ? node->value : "NULL");

    switch (node->type) {

        case NODE_BLOCK: {
            if (strcmp(node->value, "main") == 0) {
                emitTAC("LABEL", NULL, NULL, "main"); // label: 'main'
                for (int i = 0; i < node->childCount; i++) {
                    generateTAC(node->children[i], proc_name); // assignments and CALL
                }
            } else {
                // generic block (no label)
                for (int i = 0; i < node->childCount; i++) {
                    generateTAC(node->children[i], proc_name);
                }
            }
            return NULL;
        }

        case NODE_PROC_DECL: {
            emitTAC("LABEL", NULL, NULL, node->value); // label: procedure name
            generateTAC(node->children[0], node->value); // procedure body
            emitTAC("RETURN", NULL, NULL, NULL); // return from procedure
            char* old_value = strdup("main"); // restore procedure level
            registerTemp(old_value);
            proc_name = old_value;
            return NULL;
        }

        case NODE_WHILE: {
            printf("[DEBUG] Processing WHILE condition\n");

            char *start_label = newLabel();
            char *end_label = newLabel();
            emitTAC("LABEL", NULL, NULL, start_label); // L0:

            // evaluate condition (e.g. b != 0)
            char *cond_temp = generateTAC(node->children[0], proc_name); // t2 = != t0 t1

            if (cond_temp == NULL) {
                fprintf(stderr, "[ERROR] Condition result is NULL\n");
                exit(1);
            }

            emitTAC("IF_NOT", cond_temp, end_label, NULL); // IF_NOT t2 GOTO L1

            generateTAC(node->children[1], proc_name); // nested block

            emitTAC("GOTO", start_label, NULL, NULL); // GOTO L0
            emitTAC("LABEL", NULL, NULL, end_label); // L1:
            return NULL;
        }


        case NODE_CONDITION: {
            if (node->childCount != 2) {
                fprintf(stderr, "Error: CONDITION node must have two children\n");
                exit(EXIT_FAILURE);
            }
            if (strcmp(node->value, "#") == 0) {
                //  "#" --> "!="
                char *left = generateTAC(node->children[0], proc_name);
                char *right = generateTAC(node->children[1], proc_name);
                char *result = newTemp();
                emitTAC("!=", left, right, result);
                return result;
            }
            char *left = generateTAC(node->children[0], proc_name);
            char *right = generateTAC(node->children[1], proc_name);
            char *result = newTemp();
            emitTAC(node->value, left, right, result); // t5 = > t3 t4
            return result;
        }

        case NODE_IF: {
            char *cond_temp = generateTAC(node->children[0], proc_name); // eval condition
            char *skip_label = newLabel();
            printf("[DEBUG] IF condition temp: %s, skip label: %s\n", cond_temp, skip_label);
            emitTAC("IF_NOT", cond_temp, skip_label, NULL); // IF_NOT cond_temp GOTO L2

            // IF body (assignment)
            generateTAC(node->children[1], proc_name);

            emitTAC("LABEL", NULL, NULL, skip_label); // L2:
            return NULL;
        }


        case NODE_ASSIGNMENT: {
            char* temp = generateTAC(node->children[0], proc_name);
            printf("[DEBUG] Assignment: %s = %s\n", node->value, temp);
            if (temp) {
                Variable* resolved_var = findVariable(proc_name, node->value);
                if (!resolved_var) {
                    fprintf(stderr, "Error: Undefined variable '%s' in '%s'\n", node->value, proc_name);
                    exit(EXIT_FAILURE);
                }

                char* new_var = strdup(resolved_var->name);
                if (!new_var) {
                    fprintf(stderr, "[ERROR] Memory allocation failed new var in assignment\n");
                    exit(EXIT_FAILURE);
                }
                emitTAC("=", temp, NULL, new_var);

            } else {
                fprintf(stderr, "Error: Assignment has no value\n");
            }
            return NULL;
        }

        case NODE_OPERATOR: {
            // operator (e.g. -, +)
            char *left = generateTAC(node->children[0], proc_name);
            if (!left) {
                fprintf(stderr, "[ERROR] Left operand is NULL\n");
                exit(EXIT_FAILURE);
            }

            char *right = generateTAC(node->children[1], proc_name);
            if (!right) {
                fprintf(stderr, "[ERROR] Right operand is NULL\n");
                exit(EXIT_FAILURE);
            }

            char *result = newTemp();
            if (!result) {
                fprintf(stderr, "[ERROR] Result is NULL\n");
                exit(EXIT_FAILURE);
            }

            printf("[DEBUG] Operator: %s %s %s -> %s\n", left, node->value, right, result);
            emitTAC(node->value, left, right, result); // t8 = - t6 t7
            return result;
        }

        case NODE_TERM: {
            if (node->childCount != 2) {
                fprintf(stderr, "Error: TERM node must have two children\n");
                exit(1);
            }
            char *left = generateTAC(node->children[0], proc_name);
            if (!left) {
                fprintf(stderr, "[ERROR] Left operand is NULL\n");
                exit(EXIT_FAILURE);
            }

            char *right = generateTAC(node->children[1], proc_name);
            if (!right) {
                fprintf(stderr, "[ERROR] Right operand is NULL\n");
                exit(EXIT_FAILURE);
            }

            char *result = newTemp();
            if (!result) {
                fprintf(stderr, "[ERROR] Result is NULL\n");
                exit(EXIT_FAILURE);
            }

            emitTAC(node->value, left, right, result); // e.g., t4 = * t2 t3
            return result;
        }

        case NODE_FACTOR: {
            if (node->childCount == 1) {
                return generateTAC(node->children[0], proc_name); // fwrd single child
            } else if (node->childCount == 2 && strcmp(node->value, "-") == 0) {
                char *operand = generateTAC(node->children[1], proc_name);
                char *result = newTemp();
                emitTAC("NEG", operand, NULL, result); // negate factor: t6 = NEG t5
                return result;
            } else {
                fprintf(stderr, "Error: Invalid FACTOR node\n");
                exit(EXIT_FAILURE);
            }
        }

        case NODE_EXPRESSION: {

            if (node->childCount == 1) {
                // passing the child node to generateTAC?
                return generateTAC(node->children[0], proc_name);
            } else if (node->childCount == 2) {
                // binary expression .. ever occurs? see AST
                char *left = generateTAC(node->children[0], proc_name);
                char *right = generateTAC(node->children[1], proc_name);
                if (!left || !right) {
                    fprintf(stderr, "[ERROR] Invalid operands in expression\n");
                    exit(EXIT_FAILURE);
                }
                char *result = newTemp();
                emitTAC(node->value, left, right, result);
                return result;
            } else {
                fprintf(stderr, "[ERROR] Invalid number of children in expression node\n");
                exit(EXIT_FAILURE);
            }
        }

        case NODE_IDENTIFIER: {
            Variable* resolved_var = findVariable(proc_name, node->value);
            if (!resolved_var) {
                fprintf(stderr, "Error: Undefined variable '%s'\n", node->value);
                exit(EXIT_FAILURE);
            }
            char* temp = newTemp();
            if (!temp) {
                fprintf(stderr, "[ERROR] newTemp() returned NULL!\n");
                exit(EXIT_FAILURE);
            }
            emitTAC("LOAD", resolved_var->name, NULL, temp);
            return temp;
        }

        case NODE_NUMBER: {
            if (!node->value) {
                fprintf(stderr, "[ERROR] NODE_NUMBER has NULL value!\n");
                exit(EXIT_FAILURE);
            }
            
            printf("[DEBUG] Processing NUMBER: %s\n", node->value);

            char *temp = newTemp();

            if (!temp) {
                fprintf(stderr, "[ERROR] newTemp() returned NULL!\n");
                exit(EXIT_FAILURE);
            }
            printf("[DEBUG] Created temp variable: %s\n", temp);


            emitTAC("LOAD", node->value, NULL, temp);
            printf("[DEBUG] Emitted TAC: LOAD %s -> %s\n", node->value, temp);

            return temp;
        }

        case NODE_CONST_DECL: {

            char *value_temp = generateTAC(node->children[0], proc_name);
            emitTAC("=", value_temp, NULL, node->value);
            return NULL;
        }

        case NODE_CALL: {
            if (!node->value) {
                fprintf(stderr, "[ERROR] Procedure name is NULL\n");
                exit(EXIT_FAILURE);
            }
            emitTAC("CALL", node->value, NULL, NULL);
            return NULL;
        }


        default:
            printf("[DEBUG] Default case, processing children\n");
            for (int i = 0; i < node->childCount; i++) {
                generateTAC(node->children[i], proc_name);
            }
            return NULL;
    }
}



void printTAC() {
    TAC *current = tac_head;

    printf("[DEBUG] Printing TAC Instructions:\n");
  
    while (current) {

        if (strcmp(current->op, "LABEL") == 0) {
            printf("%s:\n", current->result);

        } else if (strcmp(current->op, "IF_NOT") == 0) {
            printf("IF_NOT %s GOTO %s\n", current->arg1, current->arg2); // conditional jumps

        } else if (strcmp(current->op, "GOTO") == 0) {
            printf("GOTO %s\n", current->arg1); // unconditional jumps

        } else if (strcmp(current->op, "CALL") == 0) {
            printf("CALL %s\n", current->arg1); // procedure calls

        } else if (strcmp(current->op, "LOAD") == 0) {
            printf("%s = LOAD %s\n", current->result, current->arg1); // loads

        } else if (strcmp(current->op, "RETURN") == 0) {
            printf("RETURN\n"); // procedure return

        } else if (strcmp(current->op, "=") == 0) {  // assignments
            printf("%s = %s\n", current->result, current->arg1);

        } else {
            // standard ops (+, -, !=)
            printf("%s = %s %s %s\n", current->result, current->op, current->arg1, current->arg2);
        }
        current = current->next;
    }
}


void printTACtoFile(const char *filename) {
    FILE *file = fopen(filename, "w");
    if (!file) {
        fprintf(stderr, "Error: Could not open file %s for writing\n", filename);
        exit(EXIT_FAILURE);
    }

    TAC *current = tac_head;

    while (current) {
        if (strcmp(current->op, "LABEL") == 0) {
            fprintf(file, "%s:\n", current->result);

        } else if (strcmp(current->op, "IF_NOT") == 0) {
            fprintf(file, "IF_NOT %s GOTO %s\n", current->arg1, current->arg2);

        } else if (strcmp(current->op, "GOTO") == 0) {
            fprintf(file, "GOTO %s\n", current->arg1);

        } else if (strcmp(current->op, "CALL") == 0) {
            fprintf(file, "CALL %s\n", current->arg1);

        } else if (strcmp(current->op, "LOAD") == 0) {
            fprintf(file, "%s = LOAD %s\n", current->result, current->arg1);

        } else if (strcmp(current->op, "RETURN") == 0) {
            fprintf(file, "RETURN\n");

        } else if (strcmp(current->op, "=") == 0) {
            fprintf(file, "%s = %s\n", current->result, current->arg1);

        } else {
            // Standard operations (+, -, *, /, !=, etc.)
            fprintf(file, "%s = %s %s %s\n", current->result, current->op, current->arg1, current->arg2);
        }
        current = current->next;
    }

    fclose(file);
}


void exportTACFile(FILE *file) {
    TAC *current = tac_head;
    while (current) {
        fprintf(file, "TYPE: %s\n", current->op);
        fprintf(file, "ARG1: %s\n", current->arg1 ? current->arg1 : "NULL");
        fprintf(file, "ARG2: %s\n", current->arg2 ? current->arg2 : "NULL");
        fprintf(file, "RESULT: %s\n\n", current->result ? current->result : "NULL");  // Empty line as separator
        current = current->next;
    }
}


void exportTAC(const char *filename) {
    FILE *file = fopen(filename, "w");
    if (!file) {
        perror("Error opening file");
        exit(1);
    }
    exportTACFile(file);
    fclose(file);
}

void parseTAC(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Error opening file");
        return;
    }

    char line[128], op[32], arg1[32], arg2[32], result[32];

    while (fgets(line, sizeof(line), file)) {
        if (strncmp(line, "TYPE:", 5) == 0) {
            sscanf(line, "TYPE: %s", op);
        } else if (strncmp(line, "ARG1:", 5) == 0) {
            sscanf(line, "ARG1: %s", arg1);
        } else if (strncmp(line, "ARG2:", 5) == 0) {
            sscanf(line, "ARG2: %s", arg2);
        } else if (strncmp(line, "RESULT:", 7) == 0) {
            sscanf(line, "RESULT: %s", result);
            // Now we have a complete instruction
            printf("Parsed TAC - OP: %s, ARG1: %s, ARG2: %s, RESULT: %s\n",
                   op, arg1, arg2, result);
        }
    }

    fclose(file);
}

