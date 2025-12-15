#ifndef SAP_VM_SAMPLES_H
#define SAP_VM_SAMPLES_H

#include "sap_vm.h"

// Declare functions for loading sample programs and printing their descriptions
void cmd_load_sample(sap_vm_t *vm, const char *program_name);
void print_sample_programs(void);

#endif // SAP_VM_SAMPLES_H

