#include <stdio.h>
#include <string.h>
#include "sap_vm.h"
#include "sap_vm_config.h"

result_t vm_add_breakpoint(sap_vm_t *vm, uint16_t address) {
    if (!vm_is_valid_address(address)) {
        return vm_set_error(vm, "Invalid breakpoint address 0x%04X", address);
    }
    for (int i = 0; i < vm->breakpoint_count; i++) {
        if (vm->breakpoints[i].address == address && vm->breakpoints[i].enabled) {
            return vm_set_error(vm, "Breakpoint already exists at 0x%04X", address);
        }
    }
    int slot = -1;
    for (int i = 0; i < vm->breakpoint_count; i++) {
        if (!vm->breakpoints[i].enabled) {
            slot = i;
            break;
        }
    }
    if (slot == -1) {
        if (vm->breakpoint_count >= MAX_BREAKPOINTS) {
            return vm_set_error(vm, "Maximum breakpoints (%d) reached", MAX_BREAKPOINTS);
        }
        slot = vm->breakpoint_count++;
    }
    vm->breakpoints[slot].address = address;
    vm->breakpoints[slot].enabled = true;
    vm->breakpoints[slot].hit_count = 0;
    vm->breakpoints[slot].condition[0] = '\0';
    if (vm->debug_enabled) {
        printf("Breakpoint added at 0x%04X (slot %d)\n", address, slot);
    }
    return RESULT_OK;
}

result_t vm_remove_breakpoint(sap_vm_t *vm, uint16_t address) {
    for (int i = 0; i < vm->breakpoint_count; i++) {
        if (vm->breakpoints[i].address == address && vm->breakpoints[i].enabled) {
            vm->breakpoints[i].enabled = false;
            if (vm->debug_enabled) {
                printf("Breakpoint removed from 0x%04X\n", address);
            }
            return RESULT_OK;
        }
    }
    return vm_set_error(vm, "No breakpoint found at 0x%04X", address);
}

void vm_list_breakpoints(sap_vm_t *vm) {
    printf("Active breakpoints:\n");
    bool found_any = false;
    for (int i = 0; i < vm->breakpoint_count; i++) {
        if (vm->breakpoints[i].enabled) {
            printf("  0x%04X (hits: %d)\n", 
                   vm->breakpoints[i].address, 
                   vm->breakpoints[i].hit_count);
            found_any = true;
        }
    }
    if (!found_any) {
        printf("  No breakpoints set.\n");
    }
    printf("\n");
}

bool vm_check_breakpoint(sap_vm_t *vm, uint16_t address) {
    for (int i = 0; i < vm->breakpoint_count; i++) {
        if (vm->breakpoints[i].address == address && vm->breakpoints[i].enabled) {
            vm->breakpoints[i].hit_count++;
            return true;
        }
    }
    return false;
}

result_t vm_load_program(sap_vm_t *vm, const char *filename) {
    if (!filename || !filename[0]) {
        return vm_set_error(vm, "No filename specified");
    }
    FILE *file = fopen(filename, "rb");
    if (!file) {
        return vm_set_error(vm, "Cannot open file: %s", filename);
    }
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);
    if (file_size < 0 || (size_t)file_size > MEMORY_SIZE * sizeof(int16_t)) {
        fclose(file);
        return vm_set_error(vm, "Invalid file size: %ld bytes", file_size);
    }
    size_t words_read = fread(vm->memory, sizeof(int16_t), file_size / sizeof(int16_t), file);
    if (ferror(file)) {
        fclose(file);
        return vm_set_error(vm, "Error reading file: %s", filename);
    }
    fclose(file);
    if (vm->debug_enabled) {
        printf("Loaded %zu words from %s\n", words_read, filename);
    }
    vm_reset(vm);
    return RESULT_OK;
}

result_t vm_save_program(sap_vm_t *vm, const char *filename, 
                       uint16_t start_addr, uint16_t end_addr) {
    if (!filename || !filename[0]) {
        return vm_set_error(vm, "No filename specified");
    }
    if (!vm_is_valid_address(start_addr) || !vm_is_valid_address(end_addr)) {
        return vm_set_error(vm, "Invalid address range");
    }
    if (start_addr > end_addr) {
        return vm_set_error(vm, "Start address must be <= end address");
    }
    FILE *file = fopen(filename, "wb");
    if (!file) {
        return vm_set_error(vm, "Cannot create file: %s", filename);
    }
    size_t words_to_write = end_addr - start_addr + 1;
    size_t words_written = fwrite(&vm->memory[start_addr], sizeof(int16_t), 
                                words_to_write, file);
    fclose(file);
    if (words_written != words_to_write) {
        return vm_set_error(vm, "Error writing to file");
    }
    if (vm->debug_enabled) {
        printf("Saved %zu words to %s\n", words_written, filename);
    }
    return RESULT_OK;
}

void vm_dump_state(sap_vm_t *vm, const char *filename) {
    FILE *file = fopen(filename, "w");
    if (!file) {
        printf("Error: Cannot create dump file: %s\n", filename);
        return;
    }
    fprintf(file, "SAP VM State Dump\n================\n\n");
    fprintf(file, "VM State: %s\n", vm_state_to_string(vm->state));
    fprintf(file, "Cycles: %llu\n", vm->cycle_count);
    fprintf(file, "Debug enabled: %s\n", vm->debug_enabled ? "Yes" : "No");
    fprintf(file, "Trace enabled: %s\n", vm->trace_enabled ? "Yes" : "No");
    fprintf(file, "\nCPU State:\n");
    fprintf(file, "PC: 0x%04X (%u)\n", vm->cpu.pc, vm->cpu.pc);
    fprintf(file, "SP: 0x%04X (%u)\n", vm->cpu.sp, vm->cpu.sp);
    fprintf(file, "ACC: %d (0x%04X)\n", vm->cpu.accumulator, (uint16_t)vm->cpu.accumulator);
    fprintf(file, "X: %d (0x%04X)\n", vm->cpu.x_reg, vm->cpu.x_reg);
    fprintf(file, "IR: 0x%04X\n", vm->cpu.ir);
    fprintf(file, "\nFlags:\n");
    fprintf(file, "Zero: %d\n", vm->cpu.flags.zero);
    fprintf(file, "Negative: %d\n", vm->cpu.flags.negative);
    fprintf(file, "Carry: %d\n", vm->cpu.flags.carry);
    fprintf(file, "Overflow: %d\n", vm->cpu.flags.overflow);
    fprintf(file, "\nMemory (non-zero locations):\n");
    for (uint16_t addr = 0; addr < MEMORY_SIZE; addr++) {
        if (vm->memory[addr] != 0) {
            fprintf(file, "0x%04X: %6d (0x%04X)\n", 
                   addr, vm->memory[addr], (uint16_t)vm->memory[addr]);
        }
    }
    fprintf(file, "\nBreakpoints:\n");
    bool has_breakpoints = false;
    for (int i = 0; i < vm->breakpoint_count; i++) {
        if (vm->breakpoints[i].enabled) {
            fprintf(file, "0x%04X (hits: %d)\n", 
                   vm->breakpoints[i].address, 
                   vm->breakpoints[i].hit_count);
            has_breakpoints = true;
        }
    }
    if (!has_breakpoints) {
        fprintf(file, "None\n");
    }
    if (vm->state == VM_ERROR) {
        fprintf(file, "\nError Information:\n");
        fprintf(file, "Last error: %s\n", vm->last_error);
        fprintf(file, "Error address: 0x%04X\n", vm->error_address);
    }
    fclose(file);
    printf("VM state dumped to %s\n", filename);
}

