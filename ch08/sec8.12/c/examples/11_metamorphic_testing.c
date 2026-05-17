#include "../src/core/property_test.h"
#include "../src/strategies/string_strategy.h"
#include "../src/strategies/integer_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char* data;
    int length;
} CompressedData;

CompressedData* rle_compress(const char* input) {
    int input_len = strlen(input);
    if (input_len == 0) {
        CompressedData* result = (CompressedData*)malloc(sizeof(CompressedData));
        result->data = (char*)malloc(1);
        result->data[0] = '\0';
        result->length = 0;
        return result;
    }
    
    char* compressed = (char*)malloc(input_len * 3);
    int pos = 0;
    
    int i = 0;
    while (i < input_len) {
        char current = input[i];
        int count = 1;
        
        while (i + count < input_len && input[i + count] == current && count < 99) {
            count++;
        }
        
        if (count > 2) {
            pos += sprintf(compressed + pos, "%d%c", count, current);
        } else {
            for (int j = 0; j < count; j++) {
                compressed[pos++] = current;
            }
        }
        
        i += count;
    }
    
    compressed[pos] = '\0';
    
    CompressedData* result = (CompressedData*)malloc(sizeof(CompressedData));
    result->data = (char*)malloc(pos + 1);
    strcpy(result->data, compressed);
    result->length = pos;
    
    free(compressed);
    return result;
}

char* rle_decompress(CompressedData* compressed) {
    char* result = (char*)malloc(10000);
    int pos = 0;
    
    int i = 0;
    while (i < compressed->length) {
        if (compressed->data[i] >= '0' && compressed->data[i] <= '9') {
            int count = 0;
            while (i < compressed->length && 
                   compressed->data[i] >= '0' && 
                   compressed->data[i] <= '9') {
                count = count * 10 + (compressed->data[i] - '0');
                i++;
            }
            
            if (i < compressed->length) {
                char ch = compressed->data[i];
                for (int j = 0; j < count; j++) {
                    result[pos++] = ch;
                }
                i++;
            }
        } else {
            result[pos++] = compressed->data[i];
            i++;
        }
    }
    
    result[pos] = '\0';
    return result;
}

void compressed_data_free(CompressedData* data) {
    if (data) {
        free(data->data);
        free(data);
    }
}

void test_compression_roundtrip(void* input) {
    String* original = (String*)input;
    
    CompressedData* compressed = rle_compress(original->data);
    char* decompressed = rle_decompress(compressed);
    
    PROPERTY_ASSERT(strcmp(decompressed, original->data) == 0);
    
    free(decompressed);
    compressed_data_free(compressed);
}

void test_double_compression_idempotent(void* input) {
    String* original = (String*)input;
    
    CompressedData* compressed1 = rle_compress(original->data);
    char* temp = rle_decompress(compressed1);
    CompressedData* compressed2 = rle_compress(temp);
    
    PROPERTY_ASSERT(compressed1->length == compressed2->length);
    PROPERTY_ASSERT(strcmp(compressed1->data, compressed2->data) == 0);
    
    free(temp);
    compressed_data_free(compressed1);
    compressed_data_free(compressed2);
}

void test_compression_reduces_repeated_chars(void* input) {
    String* original = (String*)input;
    
    int consecutive_count = 0;
    for (int i = 0; i < (int)strlen(original->data) - 1; i++) {
        if (original->data[i] == original->data[i + 1]) {
            consecutive_count++;
        }
    }
    
    if (consecutive_count < 3) {
        return;
    }
    
    CompressedData* compressed = rle_compress(original->data);
    
    PROPERTY_ASSERT(compressed->length <= (int)strlen(original->data));
    
    compressed_data_free(compressed);
}

void test_concat_compress_vs_compress_concat(void* input) {
    String* str = (String*)input;
    
    char* concatenated = (char*)malloc(strlen(str->data) * 2 + 1);
    strcpy(concatenated, str->data);
    strcat(concatenated, str->data);
    
    CompressedData* compress_then_concat = rle_compress(concatenated);
    
    CompressedData* part1 = rle_compress(str->data);
    CompressedData* part2 = rle_compress(str->data);
    
    char* concat_compressed = (char*)malloc(
        strlen(part1->data) + strlen(part2->data) + 1
    );
    strcpy(concat_compressed, part1->data);
    strcat(concat_compressed, part2->data);
    
    char* result1 = rle_decompress(compress_then_concat);
    
    CompressedData* temp_data = (CompressedData*)malloc(sizeof(CompressedData));
    temp_data->data = concat_compressed;
    temp_data->length = strlen(concat_compressed);
    char* result2 = rle_decompress(temp_data);
    
    PROPERTY_ASSERT(strcmp(result1, result2) == 0);
    
    free(concatenated);
    free(result1);
    free(result2);
    free(concat_compressed);
    free(temp_data);
    compressed_data_free(compress_then_concat);
    compressed_data_free(part1);
    compressed_data_free(part2);
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
    printf("Property-Based Testing - Metamorphic Properties\n");
    printf("===============================================\n\n");
    
    printf("Testing Run-Length Encoding (RLE) Compression:\n");
    printf("----------------------------------------------\n");
    
    Strategy* string_strategy = string_strategy_create("aabbbcccc", 50);
    
    run_property_test(
        "Compression round-trip: decompress(compress(x)) = x",
        test_compression_roundtrip,
        string_strategy,
        100
    );
    
    run_property_test(
        "Double compression is idempotent",
        test_double_compression_idempotent,
        string_strategy,
        100
    );
    
    run_property_test(
        "Compression reduces size for repeated characters",
        test_compression_reduces_repeated_chars,
        string_strategy,
        100
    );
    
    run_property_test(
        "Compress-concat metamorphic relationship",
        test_concat_compress_vs_compress_concat,
        string_strategy,
        100
    );
    
    strategy_free(string_strategy);
    
    printf("All tests completed.\n");
    printf("\nMetamorphic Testing Pattern:\n");
    printf("  Instead of checking 'correct output', we test:\n");
    printf("  - Relationships between operations\n");
    printf("  - Invariants that hold regardless of input\n");
    printf("  - Properties that don't require oracle\n");
    printf("\nExamples:\n");
    printf("  - compress(compress(x)) behaves like compress(x)\n");
    printf("  - compress(a+b) relates to compress(a)+compress(b)\n");
    printf("  - Useful when 'correct answer' is hard to compute!\n");
    
    return 0;
}
