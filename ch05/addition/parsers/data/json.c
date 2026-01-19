#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

typedef enum {
    JSON_NULL,
    JSON_BOOL,
    JSON_NUMBER,
    JSON_STRING,
    JSON_ARRAY,
    JSON_OBJECT
} JsonType;

typedef struct JsonValue JsonValue;

typedef struct {
    char *key;
    JsonValue *value;
} JsonKeyValue;

struct JsonValue {
    JsonType type;
    union {
        int bool_value;
        double num_value;
        char *str_value;
        struct {
            JsonValue **items;
            size_t length;
        } array_value;
        struct {
            JsonKeyValue *pairs;
            size_t length;
        } object_value;
    };
};

// fwd. decl.
JsonValue* json_parse(const char **json);
void json_free(JsonValue *json);
void print_json(const JsonValue *json, int indent);
void skip_whitespace(const char **json);
int expect_char(const char **json, char c);
char* json_strdup(const char *str, size_t len);

// util
void skip_whitespace(const char **json) {
    while (isspace(**json)) (*json)++;
}

int expect_char(const char **json, char c) {
    skip_whitespace(json);
    if (**json != c) return 0;
    (*json)++;
    return 1;
}

char* json_strdup(const char *str, size_t len) {
    char *copy = malloc(len + 1);
    strncpy(copy, str, len);
    copy[len] = '\0';
    return copy;
}

// fwd. decl. parse JSON values
JsonValue* json_parse_value(const char **json);
JsonValue* json_parse_object(const char **json);
JsonValue* json_parse_array(const char **json);
JsonValue* json_parse_string(const char **json);
JsonValue* json_parse_number(const char **json);
JsonValue* json_parse_true(const char **json);
JsonValue* json_parse_false(const char **json);
JsonValue* json_parse_null(const char **json);

// JSON parsing
JsonValue* json_parse(const char **json) {
    skip_whitespace(json);
    return json_parse_value(json);
}

JsonValue* json_parse_value(const char **json) {
    if (expect_char(json, '{')) {
        return json_parse_object(json);
    } else if (expect_char(json, '[')) {
        return json_parse_array(json);
    } else if (**json == '\"') {
        return json_parse_string(json);
    } else if (isdigit(**json) || **json == '-') {
        return json_parse_number(json);
    } else if (strncmp(*json, "true", 4) == 0) {
        return json_parse_true(json);
    } else if (strncmp(*json, "false", 5) == 0) {
        return json_parse_false(json);
    } else if (strncmp(*json, "null", 4) == 0) {
        return json_parse_null(json);
    }
    return NULL; // Error: unrecognized value
}

JsonValue* json_parse_object(const char **json) {
    JsonValue *object = malloc(sizeof(JsonValue));
    object->type = JSON_OBJECT;
    object->object_value.length = 0;
    object->object_value.pairs = NULL;

    while (1) {
        skip_whitespace(json);
        if (expect_char(json, '}')) break;

        JsonKeyValue pair;
        pair.key = json_parse_string(json)->str_value;
        
        skip_whitespace(json);
        if (!expect_char(json, ':')) return NULL;

        pair.value = json_parse_value(json);
        
        // add pair to object
        object->object_value.pairs = realloc(object->object_value.pairs, sizeof(JsonKeyValue) * (object->object_value.length + 1));
        object->object_value.pairs[object->object_value.length++] = pair;

        skip_whitespace(json);
        if (!expect_char(json, ',')) break;
    }
    return object;
}

JsonValue* json_parse_array(const char **json) {
    JsonValue *array = malloc(sizeof(JsonValue));
    array->type = JSON_ARRAY;
    array->array_value.length = 0;
    array->array_value.items = NULL;

    while (1) {
        skip_whitespace(json);
        if (expect_char(json, ']')) break;

        JsonValue *value = json_parse_value(json);
        array->array_value.items = realloc(array->array_value.items, sizeof(JsonValue*) * (array->array_value.length + 1));
        array->array_value.items[array->array_value.length++] = value;

        skip_whitespace(json);
        if (!expect_char(json, ',')) break;
    }
    return array;
}

JsonValue* json_parse_string(const char **json) {
    const char *start = ++(*json);
    while (**json != '\"') {
        if (**json == '\\') (*json)++; // skip escaping
        (*json)++;
    }
    size_t len = *json - start;
    JsonValue *string_value = malloc(sizeof(JsonValue));
    string_value->type = JSON_STRING;
    string_value->str_value = json_strdup(start, len);
    (*json)++; // skip closing quote
    return string_value;
}

JsonValue* json_parse_number(const char **json) {
    const char *start = *json;
    while (isdigit(**json) || **json == '-' || **json == '.') (*json)++;
    size_t len = *json - start;

    JsonValue *num_value = malloc(sizeof(JsonValue));
    num_value->type = JSON_NUMBER;
    sscanf(start, "%lf", &num_value->num_value);
    return num_value;
}

JsonValue* json_parse_true(const char **json) {
    JsonValue *bool_value = malloc(sizeof(JsonValue));
    bool_value->type = JSON_BOOL;
    bool_value->bool_value = 1; // true
    *json += 4; // move past "true"
    return bool_value;
}

JsonValue* json_parse_false(const char **json) {
    JsonValue *bool_value = malloc(sizeof(JsonValue));
    bool_value->type = JSON_BOOL;
    bool_value->bool_value = 0; // false
    *json += 5; // move past "false"
    return bool_value;
}

JsonValue* json_parse_null(const char **json) {
    JsonValue *null_value = malloc(sizeof(JsonValue));
    null_value->type = JSON_NULL;
    *json += 4; // move past "null"
    return null_value;
}

// free memory for JSON objects
void json_free(JsonValue *json) {
    if (!json) return;

    switch (json->type) {
        case JSON_STRING:
            free(json->str_value);
            break;
        case JSON_ARRAY:
            for (size_t i = 0; i < json->array_value.length; i++) {
                json_free(json->array_value.items[i]);
            }
            free(json->array_value.items);
            break;
        case JSON_OBJECT:
            for (size_t i = 0; i < json->object_value.length; i++) {
                free(json->object_value.pairs[i].key);
                json_free(json->object_value.pairs[i].value);
            }
            free(json->object_value.pairs);
            break;
        default:
            break;
    }
    free(json);
}

// pretty-print
void print_json(const JsonValue *json, int indent) {
    switch (json->type) {
        case JSON_NULL:
            printf("null");
            break;
        case JSON_BOOL:
            printf(json->bool_value ? "true" : "false");
            break;
        case JSON_NUMBER:
            printf("%lf", json->num_value);
            break;
        case JSON_STRING:
            printf("\"%s\"", json->str_value);
            break;
        case JSON_ARRAY:
            printf("[\n");
            for (size_t i = 0; i < json->array_value.length; i++) {
                for (int j = 0; j < indent + 2; j++) printf(" ");
                print_json(json->array_value.items[i], indent + 2);
                if (i < json->array_value.length - 1) printf(",");
                printf("\n");
            }
            for (int j = 0; j < indent; j++) printf(" ");
            printf("]");
            break;
        case JSON_OBJECT:
            printf("{\n");
            for (size_t i = 0; i < json->object_value.length; i++) {
                for (int j = 0; j < indent + 2; j++) printf(" ");
                printf("\"%s\": ", json->object_value.pairs[i].key);
                print_json(json->object_value.pairs[i].value, indent + 2);
                if (i < json->object_value.length - 1) printf(",");
                printf("\n");
            }
            for (int j = 0; j < indent; j++) printf(" ");
            printf("}");
            break;
    }
}


int main() {
    const char *json_string = "{\"name\": \"John\", \"age\": 30, \"is_student\": false, \"subjects\": [\"math\", \"science\"]}";

    JsonValue *json = json_parse(&json_string);
    if (json) {
        print_json(json, 0);
        printf("\n");
        json_free(json);
    } else {
        printf("Failed to parse JSON.\n");
    }

    return 0;
}


