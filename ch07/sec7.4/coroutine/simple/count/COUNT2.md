
## Count 2

- The state machine lifecycle of a coroutine
- The main operations (create, resume, yield)

```mermaid
stateDiagram-v2
    [*] --> CO_READY
    CO_READY --> CO_RUNNING: coroutine_resume()
    CO_RUNNING --> CO_SUSPENDED: coroutine_yield()
    CO_SUSPENDED --> CO_RUNNING: coroutine_resume()
    CO_RUNNING --> CO_DEAD: Execution completes
    CO_DEAD --> [*]

    classDef coroutine fill:#e6f3ff,stroke:#333
    class CO_READY,CO_RUNNING,CO_SUSPENDED,CO_DEAD coroutine

    note right of CO_RUNNING
        Executes coroutine function
        (e.g. counter_function)
        Manages PC and state
    end note

    note left of CO_SUSPENDED
        Preserves:
        - Program Counter (pc)
        - Yield Value
        - Coroutine Data
    end note
```

- Preservation of execution context between suspensions
- Interaction between main program and coroutines


```mermaid
flowchart TD
    A[Main Program] --> B[Create Coroutine]
    B --> C[coroutine_create]
    C --> D[Initialize state=READY, pc=0]
    
    A --> E[Resume Coroutine]
    E --> F[coroutine_resume]
    F --> G{State?}
    G -->|READY/RUNNING| H[Execute coroutine function]
    H --> I[Update PC and state]
    I --> J{Yield or Complete?}
    J -->|Yield| K[Return to main with value]
    J -->|Complete| L[Mark as DEAD]
    
    K --> E
    L --> M[Cleanup]
    
    classDef coroutine fill:#e6f3ff,stroke:#333
    class C,D,F,H,I,J,K,L coroutine
```
