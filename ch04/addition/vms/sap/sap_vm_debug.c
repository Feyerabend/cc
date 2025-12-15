#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <stdint.h>
#include "sap_vm.h"
#include "sap_vm_config.h"
#include "sap_vm_samples.h"

typedef void (*command_handler_t)(sap_vm_t *vm, const char *args);

typedef struct {
    const char *name;
    const char *alias;
    command_handler_t handler;
    const char *description;
} command_t;

// Forward declarations for command handlers
static void cmd_help(sap_vm_t *vm, const char *args);
static void cmd_state(sap_vm_t *vm, const char *args);
static void cmd_step(sap_vm_t *vm, const char *args);
static void cmd_run(sap_vm_t *vm, const char *args);
static void cmd_reset(sap_vm_t *vm, const char *args);
static void cmd_memory(sap_vm_t *vm, const char *args);
static void cmd_disasm(sap_vm_t *vm, const char *args);
static void cmd_breakpoint(sap_vm_t *vm, const char *args);
static void cmd_trace(sap_vm_t *vm, const char *args);

static const command_t commands[] = {
    {"help", "h", cmd_help, "Show this help"},
    {"quit", "q", NULL, "Exit debugger (also 'exit')"},
    {"state", "s", cmd_state, "Show VM state"},
    {"step", "st", cmd_step, "Execute one instruction"},
    {"run", "r", cmd_run, "Run VM (default: until halt) [cycles]"},
    {"reset", NULL, cmd_reset, "Reset VM to initial state"},
    {"memory", "mem", cmd_memory, "Show memory contents [start] [end]"},
    {"disasm", "dis", cmd_disasm, "Disassemble instructions [start] [count]"},
    {"breakpoint", "bp", cmd_breakpoint, "Manage breakpoints [add|del|list] [addr]"},
    {"load", "l", cmd_load_sample, "Load sample program <program>"},
    {"trace", "t", cmd_trace, "Enable/disable instruction tracing [on|off]"},
    {NULL, NULL, NULL, NULL}
};

static void print_banner(void);
static bool get_user_input(char *buffer, size_t size);
static bool parse_command(const char *input, char *command, char *args);
static uint16_t parse_address(const char *str);
static int parse_number(const char *str);

int main(void) {
    sap_vm_t vm;
    char input[MAX_INPUT_SIZE];
    char command[MAX_COMMAND_SIZE];
    char args[MAX_ARGS_SIZE];
    print_banner();
    vm_init(&vm);
    printf("SAP VM initialized. Type 'help' for commands.\n\n");
    while (true) {
        printf("sap-vm> ");
        if (!get_user_input(input, sizeof(input))) {
            continue;
        }
        if (!parse_command(input, command, args)) {
            continue;
        }
        for (char *p = command; *p; p++) {
            *p = tolower(*p);
        }
        bool handled = false;
        for (const command_t *cmd = commands; cmd->name; cmd++) {
            if (strcmp(command, cmd->name) == 0 || (cmd->alias && strcmp(command, cmd->alias) == 0)) {
                if (cmd->handler) {
                    cmd->handler(&vm, args);
                } else if (strcmp(cmd->name, "quit") == 0) {
                    printf("Goodbye!\n");
                    vm_destroy(&vm);
                    return 0;
                }
                handled = true;
                break;
            }
        }
        if (!handled) {
            printf("Unknown command: %s. Type 'help' for available commands.\n", command);
        }
        printf("\n");
    }
    return 0;
}

static void print_banner(void) {
    printf("======================================\n");
    printf("    SAP VM Debugger & Test Suite     \n");
    printf("         Version 1.0                 \n");
    printf("======================================\n\n");
}

static bool get_user_input(char *buffer, size_t size) {
    if (fgets(buffer, size, stdin) == NULL) {
        return false;
    }
    size_t len = strlen(buffer);
    if (len > 0 && buffer[len - 1] == '\n') {
        buffer[len - 1] = '\0';
    }
    return strlen(buffer) > 0;
}

static bool parse_command(const char *input, char *command, char *args) {
    char temp[MAX_INPUT_SIZE];
    strncpy(temp, input, MAX_INPUT_SIZE - 1);
    temp[MAX_INPUT_SIZE - 1] = '\0';
    command[0] = args[0] = '\0';
    return sscanf(temp, "%31s %223[^\n]", command, args) >= 1;
}

static uint16_t parse_address(const char *str) {
    if (!str || !str[0]) return 0;
    if (strncmp(str, "0x", 2) == 0 || strncmp(str, "0X", 2) == 0) {
        return (uint16_t)strtol(str, NULL, 16);
    }
    return (uint16_t)strtol(str, NULL, 10);
}

static int parse_number(const char *str) {
    if (!str || !str[0]) return 0;
    return (int)strtol(str, NULL, 0);
}

static void cmd_help(sap_vm_t *vm, const char *args) {
    (void)vm;
    (void)args; // Unused parameter
    printf("Available commands:\n");
    for (const command_t *cmd = commands; cmd->name; cmd++) {
        printf("  %s", cmd->name);
        if (cmd->alias) printf(", %s", cmd->alias);
        printf("%*s - %s\n", (int)(20 - strlen(cmd->name) - (cmd->alias ? strlen(cmd->alias) + 2 : 0)), "", cmd->description);
    }
    printf("\nSample programs:\n");
    print_sample_programs();
}

static void cmd_state(sap_vm_t *vm, const char *args) {
    (void)args; // Unused parameter
    vm_print_state(vm);
}

static void cmd_step(sap_vm_t *vm, const char *args) {
    (void)args; // Unused parameter
    result_t result = vm_step(vm);
    switch (result) {
        case RESULT_OK:
            printf("Step completed.\n");
            break;
        case RESULT_HALT:
            printf("Program halted.\n");
            break;
        case RESULT_ERROR:
            printf("Error: %s\n", vm->last_error);
            break;
        case RESULT_BREAKPOINT:
            printf("Breakpoint hit at PC=0x%04X\n", vm->last_pc);
            break;
    }
    vm_print_state(vm);
}

static void cmd_run(sap_vm_t *vm, const char *args) {
    uint64_t cycles = UINT64_MAX;
    if (args && strlen(args) > 0) {
        cycles = (uint64_t)parse_number(args);
        if (cycles == 0) {
            cycles = UINT64_MAX;
        }
    }
    printf("Running VM");
    if (cycles != UINT64_MAX) {
        printf(" for %llu cycles", cycles);
    }
    printf("...\n");
    result_t result = vm_run(vm, cycles);
    switch (result) {
        case RESULT_OK:
            printf("Execution completed.\n");
            break;
        case RESULT_HALT:
            printf("Program halted normally.\n");
            break;
        case RESULT_ERROR:
            printf("Execution error: %s\n", vm->last_error);
            break;
        case RESULT_BREAKPOINT:
            printf("Breakpoint hit.\n");
            break;
    }
    vm_print_state(vm);
}

static void cmd_reset(sap_vm_t *vm, const char *args) {
    (void)args; // Unused parameter
    vm_reset(vm);
    vm_print_state(vm);
}

static void cmd_memory(sap_vm_t *vm, const char *args) {
    uint16_t start = 0, end = 15;
    if (args && strlen(args) > 0) {
        char start_str[32], end_str[32];
        int parsed = sscanf(args, "%31s %31s", start_str, end_str);
        if (parsed >= 1) {
            start = parse_address(start_str);
        }
        if (parsed >= 2) {
            end = parse_address(end_str);
        } else {
            end = start + 15;
        }
    }
    vm_print_memory(vm, start, end);
}

static void cmd_disasm(sap_vm_t *vm, const char *args) {
    uint16_t start = vm->cpu.pc;
    uint16_t count = 10;
    if (args && strlen(args) > 0) {
        char start_str[32], count_str[32];
        int parsed = sscanf(args, "%31s %31s", start_str, count_str);
        if (parsed >= 1) {
            start = parse_address(start_str);
        }
        if (parsed >= 2) {
            count = parse_address(count_str);
        }
    }
    vm_print_disassembly(vm, start, count);
}

static void cmd_breakpoint(sap_vm_t *vm, const char *args) {
    if (!args || strlen(args) == 0) {
        vm_list_breakpoints(vm);
        return;
    }
    char action[32], addr_str[32];
    int parsed = sscanf(args, "%31s %31s", action, addr_str);
    if (parsed < 1) {
        printf("Usage: breakpoint [add|del|list] [address]\n");
        return;
    }
    for (char *p = action; *p; p++) {
        *p = tolower(*p);
    }
    if (strcmp(action, "list") == 0 || strcmp(action, "l") == 0) {
        vm_list_breakpoints(vm);
    }
    else if (strcmp(action, "add") == 0 || strcmp(action, "a") == 0) {
        if (parsed < 2) {
            printf("Usage: breakpoint add <address>\n");
            return;
        }
        uint16_t addr = parse_address(addr_str);
        if (vm_add_breakpoint(vm, addr) == RESULT_OK) {
            printf("Breakpoint added at 0x%04X\n", addr);
        }
    }
    else if (strcmp(action, "del") == 0 || strcmp(action, "delete") == 0 || 
             strcmp(action, "remove") == 0 || strcmp(action, "d") == 0) {
        if (parsed < 2) {
            printf("Usage: breakpoint del <address>\n");
            return;
        }
        uint16_t addr = parse_address(addr_str);
        if (vm_remove_breakpoint(vm, addr) == RESULT_OK) {
            printf("Breakpoint removed from 0x%04X\n", addr);
        }
    }
    else {
        printf("Unknown breakpoint action: %s\n", action);
        printf("Available actions: add, del, list\n");
    }
}

static void cmd_trace(sap_vm_t *vm, const char *args) {
    if (!args || strlen(args) == 0) {
        printf("Instruction tracing is %s\n", vm->trace_enabled ? "ON" : "OFF");
        return;
    }
    char setting[32];
    sscanf(args, "%31s", setting);
    for (char *p = setting; *p; p++) {
        *p = tolower(*p);
    }
    if (strcmp(setting, "on") == 0 || strcmp(setting, "1") == 0 || 
        strcmp(setting, "true") == 0 || strcmp(setting, "yes") == 0) {
        vm->trace_enabled = true;
        printf("Instruction tracing enabled.\n");
    }
    else if (strcmp(setting, "off") == 0 || strcmp(setting, "0") == 0 || 
             strcmp(setting, "false") == 0 || strcmp(setting, "no") == 0) {
        vm->trace_enabled = false;
        printf("Instruction tracing disabled.\n");
    }
    else {
        printf("Usage: trace [on|off]\n");
    }
}

