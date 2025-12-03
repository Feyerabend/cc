#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// Converts an integer to a string in the given base (2–36)
void int_to_base_str(int value, int base, char *output, size_t output_size) {
    const char *digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    char buf[64];
    int i = 0;

    if (base < 2 || base > 36) {
        snprintf(output, output_size, "Invalid base");
        return;
    }

    int is_negative = 0;
    if (value < 0) {
        is_negative = 1;
        value = -value;
    }

    do {
        buf[i++] = digits[value % base];
        value /= base;
    } while (value > 0);

    if (is_negative) buf[i++] = '-';

    buf[i] = '\0';

    // Reverse the string
    int len = strlen(buf);
    for (int j = 0; j < len; ++j) {
        output[j] = buf[len - j - 1];
    }
    output[len] = '\0';
}

int main() {
    int in_base, out_base;
    char number_str[64];
    char result_str[64];

    printf("General base converter (bases 2–36)\n");
    printf("Example: Convert from base 16 to base 10, number 1A\n");

    while (1) {
        printf("\nEnter input base (2–36): ");
        if (scanf("%d", &in_base) != 1 || in_base < 2 || in_base > 36) {
            printf("Invalid input base.\n");
            while (getchar() != '\n'); // clear buffer
            continue;
        }

        printf("Enter output base (2–36): ");
        if (scanf("%d", &out_base) != 1 || out_base < 2 || out_base > 36) {
            printf("Invalid output base.\n");
            while (getchar() != '\n');
            continue;
        }

        printf("Enter number to convert: ");
        scanf("%s", number_str);

        // Convert input string to integer
        int value = (int)strtol(number_str, NULL, in_base);

        // Convert integer to output base string
        int_to_base_str(value, out_base, result_str, sizeof(result_str));

        printf("Result: %s (decimal: %d)\n", result_str, value);
    }

    return 0;
}
