#include <stdio.h>
#include <stdint.h>

// Convert an 8-bit BCD number (two digits) to decimal
int bcd_to_decimal(uint8_t bcd) {
    int high = (bcd >> 4) & 0x0F;  // upper nibble
    int low  = bcd & 0x0F;         // lower nibble
    return high * 10 + low;
}

// Convert a multi-byte BCD number to decimal
long bcd_to_decimal32(uint32_t bcd) {
    long result = 0;
    long multiplier = 1;

    while (bcd > 0) {
        int digit = bcd & 0xF;     // lowest nibble
        result += digit * multiplier;
        multiplier *= 10;
        bcd >>= 4;                 // shift to next nibble
    }

    return result;
}

int main(void) {
    uint32_t bcd = 0x0123;  // BCD = 123
    long decimal = bcd_to_decimal32(bcd);
    printf("BCD 0x%4X -> Decimal %ld\n", bcd, decimal);
    return 0;
}
