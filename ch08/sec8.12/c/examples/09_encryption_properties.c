#include "../src/core/property_test.h"
#include "../src/strategies/string_strategy.h"
#include "../src/strategies/integer_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* caesar_encrypt(const char* plaintext, int shift) {
    int text_len = strlen(plaintext);
    char* ciphertext = (char*)malloc(text_len + 1);
    
    for (int i = 0; i < text_len; i++) {
        unsigned char ch = (unsigned char)plaintext[i];
        ciphertext[i] = (char)((ch + shift) % 256);
        if (ciphertext[i] == '\0') {
            ciphertext[i] = 1;
        }
    }
    ciphertext[text_len] = '\0';
    
    return ciphertext;
}

char* caesar_decrypt(const char* ciphertext, int shift) {
    int text_len = strlen(ciphertext);
    char* plaintext = (char*)malloc(text_len + 1);
    
    for (int i = 0; i < text_len; i++) {
        unsigned char ch = (unsigned char)ciphertext[i];
        int original = (ch - shift + 256) % 256;
        
        if (ch == 1 && (original % 256) == 0) {
            plaintext[i] = '\0';
        } else {
            plaintext[i] = (char)original;
        }
    }
    plaintext[text_len] = '\0';
    
    return plaintext;
}

void test_encryption_roundtrip(void* input) {
    String* plaintext = (String*)input;
    int shift = 13;
    
    char* ciphertext = caesar_encrypt(plaintext->data, shift);
    char* decrypted = caesar_decrypt(ciphertext, shift);
    
    PROPERTY_ASSERT(strcmp(decrypted, plaintext->data) == 0);
    
    free(ciphertext);
    free(decrypted);
}

void test_encryption_changes_data(void* input) {
    String* plaintext = (String*)input;
    int shift = 7;
    
    if (strlen(plaintext->data) == 0) {
        return;
    }
    
    char* ciphertext = caesar_encrypt(plaintext->data, shift);
    
    int differs = strcmp(ciphertext, plaintext->data) != 0;
    
    PROPERTY_ASSERT(differs);
    
    free(ciphertext);
}

void test_encryption_same_length(void* input) {
    String* plaintext = (String*)input;
    int shift = 5;
    
    char* ciphertext = caesar_encrypt(plaintext->data, shift);
    
    PROPERTY_ASSERT(strlen(ciphertext) == strlen(plaintext->data));
    
    free(ciphertext);
}

void test_encryption_different_keys(void* input) {
    String* plaintext = (String*)input;
    int shift1 = 3;
    int shift2 = 7;
    
    if (strlen(plaintext->data) == 0) {
        return;
    }
    
    char* cipher1 = caesar_encrypt(plaintext->data, shift1);
    char* cipher2 = caesar_encrypt(plaintext->data, shift2);
    
    PROPERTY_ASSERT(strcmp(cipher1, cipher2) != 0);
    
    free(cipher1);
    free(cipher2);
}

void test_double_encryption_identity(void* input) {
    String* plaintext = (String*)input;
    int shift = 10;
    
    char* encrypted_once = caesar_encrypt(plaintext->data, shift);
    char* decrypted = caesar_decrypt(encrypted_once, shift);
    
    PROPERTY_ASSERT(strcmp(decrypted, plaintext->data) == 0);
    
    free(encrypted_once);
    free(decrypted);
}

void run_property_test(
    const char* name,
    PropertyFn property,
    Strategy* strategy,
    int max_examples
) {
    printf("Running: %s\n", name);
    
    TestResult* result = test_property(
        property,
        strategy,
        max_examples,
        (unsigned int)time(NULL)
    );
    
    if (result->passed) {
        printf("  ✓ PASSED (%d examples in %.3fs)\n",
               result->examples_tried,
               result->execution_time);
    } else {
        printf("  ✗ FAILED after %d examples\n", result->examples_tried);
        printf("    Shrink iterations: %d\n", result->shrink_iterations);
    }
    
    test_result_free(result);
    printf("\n");
}

int main(void) {
    printf("Property-Based Testing - Encryption\n");
    printf("===================================\n\n");
    
    printf("Testing Caesar Cipher Properties:\n");
    printf("----------------------------------\n");
    
    Strategy* string_strategy = string_strategy_create(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*() ",
        100
    );
    
    run_property_test(
        "Encrypt/decrypt round-trip preserves plaintext",
        test_encryption_roundtrip,
        string_strategy,
        100
    );
    
    run_property_test(
        "Encryption changes the data (ciphertext != plaintext)",
        test_encryption_changes_data,
        string_strategy,
        100
    );
    
    run_property_test(
        "Encryption preserves length",
        test_encryption_same_length,
        string_strategy,
        100
    );
    
    run_property_test(
        "Different keys produce different ciphertexts",
        test_encryption_different_keys,
        string_strategy,
        100
    );
    
    run_property_test(
        "Encrypt/decrypt round-trip (Caesar cipher)",
        test_double_encryption_identity,
        string_strategy,
        100
    );
    
    strategy_free(string_strategy);
    
    printf("All tests completed.\n");
    printf("\nNote: Cryptographic properties tested:\n");
    printf("  - Round-trip: decrypt(encrypt(x)) == x\n");
    printf("  - Obfuscation: ciphertext != plaintext\n");
    printf("  - Length preservation\n");
    printf("  - Shift sensitivity (different shifts → different outputs)\n");
    printf("\nThis demonstrates real-world encryption testing.\n");
    
    return 0;
}
