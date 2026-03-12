
*EXPAND ON LATER*

## What are Effect Systems?

Effect systems are type system extensions that track *side effects* in code.
They answer the question: "What can this function do besides return a value?"

Common effects include:
- *IO*: Reading/writing files, network calls
- *State*: Mutable state access
- *Exceptions*: Can throw errors
- *Async*: Non-blocking operations
- *Random*: Non-deterministic behavior

The idea is that functions are annotated with their effects,
letting you statically verify that effectful operations are handled properly.

For example, in a hypothetical language:
```
fn pure_math(x: Int) -> Int { x * 2 }          // No effects
fn read_file(path: String) -> String with IO   // Has IO effect
fn parse(s: String) -> Int with Error          // Can fail
```



### C impl.

C doesn't have built-in effect tracking, but we can simulate it using:
1. *Tagged unions* to represent effect types
2. *Handler functions* to interpret effects
3. *Continuation-passing style* for control flow

Here's a practical implementation:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// Effect types
typedef enum {
    EFFECT_RETURN,
    EFFECT_READ,
    EFFECT_WRITE,
    EFFECT_ERROR
} EffectType;

// Effect data structure
typedef struct Effect {
    EffectType type;
    union {
        struct {
            char* prompt;
            char* buffer;
            size_t buffer_size;
        } read;
        struct {
            char* message;
        } write;
        struct {
            char* message;
        } error;
        struct {
            void* value;
        } return_value;
    } data;
} Effect;

// Continuation type: function that resumes computation
typedef Effect (*Continuation)(void* result, void* context);

// Effect handlers
typedef struct {
    Effect (*handle_read)(char* prompt, Continuation k, void* ctx);
    Effect (*handle_write)(char* message, Continuation k, void* ctx);
    Effect (*handle_error)(char* message, Continuation k, void* ctx);
} EffectHandlers;

// Helper to create effects
Effect make_return(void* value) {
    Effect e;
    e.type = EFFECT_RETURN;
    e.data.return_value.value = value;
    return e;
}

Effect make_read(char* prompt, char* buffer, size_t size) {
    Effect e;
    e.type = EFFECT_READ;
    e.data.read.prompt = prompt;
    e.data.read.buffer = buffer;
    e.data.read.buffer_size = size;
    return e;
}

Effect make_write(char* message) {
    Effect e;
    e.type = EFFECT_WRITE;
    e.data.write.message = message;
    return e;
}

Effect make_error(char* message) {
    Effect e;
    e.type = EFFECT_ERROR;
    e.data.error.message = message;
    return e;
}

// Example: A computation that performs effects
typedef struct {
    int step;
    char name_buffer[100];
    int age;
} GreetContext;

Effect greet_continuation(void* result, void* context) {
    GreetContext* ctx = (GreetContext*)context;
    
    switch(ctx->step) {
        case 0: // After reading name
            strcpy(ctx->name_buffer, (char*)result);
            ctx->step = 1;
            return make_write("How old are you?");
            
        case 1: // After writing age prompt
            ctx->step = 2;
            return make_read("Age: ", ctx->name_buffer, sizeof(ctx->name_buffer));
            
        case 2: // After reading age
            ctx->age = atoi((char*)result);
            if (ctx->age < 0 || ctx->age > 150) {
                return make_error("Invalid age!");
            }
            ctx->step = 3;
            
            char greeting[200];
            snprintf(greeting, sizeof(greeting), 
                    "Hello %s! You are %d years old.", 
                    ctx->name_buffer, ctx->age);
            return make_write(greeting);
            
        case 3: // After final write
            return make_return("Done");
            
        default:
            return make_error("Invalid state");
    }
}

Effect start_greet_program(void* _) {
    return make_write("What's your name?");
}

// Effect interpreter with handlers
void* run_with_handlers(Effect initial, EffectHandlers* handlers, void* context) {
    Effect current = initial;
    
    while (current.type != EFFECT_RETURN) {
        switch(current.type) {
            case EFFECT_READ: {
                char buffer[256];
                printf("%s", current.data.read.prompt);
                fgets(buffer, sizeof(buffer), stdin);
                buffer[strcspn(buffer, "\n")] = 0; // Remove newline
                
                current = greet_continuation(buffer, context);
                break;
            }
            
            case EFFECT_WRITE:
                printf("%s\n", current.data.write.message);
                current = greet_continuation(NULL, context);
                break;
                
            case EFFECT_ERROR:
                fprintf(stderr, "Error: %s\n", current.data.error.message);
                return NULL;
                
            default:
                fprintf(stderr, "Unknown effect type\n");
                return NULL;
        }
    }
    
    return current.data.return_value.value;
}

int main() {
    GreetContext ctx = {0};
    EffectHandlers handlers = {0}; // Not used in this simple version
    
    Effect initial = start_greet_program(NULL);
    void* result = run_with_handlers(initial, &handlers, &ctx);
    
    printf("\nProgram completed: %s\n", result ? (char*)result : "Failed");
    
    return 0;
}
```

*Key concepts here:*

1. *Effects as data*: Instead of performing side effects directly,
   functions return `Effect` structures describing what they want to do

2. *Handlers interpret effects*: The `run_with_handlers` function decides
   how to actually perform each effect (could swap stdio with network, mock testing, etc.)

3. *Continuations*: The `greet_continuation` function represents
   "what to do next" after an effect completes

4. *Separation of description and execution*: The business logic (greeting user)
   is separated from IO implementation

This is a simplified algebraic effect system. Real systems provide better syntax
and type safety, but the core idea is: *effects are values that get interpreted by handlers*.

