#include <stdio.h>
#include <string.h>

/* Vulnerable: strcpy performs no bounds check */
void greet(char *name) {
    char buf[64];
    strcpy(buf, name);          /* overflows if strlen(name) >= 64 */
    printf("Hello, %s!\n", buf);
}

/* Safe: snprintf enforces the buffer size */
void greet_safe(const char *name) {
    char buf[64];
    snprintf(buf, sizeof(buf), "%s", name);
    printf("Hello, %s!\n", buf);
}
