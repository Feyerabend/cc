
![Simple Errors](./../../../assets/image/errors/simple.png)

## Error Handling in Embedded Systems: A Case Study

This project demonstrates comprehensive error handling patterns in embedded C programming,
using a display driver for the Raspberry Pi Pico as a practical example. The implementation
showcases professional-grade error management techniques that balance robustness with the
resource constraints of embedded systems.


### Error Handling Architecture


#### Multi-Layer Error System

The error handling is built on three complementary layers:

1. *Error Codes* - Enumerated error types providing standardized return values
2. *Error Context* - Detailed diagnostic information captured at the error site
3. *Error Strings* - Human-readable descriptions for debugging and logging

This layered approach allows the system to provide both machine-readable error codes for
programmatic handling and human-readable context for debugging, without sacrificing performance
in production.


#### Error Code Design

The error enumeration defines 16 distinct error conditions, each representing a specific failure mode:

- *Initialization errors* - Already initialized, not initialized, hardware failures
- *Resource errors* - DMA unavailable, configuration failed, null pointers
- *Operational errors* - Invalid coordinates, timeouts, command failures
- *State errors* - Operations attempted in invalid states

Each error code is semantically meaningful, allowing calling code to make intelligent decisions about
recovery strategies. For example, a "not initialized" error might trigger initialisation, while a
"DMA timeout" might fall back to blocking transfers.


### Error Context Capture

#### The DISP_ERROR Macro

The macro pattern captures rich diagnostic information at the error site without cluttering the code:

```c
#define DISP_ERROR(code, msg) \
    (disp_set_error_context((code), __func__, __LINE__, (msg)), (code))
```

This macro:
- Returns the error code for immediate checking
- Captures the function name automatically
- Records the exact line number
- Stores a descriptive message
- Requires minimal typing at error sites


#### Context Structure

The error context structure stores:
- *Error code* - What went wrong
- *Function name* - Where it happened
- *Line number* - Exact location in source
- *Message* - Additional details or hints

This information is invaluable during development and debugging, especially in
embedded systems where traditional debugging tools may be limited.


### Error Propagation Patterns

#### Immediate Return Pattern

Functions check for errors and propagate them immediately:

```c
if ((e = write_cmd(0x01)) != DISP_OK) return e;
```

This pattern:
- Keeps error handling concise
- Allows errors to bubble up the call stack
- Preserves error context from the original source
- Avoids nested error handling logic


#### Resource Cleanup on Error

Critical sections properly clean up on failure:

```c
if (initialization_step_fails) {
    cleanup_resources();
    return DISP_ERROR(code, "description");
}
```

This ensures that:
- Partial initialization doesn't leave the system in an inconsistent state
- Resources are properly released even during failure paths
- The next initialization attempt starts from a clean state


### Error Recovery Strategies

### Graceful Degradation

When DMA initialisation fails, the system falls back to blocking SPI transfers:

```c
if (dma_init() != DISP_OK) {
    printf("DEBUG: DMA init failed, continuing without DMA\n");
    g.config.use_dma = false;
}
```

This demonstrates an important embedded principle: *provide the best service
possible given available resources*. The display still functions, just with
lower performance.


#### Validation and Prevention

Input validation prevents errors before they occur:

```c
if (x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) 
    return DISP_ERROR(DISP_ERR_INVALID_COORDS, "bad pos");
```

Early validation:
- Prevents undefined behavior
- Provides clear feedback about what's wrong
- Avoids cascading failures deeper in the system
- Makes debugging easier by catching issues at the boundary


#### Timeout Protection

Long-running operations include timeout checks to prevent hangs:

```c
while (g.dma_busy) {
    if (timeout_exceeded) {
        abort_operation();
        return DISP_ERROR(DISP_ERR_DMA_TIMEOUT, "timeout");
    }
}
```

This protects against:
- Hardware failures that never complete
- Infinite wait loops that freeze the system
- Deadlocks in concurrent operations


### Error Reporting and Debugging

#### Debug Output

Strategic printf statements provide visibility into the system state:

```c
printf("DEBUG: DMA channel %d initialized\n", g.dma_channel);
printf("DEBUG: LCD init sequence failed: %s\n", disp_error_string(e));
```

In embedded systems, serial logging is often the primary debugging tool. These messages:
- Confirm successful initialization steps
- Report failure conditions with context
- Provide performance metrics
- Help trace execution flow


#### Error String Conversion

The error-to-string lookup table enables readable error messages:

```c
const char* err_str[] = {
    "OK", "Already init", "Not init", "SPI fail", ...
};
```

This simple table:
- Translates error codes to descriptions
- Minimal memory overhead (array of pointers)
- O(1) lookup time
- Consistent error message format


#### Error Query API

Applications can inspect the last error for detailed diagnostics:

```c
disp_error_context_t ctx = disp_get_last_error();
printf("Error in %s at line %d: %s\n", 
       ctx.function, ctx.line, ctx.message);
```

This allows higher-level code to:
- Log detailed error information
- Display errors to users
- Make informed recovery decisions
- Track error patterns over time


### State Machine Error Handling

#### State Validation

Many operations check initialisation state:

```c
if (!g.initialized) 
    return DISP_ERROR(DISP_ERR_NOT_INIT, "not init");
```

This prevents:
- Operations on uninitialized hardware
- Null pointer dereferences
- Undefined hardware states
- Cascading failures


#### Idempotent Operations

Some operations check and prevent redundant calls:

```c
if (g.initialized) 
    return DISP_ERROR(DISP_ERR_ALREADY_INIT, "already init");
```

This pattern:
- Makes functions safe to call multiple times
- Prevents resource leaks from repeated initialization
- Provides clear feedback about state errors
- Simplifies application code


### Interrupt Safety

#### Volatile State Variables

Variables modified in interrupt handlers are marked volatile:

```c
volatile bool dma_busy;
volatile bool btn_debounced[BUTTON_COUNT];
```

This ensures:
- Compiler doesn't optimize away state checks
- Main loop sees interrupt-driven state changes
- No race conditions from compiler reordering
- Correct behavior even with optimization enabled


#### Atomic Operations

DMA completion uses hardware interrupt flags for atomic state changes,
preventing race conditions between interrupt context and main code.


### Memory Safety

#### Null Pointer Checks

All functions taking pointers validate them:

```c
if (!data || len == 0) 
    return DISP_ERROR(DISP_ERR_NULL_POINTER, "bad data");
```


#### Bounds Checking

Array operations validate indices:

```c
if (b >= BUTTON_COUNT) 
    return DISP_ERROR(DISP_ERR_INVALID_DIMENSIONS, "invalid button");
```


#### Memory Allocation Failure Handling

Dynamic allocations check for failure:

```c
g.framebuffer = malloc(size);
if (!g.framebuffer) {
    return DISP_ERROR(DISP_ERR_NULL_POINTER, "framebuffer alloc failed");
}
```


### Key Takeaways

This error handling system demonstrates several important embedded programming principles:

1. *Errors are values* - Return codes allow systematic error checking
2. *Context matters* - Capture location and description at error sites
3. *Fail gracefully* - Degrade functionality rather than crash
4. *Validate early* - Check inputs at function boundaries
5. *Protect critical sections* - Use timeouts and guards
6. *Make debugging easy* - Provide visibility through logging
7. *Clean up properly* - Release resources on all error paths
8. *State consistency* - Prevent operations in invalid states

The implementation shows that robust error handling doesn't require exceptions or complex
frameworks--just careful design, consistent patterns, and attention to failure modes.
This approach works well in resource-constrained embedded systems where reliability is critical.


### Summary

This error handling system is demonstrated in a complete ST7789 display driver for the
Raspberry Pi Pico (320x240 LCD), including:

- Hardware initialization with proper error propagation
- DMA-accelerated graphics with timeout protection
- Button input with debouncing and state management
- Framebuffer support with allocation failure handling
- Comprehensive test suite exercising all error paths

The driver provides both direct rendering and framebuffer modes, with DMA support for
high-performance graphics--all while maintaining robust error handling throughout.

