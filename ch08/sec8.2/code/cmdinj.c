#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/* Vulnerable: filename = "; rm -rf /" causes catastrophic execution */
void show_file_bad(const char *filename) {
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "cat %s", filename);
    system(cmd);                /* shell interprets metacharacters */
}

/* Safe: exec does not invoke a shell; filename is just an argument */
void show_file_safe(const char *filename) {
    execlp("cat", "cat", filename, (char *)NULL);
}
