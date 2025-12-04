#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// def types for fields
typedef enum {
    TYPE_INT,
    TYPE_FLOAT,
} FieldType;

// def a flexible field structure (int and float)
typedef struct {
    char *name;
    FieldType type;
    union {
        int int_value;
        float float_value;
    } value;
} Field;

// def the object structure
typedef struct {
    char *name;
    Field *fields;
    int field_count;
} Object;

// Define VM instructions
typedef enum {
    PRINT,
    ADD,
    SUB,
    MUL,
    DIV,
    HALT
} Instruction;

// def VM instr.
typedef struct {
    Instruction instruction;
    int field_index;
    float operand;
} VMInstruction;

// def VM struct
typedef struct {
    VMInstruction *method;  // array of VM instructions (method)
    int method_length;      // number of instructions in the method
    int pc;                 // program counter
} VirtualMachine;

// fwd. decl.
void print_fields(const Object *obj);
void run_vm(VirtualMachine *vm, Object *obj);
Object *create_object(const char *name, Field *fields, int field_count);
void free_object(Object *obj);

void print_fields(const Object *obj) {
    printf("Object: %s\n", obj->name);
    for (int i = 0; i < obj->field_count; i++) {
        if (obj->fields[i].type == TYPE_FLOAT) {
            printf("%s (float): %.2f\n", obj->fields[i].name, obj->fields[i].value.float_value);
        } else {
            printf("%s (int): %d\n", obj->fields[i].name, obj->fields[i].value.int_value);
        }
    }
}

void run_vm(VirtualMachine *vm, Object *obj) {
    while (vm->pc < vm->method_length) {
        VMInstruction *instr = &vm->method[vm->pc];
        Field *field = &obj->fields[instr->field_index];

        switch (instr->instruction) {
            case PRINT:
                print_fields(obj);
                break;
            case ADD:
                if (field->type == TYPE_FLOAT)
                    field->value.float_value += instr->operand;
                else
                    field->value.int_value += (int)instr->operand;
                break;
            case SUB:
                if (field->type == TYPE_FLOAT)
                    field->value.float_value -= instr->operand;
                else
                    field->value.int_value -= (int)instr->operand;
                break;
            case MUL:
                if (field->type == TYPE_FLOAT)
                    field->value.float_value *= instr->operand;
                else
                    field->value.int_value *= (int)instr->operand;
                break;
            case DIV:
                if (field->type == TYPE_FLOAT)
                    field->value.float_value /= instr->operand;
                else
                    field->value.int_value /= (int)instr->operand;
                break;
            case HALT:
                return;
            default:
                printf("Unknown instruction\n");
                return;
        }

        vm->pc++;
    }
}

// object with fields
Object *create_object(const char *name, Field *fields, int field_count) {
    Object *obj = malloc(sizeof(Object));
    obj->name = strdup(name);
    obj->fields = malloc(field_count * sizeof(Field));
    memcpy(obj->fields, fields, field_count * sizeof(Field));
    obj->field_count = field_count;
    return obj;
}

// clean up
void free_object(Object *obj) {
    free(obj->fields);
    free(obj->name);
    free(obj);
}

int main() {
    // Define fields for the object
    Field fields[2] = {
        {"field1", TYPE_FLOAT, .value.float_value = 10.0f},
        {"field2", TYPE_INT, .value.int_value = 20}
    };

    // Create an object
    Object *obj = create_object("ExampleObject", fields, 2);

    // Print the initial state of the object
    printf("Initial state of object:\n");
    print_fields(obj);

    // Dynamically create a method (instructions) that adds to the first field
    VMInstruction method[4];
    method[0] = (VMInstruction){PRINT, 0, 0};     // Print the first field
    method[1] = (VMInstruction){ADD, 0, 5.0f};    // Add 5 to the first field
    method[2] = (VMInstruction){PRINT, 0, 0};     // Print the updated field
    method[3] = (VMInstruction){HALT, 0, 0};      // Halt the VM

    // Create and run the virtual machine with the method
    VirtualMachine vm = {method, 4, 0};  // 4 instructions
    printf("\nRunning VM method:\n");
    run_vm(&vm, obj);

    // Clean up
    free_object(obj);

    return 0;
}

/*

// Simple addition program

object ExampleObject {
    field field1: float = 10.0;   // Initial value of the first field
    field field2: int = 20;       // Initial value of the second field

    method addValue() {
        print(field1);            // Print the initial value of field1
        field1 = field1 + 5.0;    // Add 5 to field1
        print(field1);            // Print the updated value of field1
    }
}

ExampleObject.addValue();  // Call the addValue method

*/