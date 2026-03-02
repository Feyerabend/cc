
## Dispatch

Dispatch, at its core, is a mechanism for selecting and invoking a specific function
or behaviour based on some criteria, such as input values, types, patterns, or runtime
conditions. It is about routing a request to the appropriate handler, enabling flexibility
and modularity in code. Conceptually, dispatch is like a switchboard operator: given an
incoming call (input), it connects it to the correct line (function) according to
predefined rules or identifiers.

Dispatch is central to many programming paradigms:

* *Polymorphism* in object-oriented programming dispatches method calls based
  on object types.
* *Event handling* dispatches actions based on events.
* *Command processing* dispatches operations based on tokens or opcodes.
* *Embedded control systems* dispatch interrupts, sensor data, and state transitions.

The criteria for dispatch can vary widely--types, values, patterns, runtime metadata,
external configuration, or even probabilistic selection.

We first encounter simple dispatch in virtual machines or interpreters, typically
implemented using `if-elif-else` in Python or `switch-case` in C.



### Basic Dispatch Techniques

#### Python: Conditional Dispatch

```python
if opcode == "ADD":
    do_add()
elif opcode == "SUB":
    do_sub()
elif opcode == "MUL":
    do_mul()
else:
    unknown_opcode()
```

#### C: Switch-Based Dispatch

```c
switch (opcode) {
    case OP_ADD:
        do_add();
        break;
    case OP_SUB:
        do_sub();
        break;
    case OP_MUL:
        do_mul();
        break;
    default:
        unknown_opcode();
        break;
}
```

#### Python: Dictionary-Based Dispatch

```python
dispatch_table = {
    "ADD": do_add,
    "SUB": do_sub,
    "MUL": do_mul,
}

operation = dispatch_table.get(opcode, unknown_opcode)
operation()
```

#### C: Function Pointer Table

```c
typedef void (*operation_func)();

operation_func dispatch_table[] = {
    do_add,
    do_sub,
    do_mul
};

if (opcode >= 0 && opcode < sizeof(dispatch_table)/sizeof(dispatch_table[0])) {
    dispatch_table[opcode]();
} else {
    unknown_opcode();
}
```

These techniques provide constant-time lookup and scale better than large
conditional chains.



## Advanced Dispatch Flavours

The following sections describe less common but conceptually powerful
dispatch mechanisms. Each is illustrated both conceptually and with
embedded-system-oriented C examples, showing how these ideas translate
to constrained environments such as microcontroller-based sensor hubs.



### 1. Continuation-Passing Style (CPS) Dispatch

#### Concept

Instead of directly invoking a function, CPS dispatch passes control
to a [continuation](./../continue/)--a function representing
"what happens next." This makes control flow explicit and enables
asynchronous, non-blocking execution.

#### Embedded Context

In embedded systems:
* Interrupt service routines must be short.
* Blocking is unacceptable in hard real-time systems.
* Processing is often deferred to later stages.

CPS allows the ISR to dispatch quickly and defer work safely.

#### C Example (Sensor Hub)

```c
#include <stdint.h>
#include <stdio.h>

typedef struct {
    uint8_t sensor_id;
    int16_t value;
} SensorData;

typedef void (*Continuation)(int16_t);

void process_temperature(SensorData data, Continuation cont) {
    int16_t calibrated = data.value * 10;
    cont(calibrated);
}

void log_to_uart(int16_t value) {
    printf("Temperature: %d C\n", value);
}

void send_to_host(int16_t value) {
    printf("Sent to host: %d\n", value);
}

void dispatch_sensor(SensorData data, Continuation cont) {
    if (data.sensor_id == 1) {
        process_temperature(data, cont);
    } else {
        cont(-1);
    }
}
```

#### Characteristics

* Explicit control flow
* Ideal for asynchronous systems
* Common in event loops and embedded schedulers
* Requires careful stack discipline



### 2. Rule-Based Dispatch (Expert System Style)

#### Concept

Dispatch is driven by declarative rules consisting of:
* A condition
* An action

Rules are evaluated sequentially until a match is found.

#### Embedded Context

Useful for:
* Configurable firmware behaviour
* Safety thresholds
* Field-upgradable rule sets
* Decision engines in constrained devices

#### C Example (Pressure Monitoring)

```c
typedef struct {
    uint8_t sensor_id;
    int16_t value;
} SensorData;

typedef struct {
    uint8_t (*condition)(SensorData);
    void (*action)(SensorData);
} Rule;

uint8_t is_high_pressure(SensorData data) {
    return data.value > 1000;
}

void alert_high_pressure(SensorData data) {
    printf("ALERT: High pressure %d hPa\n", data.value);
}

Rule rules[] = {
    {is_high_pressure, alert_high_pressure},
    {NULL, NULL}
};

void dispatch_by_rules(SensorData data) {
    for (int i = 0; rules[i].condition != NULL; i++) {
        if (rules[i].condition(data)) {
            rules[i].action(data);
            return;
        }
    }
}
```

#### Characteristics

* Declarative logic
* Highly extensible
* Slightly higher runtime cost
* Requires conflict resolution strategy



### 3. Aspect-Oriented Dispatch

#### Concept

Dispatch is augmented with cross-cutting concerns such as:
* Logging
* Validation
* Power monitoring
* Error tracking

Instead of choosing a single handler, it composes behaviour around
a core function.

#### Embedded Context

Embedded systems benefit from:

* Centralised logging
* Power-aware instrumentation
* Validation hooks
* Fault detection layers

#### C Example (Motion Sensor with Aspects)

```c
typedef struct {
    uint8_t sensor_id;
    int16_t value;
} SensorData;

typedef struct {
    SensorData data;
    uint8_t power_level;
} Context;

void logging_aspect(Context *ctx, const char *stage) {
    if (stage[0] == 'b') {
        printf("Processing sensor %d\n", ctx->data.sensor_id);
    }
}

void process_motion(SensorData data) {
    printf("Acceleration: %d\n", data.value);
}

void dispatch_with_aspects(
    SensorData data,
    uint8_t power_level,
    void (*aspects[])(Context*, const char*)
) {
    Context ctx = {data, power_level};

    for (int i = 0; aspects[i] != NULL; i++)
        aspects[i](&ctx, "before");

    process_motion(ctx.data);

    for (int i = 0; aspects[i] != NULL; i++)
        aspects[i](&ctx, "after");
}
```

#### Characteristics

* Separation of concerns
* Reusable behavioural layers
* Additional call overhead
* Common in middleware architectures



### 4. Probabilistic Dispatch

#### Concept

Dispatch selects handlers based on probability weights.
Selection is stochastic rather than deterministic.

#### Embedded Context

Used for:
* Redundant sensor balancing
* Reliability testing
* Load distribution
* Simulation or fuzzing

Not suitable for strict hard real-time determinism.

#### C Example (Redundant Sensors)

```c
#include <stdlib.h>

typedef int16_t (*SensorHandler)(int16_t);

typedef struct {
    SensorHandler handler;
    float weight;
} ProbDispatchEntry;

int16_t primary(int16_t v) {
    printf("Primary: %d\n", v);
    return v;
}

int16_t backup(int16_t v) {
    printf("Backup: %d\n", v);
    return v;
}
```

Weighted selection is implemented using cumulative probability.

#### Characteristics

* Non-deterministic
* Useful for statistical behaviour
* Requires RNG
* Harder to debug



### 5. Introspective Dispatch

#### Concept

Dispatch is driven by inspecting runtime metadata
instead of static mappings.

In dynamic languages this uses reflection.
In C, it is approximated using configuration tables.

#### Embedded Context

Useful for:
* EEPROM-based configuration
* Hardware-variant detection
* Firmware feature toggles
* Plugin-style architectures

#### C Example (Config-Based Sensor Processing)

```c
typedef struct {
    uint8_t config;
    int16_t value;
} SensorData;

typedef struct {
    uint8_t config_id;
    void (*handler)(SensorData);
} HandlerEntry;

void process_temperature(SensorData d) {
    printf("Temp: %d\n", d.value * 10);
}

HandlerEntry handlers[] = {
    {0x01, process_temperature},
    {0x00, NULL}
};

void dispatch_by_config(SensorData data) {
    for (int i = 0; handlers[i].handler != NULL; i++) {
        if (handlers[i].config_id == data.config) {
            handlers[i].handler(data);
            return;
        }
    }
}
```

#### Characteristics

* Runtime adaptability
* Table-driven
* Deterministic
* Limited by ROM size



## Why These Flavours Are Distinct

* *CPS Dispatch* focuses on explicit control flow and deferred execution.
* *Rule-Based Dispatch* emphasises declarative condition matching.
* *Aspect-Oriented Dispatch* composes behaviours around a core function.
* *Probabilistic Dispatch* introduces stochastic routing.
* *Introspective Dispatch* adapts based on runtime metadata.

Each represents a fundamentally different axis of dispatch design:
control flow, logic inference, cross-cutting composition,
random selection, and runtime adaptation.



## Embedded System Considerations

When applying dispatch in embedded systems, constraints dominate design:
* *Memory*: Static tables preferred over dynamic allocation.
* *Real-Time Guarantees*: Deterministic execution paths are critical.
* *Power Consumption*: Minimise unnecessary function calls.
* *Reliability*: Avoid recursion and unbounded rule chains.
* *Scalability*: Limited by ROM and RAM footprint.

Function pointer tables, static rule arrays, and explicit control
structures remain the most practical tools in C-based firmware.



## Conclusion

Dispatch is far richer than `if-else` or `switch-case`.
Understanding alternative dispatch mechanisms allows the programmer
to choose structures that improve:

* Performance
* Extensibility
* Maintainability
* Real-time correctness
* System modularity

From simple opcode routing to asynchronous embedded sensor hubs,
dispatch remains one of the most fundamental architectural tools
in systems programming.
