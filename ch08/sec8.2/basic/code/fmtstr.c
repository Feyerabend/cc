#include <stdio.h>

/* Vulnerable: user input is the format string; %x/%n can read/write memory */
void log_bad(const char *msg) {
    printf(msg);                    /* msg = "%x %x %x" leaks stack values */
}

/* Safe: msg is always treated as data, never as a format string */
void log_safe(const char *msg) {
    printf("%s", msg);
}
