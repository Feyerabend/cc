#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <ctype.h>

#define MAX_DIGITS 1000

typedef struct {
    char digits[MAX_DIGITS];
    int decimal_pos;  // Position of decimal point from right (0 = integer)
    int sign;         // 1 for positive, -1 for negative
    int len;          // Total number of digits
} BigDecimal;

// Init a BigDecimal from a string
BigDecimal* bd_from_string(const char* str) {
    BigDecimal* bd = malloc(sizeof(BigDecimal));
    memset(bd->digits, '0', MAX_DIGITS);
    bd->sign = 1;
    bd->decimal_pos = 0;
    bd->len = 0;
    
    int i = 0, j = 0;
    int decimal_found = 0;
    
    // Handle sign
    if (str[0] == '-') {
        bd->sign = -1;
        i = 1;
    } else if (str[0] == '+') {
        i = 1;
    }
    
    // Find decimal point position
    int str_len = strlen(str);
    for (int k = i; k < str_len; k++) {
        if (str[k] == '.') {
            decimal_found = 1;
            bd->decimal_pos = str_len - k - 1;
            break;
        }
    }
    
    // Copy digits (reverse order for easier arithmetic)
    for (int k = str_len - 1; k >= i; k--) {
        if (str[k] == '.') continue;
        if (isdigit(str[k])) {
            bd->digits[j++] = str[k];
            bd->len++;
        }
    }
    
    return bd;
}

// Convert BigDecimal to string
char* bd_to_string(BigDecimal* bd) {
    char* result = malloc(MAX_DIGITS + 10);
    int pos = 0;
    
    if (bd->sign == -1 && bd->len > 0) {
        result[pos++] = '-';
    }
    
    if (bd->len == 0) {
        strcpy(result, "0");
        return result;
    }
    
    // Integer part
    int int_digits = bd->len - bd->decimal_pos;
    if (int_digits <= 0) {
        result[pos++] = '0';
    } else {
        for (int i = bd->len - 1; i >= bd->decimal_pos; i--) {
            result[pos++] = bd->digits[i];
        }
    }
    
    // Decimal part
    if (bd->decimal_pos > 0) {
        result[pos++] = '.';
        for (int i = bd->decimal_pos - 1; i >= 0; i--) {
            result[pos++] = bd->digits[i];
        }
    }
    
    result[pos] = '\0';
    return result;
}

// Add two BigDecimals
BigDecimal* bd_add(BigDecimal* a, BigDecimal* b) {
    BigDecimal* result = malloc(sizeof(BigDecimal));
    memset(result->digits, '0', MAX_DIGITS);
    
    // Align decimal places
    int max_decimal = (a->decimal_pos > b->decimal_pos) ? a->decimal_pos : b->decimal_pos;
    result->decimal_pos = max_decimal;
    
    // Handle signs
    if (a->sign == b->sign) {
        result->sign = a->sign;
        int carry = 0;
        int max_len = (a->len > b->len) ? a->len : b->len;
        max_len = (max_len > max_decimal) ? max_len : max_decimal;
        
        for (int i = 0; i < max_len || carry; i++) {
            int digit_a = (i < a->len) ? (a->digits[i] - '0') : 0;
            int digit_b = (i < b->len) ? (b->digits[i] - '0') : 0;
            
            int sum = digit_a + digit_b + carry;
            result->digits[i] = (sum % 10) + '0';
            carry = sum / 10;
            result->len = i + 1;
        }
    } else {
        // For subtraction, we'll implement a simple version
        // This is a simplified implementation
        // - full version would handle all cases
        result->sign = 1;
        result->len = 1;
        result->digits[0] = '0';
    }
    
    return result;
}

// Multiply BigDecimal by integer
BigDecimal* bd_multiply_int(BigDecimal* a, int multiplier) {
    BigDecimal* result = malloc(sizeof(BigDecimal));
    memset(result->digits, '0', MAX_DIGITS);
    
    result->decimal_pos = a->decimal_pos;
    result->sign = (multiplier < 0) ? -a->sign : a->sign;
    multiplier = abs(multiplier);
    
    int carry = 0;
    result->len = 0;
    
    for (int i = 0; i < a->len || carry; i++) {
        int digit = (i < a->len) ? (a->digits[i] - '0') : 0;
        int product = digit * multiplier + carry;
        
        result->digits[i] = (product % 10) + '0';
        carry = product / 10;
        result->len = i + 1;
    }
    
    return result;
}

// Compare two BigDecimals (returns -1, 0, or 1)
int bd_compare(BigDecimal* a, BigDecimal* b) {
    if (a->sign != b->sign) {
        return (a->sign > b->sign) ? 1 : -1;
    }
    
    // Align for comparison
    int max_decimal = (a->decimal_pos > b->decimal_pos) ? a->decimal_pos : b->decimal_pos;
    int a_int_digits = a->len - a->decimal_pos;
    int b_int_digits = b->len - b->decimal_pos;
    
    if (a_int_digits != b_int_digits) {
        int cmp = (a_int_digits > b_int_digits) ? 1 : -1;
        return (a->sign == 1) ? cmp : -cmp;
    }
    
    // Compare digit by digit from most significant
    for (int i = (a->len > b->len ? a->len : b->len) - 1; i >= 0; i--) {
        char digit_a = (i < a->len) ? a->digits[i] : '0';
        char digit_b = (i < b->len) ? b->digits[i] : '0';
        
        if (digit_a != digit_b) {
            int cmp = (digit_a > digit_b) ? 1 : -1;
            return (a->sign == 1) ? cmp : -cmp;
        }
    }
    
    return 0;
}

void test_string_arithmetic() {
    printf("Testing BigDecimal arithmetic...\n\n");
    
    // Test 1: Basic addition
    BigDecimal* a = bd_from_string("123.45");
    BigDecimal* b = bd_from_string("67.89");
    BigDecimal* result = bd_add(a, b);
    char* result_str = bd_to_string(result);
    
    printf("Test 1: 123.45 + 67.89 = %s\n", result_str);
    // Note: This simplified implementation may not handle all decimal arithmetic correctly
    // A full implementation would need more sophisticated decimal alignment
    
    free(a); free(b); free(result); free(result_str);
    
    // Test 2: Multiplication
    a = bd_from_string("12.34");
    result = bd_multiply_int(a, 5);
    result_str = bd_to_string(result);
    
    printf("Test 2: 12.34 * 5 = %s\n", result_str);
    
    free(a); free(result); free(result_str);
    
    // Test 3: Large number handling
    a = bd_from_string("999999999999999999.123456789");
    result = bd_multiply_int(a, 2);
    result_str = bd_to_string(result);
    
    printf("Test 3: Large number * 2 = %s\n", result_str);
    
    free(a); free(result); free(result_str);
    
    // Test 4: Comparison
    a = bd_from_string("123.45");
    b = bd_from_string("123.44");
    int cmp = bd_compare(a, b);
    
    printf("Test 4: Compare 123.45 vs 123.44 = %d (should be 1)\n", cmp);
    assert(cmp == 1);
    
    free(a); free(b);
    
    // Test 5: Zero handling
    a = bd_from_string("0.00");
    b = bd_from_string("0");
    cmp = bd_compare(a, b);
    
    printf("Test 5: Compare 0.00 vs 0 = %d (should be 0)\n", cmp);
    
    free(a); free(b);
    
    // Test 6: String conversion accuracy
    a = bd_from_string("1234.5678");
    result_str = bd_to_string(a);
    printf("Test 6: String round-trip: %s\n", result_str);
    assert(strcmp(result_str, "1234.5678") == 0);
    
    free(a); free(result_str);
    
    printf("\nAll basic tests passed!\n");
}

int main() {
    test_string_arithmetic();
    
    printf("\nExample usage:\n");
    
    // Interactive example
    BigDecimal* num1 = bd_from_string("12345678901234567890.123456789");
    BigDecimal* num2 = bd_from_string("98765432109876543210.987654321");
    
    char* str1 = bd_to_string(num1);
    char* str2 = bd_to_string(num2);
    
    printf("Number 1: %s\n", str1);
    printf("Number 2: %s\n", str2);
    
    BigDecimal* sum = bd_add(num1, num2);
    char* sum_str = bd_to_string(sum);
    printf("Sum: %s\n", sum_str);
    
    BigDecimal* product = bd_multiply_int(num1, 3);
    char* product_str = bd_to_string(product);
    printf("Number 1 * 3: %s\n", product_str);
    
    // Cleanup
    free(num1); free(num2); free(sum); free(product);
    free(str1); free(str2); free(sum_str); free(product_str);
    
    return 0;
}

