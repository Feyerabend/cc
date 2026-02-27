
## EventScript: Event-Driven Language with Compiler & VM

A simple event-driven programming language:
- *Abstract Syntax Tree (AST)* representation
- *Bytecode Compiler* (AST -> Bytecode)
- *Stack-based Virtual Machine* with event loop
- *Event queue* and *handler registry*
- First-class *callbacks* via event handlers

```
Source (AST) -> Compiler -> Bytecode -> VM -> Event Loop
```

1. *AST (`ast.c`)*: Tree representation of programs
2. *Compiler (`compiler.c`)*: Transforms AST into bytecode
3. *VM (`vm.c`)*: Executes bytecode with event system
4. *Event System*: Queue + Handler Registry + Dispatcher


### Examples

```
emit "event_name", data
```
Enqueues an event with associated data onto the event queue.

```
on "event_name" {
    print "Handle the event!"
}
```
Registers a handler (callback) for a specific event type.

```
print 5 + 3    # Outputs: 8
print 10 * 2   # Outputs: 20
```

- Numbers: `42`, `100`, `0`
- Strings: `"hello"`, `"process"`


### How It Works

#### 1. Compilation Phase

The AST is compiled into bytecode instructions:

```c
// This AST:
on "greet" {
    print "Hello!"
}
emit "greet", 42

// Becomes this bytecode:
CONST 0         // Push "greet"
REGISTER 4      // Register handler at PC=4, skip to after RETURN
CONST 1         // [Handler starts] Push "Hello!"
PRINT           // Print it
RETURN          // End handler
CONST 2         // [Main continues] Push "greet"
CONST 3         // Push 42
EMIT            // Enqueue event
HALT
```

#### 2. Execution Phase

The VM runs through the bytecode:
- Registers handlers during initialization
- Skips over handler bodies (jumps past RETURN)
- Emits events into the queue
- Halts at the end

#### 3. Event Loop Phase

After main execution halts, the event loop processes the queue:

```c
while (event_queue not empty) {
    event = dequeue()
    for each handler matching event.name {
        push event.data onto stack
        jump to handler PC
        execute handler bytecode
        return from handler
    }
}
```

This demonstrates the classic *event-driven execution model*.



### Bytecode Instructions

| Opcode      | Description                          |
|-------------|--------------------------------------|
| `CONST`     | Push constant onto stack             |
| `ADD`       | Pop two, push sum                    |
| `SUB`       | Pop two, push difference             |
| `MUL`       | Pop two, push product                |
| `DIV`       | Pop two, push quotient               |
| `PRINT`     | Pop and print value                  |
| `EMIT`      | Pop data and event name, enqueue     |
| `REGISTER`  | Pop event name, register handler     |
| `RETURN`    | Return from handler                  |
| `HALT`      | Stop main execution                  |
| `POP`       | Discard top of stack                 |



#### Example 1: Basic Handler

```c
on "greet" {
    print "Hello from handler!"
}
emit "greet", 42
```

*Output:*
```
[HANDLER] Registered 'greet' at PC=4
[EVENT QUEUE] Enqueued: greet
[EVENT LOOP] Processing: greet (data=42)
[HANDLER OUTPUT] Hello from handler!
```

#### Example 2: Multiple Handlers

```c
on "start" { print "Starting.." }
on "finish" { print "Done!" }
emit "start", 0
emit "finish", 100
```

*Output:*
```
[HANDLER OUTPUT] Starting..
[HANDLER OUTPUT] Done!
```

#### Example 3: Event Chaining

Handlers can emit new events, creating chains:

```c
on "click" {
    emit "process", 10
}
on "process" {
    print "Processing data.."
}
emit "click", 1
```

*Execution flow:*
1. "click" event queued
2. Event loop processes "click"
3. Handler emits "process" event (queued)
4. Event loop processes "process"
5. Handler prints message

#### Example 4: Arithmetic

```c
on "calculate" {
    print 5 + 3
}
emit "calculate", 0
```

*Output:*
```
[HANDLER OUTPUT] 8
```



### Concepts Illustrated

#### 1. Callbacks as Event Handlers

Event handlers are *callbacks*--functions registered
to be called later when specific events occur:

```c
// Register callback
on "event" { /* callback body */ }

// Trigger callback later
emit "event", data
```

This is conceptually identical to the probably more familiar JavaScript:
```javascript
element.addEventListener("click", () => { /* callback */ });
element.click();  // Triggers callback
```

#### 2. Event Loop

The VM implements a *classic event loop*:

```c
void vm_event_loop(VM *vm) {
    while (event_queue not empty) {
        event = dequeue()
        find_and_execute_handlers(event)
    }
}
```

This mirrors Node.js, browser JavaScript, and other event-driven systems.

#### 3. Inversion of Control

Handlers demonstrate *inversion of control*:
- You don't call the handler directly
- You register it and the system calls it when appropriate
- The "when" is determined by the event dispatcher, not the caller

#### 4. Asynchronous Execution

Events are processed *after* main code completes:
```
1. Register handlers (setup phase)
2. Emit events (goes to queue, not executed immediately)
3. HALT main execution
4. Event loop processes queue (asynchronous execution)
```


### Extending the Language

#### Add a New Opcode
1. Add enum to `OpCode` in `eventscript.h`
2. Implement in compiler (`compiler.c`)
3. Implement in VM (`vm.c`)
4. Update `opcode_name()` for debugging

#### Add New AST Node Type
1. Add enum to `ASTNodeType`
2. Add struct variant in `ASTNode` union
3. Create constructor function (`ast_*.c`)
4. Add compilation logic in `compiler.c`
5. Add cleanup in `ast_free()`

#### Add Variables
The VM has a `globals[]` array ready for variable storage. You'd need to:
- Add `LOAD` and `STORE` instructions
- Implement assignment AST nodes
- Track variable names in a symbol table


### Illustration

This implementation demonstrates:
-  *Compilation pipeline* (AST -> Bytecode -> Execution)  
-  *Stack-based VM* architecture  
-  *Event-driven programming* model  
-  *Callbacks* implemented in C  
-  *Event queue* and dispatch logic  
-  *Handler registry* pattern  
-  *Bytecode interpretation*  
-  *Memory management* in C  

