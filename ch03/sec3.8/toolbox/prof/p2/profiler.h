#ifndef PROFILER_H
#define PROFILER_H

#include <time.h>

#define NUM_OPCODES 256

typedef struct {
    clock_t start;
    clock_t end;
    clock_t opcode_start[NUM_OPCODES];
    double opcode_time[NUM_OPCODES];
    int opcode_count[NUM_OPCODES];
    size_t current_memory;
    size_t peak_memory;
    int stack_depth;
    int peak_stack_depth;
} Profiler;

void profiler_start(Profiler *profiler);
void profiler_stop(Profiler *profiler);
void profiler_opcode_start(Profiler *profiler, int opcode);
void profiler_opcode_stop(Profiler *profiler, int opcode);
void profiler_track_allocation(Profiler *profiler, size_t size);
void profiler_track_deallocation(Profiler *profiler, size_t size);
void profiler_update_stack_depth(Profiler *profiler, int sp);
void profiler_print(Profiler *profiler);

#endif