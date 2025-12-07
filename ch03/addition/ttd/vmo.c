#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// types for fields
typedef enum {
    TYPE_INT,
    TYPE_FLOAT,
} FieldType;

// flexible field structure (union int and float)
typedef struct {
    char *name;
    FieldType type;
    union {
        int int_value;
        float float_value;
    } value;
} Field;

// object structure
typedef struct {
    char *name;
    Field *fields;
    int field_count;
} Object;

// VM instructions
typedef enum {
    PRINT,
    ADD,
    SUB,
    MUL,
    DIV,
    HALT
} Instruction;

// VM instruction structure
typedef struct {
    Instruction instruction;
    int field_index;
    float operand;
} VMInstruction;

// VM structure
typedef struct {
    VMInstruction *method;  // array of VM instructions (method)
    int method_length;      // number of instructions in the method
    int pc;                 // program counter
} VirtualMachine;

// snapshot structure
typedef struct {
    int pc;                 // program counter
    Field *fields_snapshot; // copy of object fields
    int field_count;        // number of fields
} Snapshot;

// fwd decl
void print_fields(const Object *obj);
void run_vm(VirtualMachine *vm, Object *obj);
Object *create_object(const char *name, Field *fields, int field_count);
void free_object(Object *obj);
Snapshot *create_snapshot(const VirtualMachine *vm, const Object *obj);
void load_snapshot(VirtualMachine *vm, Object *obj, Snapshot *snapshot);
void free_snapshot(Snapshot *snapshot);

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

void free_object(Object *obj) {
    free(obj->fields);
    free(obj->name);
    free(obj);
}

// snapshot of VM state
Snapshot *create_snapshot(const VirtualMachine *vm, const Object *obj) {
    Snapshot *snapshot = malloc(sizeof(Snapshot));
    snapshot->pc = vm->pc;
    snapshot->field_count = obj->field_count;
    snapshot->fields_snapshot = malloc(obj->field_count * sizeof(Field));
    memcpy(snapshot->fields_snapshot, obj->fields, obj->field_count * sizeof(Field));
    return snapshot;
}

// load snapshot to restore VM state
void load_snapshot(VirtualMachine *vm, Object *obj, Snapshot *snapshot) {
    vm->pc = snapshot->pc;
    memcpy(obj->fields, snapshot->fields_snapshot, snapshot->field_count * sizeof(Field));
}

// free snapshot
void free_snapshot(Snapshot *snapshot) {
    free(snapshot->fields_snapshot);
    free(snapshot);
}

int main() {

    // fields for object
    Field fields[2] = {
        {"field1", TYPE_FLOAT, .value.float_value = 10.0f},
        {"field2", TYPE_INT, .value.int_value = 20}
    };

    // create object
    Object *obj = create_object("ExampleObject", fields, 2);

    printf("Initial state of object:\n");
    print_fields(obj);

    // VM instructions "method"
    VMInstruction method[8];
    method[0] = (VMInstruction){ADD, 0, 5.0f};    // Add 5 to field1
    method[1] = (VMInstruction){PRINT, 0, 0};     // Print state
    method[2] = (VMInstruction){SUB, 1, 10};      // Subtract 10 from field2
    method[3] = (VMInstruction){PRINT, 0, 0};     // Print state
    method[4] = (VMInstruction){MUL, 0, 2.0f};    // Multiply field1 by 2
    method[5] = (VMInstruction){PRINT, 0, 0};     // Print state
    method[6] = (VMInstruction){DIV, 1, 2};       // Divide field2 by 2
    method[7] = (VMInstruction){HALT, 0, 0};      // Halt VM

    // create the VM
    VirtualMachine vm = {method, 8, 0};  // 8 instructions

    // snapshots at various points
    Snapshot *snapshot1 = create_snapshot(&vm, obj);  // snapshot after first add
    run_vm(&vm, obj);  // .. until halt

    // first rewind
    printf("\n--- Rewind to Snapshot 1 ---\n");
    load_snapshot(&vm, obj, snapshot1);
    print_fields(obj);  // state after rewinding to first snapshot: 1

    // another snapshot after first rewind
    Snapshot *snapshot2 = create_snapshot(&vm, obj);  // snapshot after first rewind

    // run again to another state
    run_vm(&vm, obj);  // .. until halt again

    // second rewind
    printf("\n--- Rewind to Snapshot 2 ---\n");
    load_snapshot(&vm, obj, snapshot2);
    print_fields(obj);  // show state after rewinding to second snapshot: 2

    // clean up
    free_snapshot(snapshot1);
    free_snapshot(snapshot2);
    free_object(obj);

    return 0;
}