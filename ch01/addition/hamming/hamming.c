#include <stdio.h>

// Encode 4-bit data into 7-bit Hamming(7,4) code
unsigned char hamming_encode_4bit(unsigned char data) {

    // Extract individual data bits
    unsigned char d1 = (data >> 3) & 1;
    unsigned char d2 = (data >> 2) & 1;
    unsigned char d3 = (data >> 1) & 1;
    unsigned char d4 = (data >> 0) & 1;

    // Calculate parity bits
    unsigned char p1 = d1 ^ d2 ^ d4;
    unsigned char p2 = d1 ^ d3 ^ d4;
    unsigned char p4 = d2 ^ d3 ^ d4;

    // Arrange bits: p1 p2 d1 p4 d2 d3 d4
    unsigned char code = 0;
    code |= (p1 << 6);
    code |= (p2 << 5);
    code |= (d1 << 4);
    code |= (p4 << 3);
    code |= (d2 << 2);
    code |= (d3 << 1);
    code |= (d4 << 0);

    return code;
}

// Decode 7-bit Hamming code, correct single-bit errors
unsigned char hamming_decode_7bit(unsigned char code, int *error_position) {
    // Extract bits
    unsigned char p1 = (code >> 6) & 1;
    unsigned char p2 = (code >> 5) & 1;
    unsigned char d1 = (code >> 4) & 1;
    unsigned char p4 = (code >> 3) & 1;
    unsigned char d2 = (code >> 2) & 1;
    unsigned char d3 = (code >> 1) & 1;
    unsigned char d4 = (code >> 0) & 1;

    // Recalculate parity bits
    unsigned char c1 = p1 ^ d1 ^ d2 ^ d4;
    unsigned char c2 = p2 ^ d1 ^ d3 ^ d4;
    unsigned char c4 = p4 ^ d2 ^ d3 ^ d4;

    // Syndrome (binary position of error)
    unsigned char syndrome = (c4 << 2) | (c2 << 1) | c1;
    *error_position = syndrome;

    // If syndrome is non-zero, correct the bit
    if (syndrome != 0 && syndrome <= 7) {
        code ^= (1 << (7 - syndrome)); // flip the erroneous bit
    }

    // Extract corrected data
    unsigned char corrected_d1 = (code >> 4) & 1;
    unsigned char corrected_d2 = (code >> 2) & 1;
    unsigned char corrected_d3 = (code >> 1) & 1;
    unsigned char corrected_d4 = (code >> 0) & 1;

    unsigned char decoded_data = (corrected_d1 << 3) |
                                 (corrected_d2 << 2) |
                                 (corrected_d3 << 1) |
                                 (corrected_d4 << 0);

    return decoded_data;
}

int main() {
    for (int i = 0; i < 16; ++i) {
        unsigned char encoded = hamming_encode_4bit(i);
        printf("Data: %01X => Encoded: %02X\n", i, encoded);

        // Test with a single-bit error (flip bit 3)
        unsigned char corrupted = encoded ^ (1 << 3);
        int error_pos;
        unsigned char decoded = hamming_decode_7bit(corrupted, &error_pos);
        printf("  Corrupted: %02X (bit %d flipped), Decoded: %01X\n", corrupted, error_pos, decoded);
    }
    return 0;
}

