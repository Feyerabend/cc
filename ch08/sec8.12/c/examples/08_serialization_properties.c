#include "../src/core/property_test.h"
#include "../src/strategies/integer_strategy.h"
#include "../src/strategies/string_strategy.h"
#include "../src/strategies/tuple_strategy.h"
#include "../src/strategies/list_strategy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char* buffer;
    int capacity;
    int position;
} ByteBuffer;

ByteBuffer* byte_buffer_create(int capacity) {
    ByteBuffer* buf = (ByteBuffer*)malloc(sizeof(ByteBuffer));
    buf->buffer = (char*)malloc(capacity);
    buf->capacity = capacity;
    buf->position = 0;
    return buf;
}

void byte_buffer_free(ByteBuffer* buf) {
    if (buf) {
        free(buf->buffer);
        free(buf);
    }
}

void byte_buffer_write_int(ByteBuffer* buf, int value) {
    if (buf->position + 4 <= buf->capacity) {
        buf->buffer[buf->position++] = (value >> 24) & 0xFF;
        buf->buffer[buf->position++] = (value >> 16) & 0xFF;
        buf->buffer[buf->position++] = (value >> 8) & 0xFF;
        buf->buffer[buf->position++] = value & 0xFF;
    }
}

int byte_buffer_read_int(ByteBuffer* buf) {
    if (buf->position + 4 <= buf->capacity) {
        int value = 0;
        value |= ((unsigned char)buf->buffer[buf->position++]) << 24;
        value |= ((unsigned char)buf->buffer[buf->position++]) << 16;
        value |= ((unsigned char)buf->buffer[buf->position++]) << 8;
        value |= ((unsigned char)buf->buffer[buf->position++]);
        return value;
    }
    return 0;
}

void byte_buffer_write_string(ByteBuffer* buf, const char* str) {
    int len = strlen(str);
    byte_buffer_write_int(buf, len);
    
    if (buf->position + len <= buf->capacity) {
        memcpy(buf->buffer + buf->position, str, len);
        buf->position += len;
    }
}

char* byte_buffer_read_string(ByteBuffer* buf) {
    int len = byte_buffer_read_int(buf);
    
    if (len < 0 || len > 10000 || buf->position + len > buf->capacity) {
        char* empty = (char*)malloc(1);
        empty[0] = '\0';
        return empty;
    }
    
    char* str = (char*)malloc(len + 1);
    memcpy(str, buf->buffer + buf->position, len);
    str[len] = '\0';
    buf->position += len;
    
    return str;
}

void test_int_serialization_roundtrip(void* input) {
    int original = *(int*)input;
    
    ByteBuffer* buf = byte_buffer_create(1024);
    
    byte_buffer_write_int(buf, original);
    
    buf->position = 0;
    int decoded = byte_buffer_read_int(buf);
    
    PROPERTY_ASSERT(decoded == original);
    
    byte_buffer_free(buf);
}

void test_string_serialization_roundtrip(void* input) {
    String* original = (String*)input;
    
    ByteBuffer* buf = byte_buffer_create(10240);
    
    byte_buffer_write_string(buf, original->data);
    
    buf->position = 0;
    char* decoded = byte_buffer_read_string(buf);
    
    PROPERTY_ASSERT(strcmp(decoded, original->data) == 0);
    
    free(decoded);
    byte_buffer_free(buf);
}

void test_multiple_values_serialization(void* input) {
    Tuple2* tuple = (Tuple2*)input;
    int val1 = *(int*)tuple->first;
    int val2 = *(int*)tuple->second;
    
    ByteBuffer* buf = byte_buffer_create(1024);
    
    byte_buffer_write_int(buf, val1);
    byte_buffer_write_int(buf, val2);
    
    buf->position = 0;
    int decoded1 = byte_buffer_read_int(buf);
    int decoded2 = byte_buffer_read_int(buf);
    
    PROPERTY_ASSERT(decoded1 == val1);
    PROPERTY_ASSERT(decoded2 == val2);
    
    byte_buffer_free(buf);
}

void test_serialization_preserves_order(void* input) {
    IntList* list = (IntList*)input;
    
    ByteBuffer* buf = byte_buffer_create(list->length * 4 + 100);
    
    byte_buffer_write_int(buf, list->length);
    for (int i = 0; i < list->length; i++) {
        byte_buffer_write_int(buf, list->data[i]);
    }
    
    buf->position = 0;
    int decoded_length = byte_buffer_read_int(buf);
    
    PROPERTY_ASSERT(decoded_length == list->length);
    
    for (int i = 0; i < decoded_length; i++) {
        int decoded_value = byte_buffer_read_int(buf);
        PROPERTY_ASSERT(decoded_value == list->data[i]);
    }
    
    byte_buffer_free(buf);
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
    printf("Property-Based Testing - Serialization\n");
    printf("======================================\n\n");
    
    printf("Testing Binary Serialization Round-Trip:\n");
    printf("----------------------------------------\n");
    
    Strategy* int_strategy = integer_strategy_create(-10000, 10000);
    run_property_test(
        "Integer serialization round-trip",
        test_int_serialization_roundtrip,
        int_strategy,
        100
    );
    strategy_free(int_strategy);
    
    Strategy* string_strategy = string_strategy_create(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
        100
    );
    run_property_test(
        "String serialization round-trip",
        test_string_serialization_roundtrip,
        string_strategy,
        100
    );
    strategy_free(string_strategy);
    
    Strategy* int_strat = integer_strategy_create(-1000, 1000);
    Strategy* tuple_strategy = tuple2_strategy_create(int_strat, int_strat);
    run_property_test(
        "Multiple values serialization",
        test_multiple_values_serialization,
        tuple_strategy,
        100
    );
    strategy_free(tuple_strategy);
    
    Strategy* list_strategy = list_strategy_create(int_strat, 50);
    run_property_test(
        "List serialization preserves order",
        test_serialization_preserves_order,
        list_strategy,
        100
    );
    strategy_free(list_strategy);
    strategy_free(int_strat);
    
    printf("All tests completed.\n");
    printf("\nNote: Round-trip properties tested:\n");
    printf("  - encode(x) then decode() == x\n");
    printf("  - Preserves value equality\n");
    printf("  - Preserves ordering\n");
    printf("  - Works for multiple data types\n");
    printf("\nThis demonstrates real-world serialization testing.\n");
    
    return 0;
}
