#include <stdio.h>
#include "profiler.h"

void profiler_start(Profiler *profiler) {
    profiler->start = clock();
    profiler->current_memory = 0;
    profiler->peak_memory = 0;
    profiler->stack_depth = 0;
    profiler->peak_stack_depth = 0;
    for (int i = 0; i < NUM_OPCODES; i++) {
        profiler->opcode_time[i] = 0.0;
        profiler->opcode_count[i] = 0;
    }
}

void profiler_stop(Profiler *profiler) {
    profiler->end = clock();
}

void profiler_opcode_start(Profiler *profiler, int opcode) {
    profiler->opcode_start[opcode] = clock();
}

void profiler_opcode_stop(Profiler *profiler, int opcode) {
    clock_t opcode_end = clock();
    profiler->opcode_time[opcode] += (double)(opcode_end - profiler->opcode_start[opcode]) / CLOCKS_PER_SEC;
    profiler->opcode_count[opcode]++;
}

void profiler_track_allocation(Profiler *profiler, size_t size) {
    profiler->current_memory += size;
    if (profiler->current_memory > profiler->peak_memory) {
        profiler->peak_memory = profiler->current_memory;
    }
}

void profiler_track_deallocation(Profiler *profiler, size_t size) {
    if (profiler->current_memory >= size) {
        profiler->current_memory -= size;
    }
}

void profiler_update_stack_depth(Profiler *profiler, int sp) {
    profiler->stack_depth = sp + 1;
    if (profiler->stack_depth > profiler->peak_stack_depth) {
        profiler->peak_stack_depth = profiler->stack_depth;
    }
}

void profiler_print(Profiler *profiler) {
    double total_time = (double)(profiler->end - profiler->start) / CLOCKS_PER_SEC;
    printf("Total execution time: %.6f seconds\n", total_time);
    printf("Peak memory usage: %zu bytes\n", profiler->peak_memory);
    printf("Peak stack depth: %d\n", profiler->peak_stack_depth);

    printf("\nOpcode Execution Profile:\n");
    printf("%-10s %-15s %-10s\n", "Opcode", "Time (s)", "Count");
    printf("------------------------------------------------\n");

    for (int i = 0; i < NUM_OPCODES; i++) {
        if (profiler->opcode_count[i] > 0) {
            printf("%-10d %-15.6f %-10d\n", i, profiler->opcode_time[i], profiler->opcode_count[i]);
        }
    }
}