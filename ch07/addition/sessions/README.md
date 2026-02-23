
## Session Types VM

A minimal virtual machine for executing
session-typed concurrent processes in Python.

1. *Type safety* - Can't send/receive wrong types
2. *Linearity* - Each channel endpoint used exactly once
3. *Protocol adherence* - Processes follow their session types
4. *Deadlock freedom* - Well-typed processes can't deadlock (in theory!)


### Architecture

```
session_vm.py       - Core VM implementation
├── SessionType     - Session type definitions (!, ?, ⊕, &, end)
├── ChannelEndpoint - Typed channel endpoints with queues
├── Process         - Process definitions (Send, Receive, Select, etc.)
└── SessionTypesVM  - The virtual machine

examples.py         - Example programs demonstrating the VM
```


### Session Type Syntax

| Notation | Type | Meaning |
|----------|------|---------|
| `!T.S` | Send | Send value of type T, then continue with S |
| `?T.S` | Receive | Receive value of type T, then continue with S |
| `⊕{l: S, ...}` | Choice | Offer choice of labeled branches |
| `&{l: S, ...}` | Offer | Accept choice from partner |
| `end` | End | Session complete |


### Process Syntax

| Process | Meaning |
|---------|---------|
| `SendProcess(ch, val, cont)` | Send `val` on channel `ch`, then `cont` |
| `ReceiveProcess(ch, var, cont)` | Receive into `var` from `ch`, then `cont` |
| `SelectProcess(ch, label, cont)` | Send choice `label`, then `cont` |
| `OfferProcess(ch, branches)` | Accept choice, branch accordingly |
| `CloseProcess(ch)` | Close channel (must be at `end` type) |
| `ParallelProcess(p1, p2)` | Run `p1` and `p2` in parallel |


### Example: Simple Communication

```python
from session_vm import *

vm = SessionTypesVM()

# Session type: !Int.?String.end
# "Send an Int, receive a String, done"
session_type = Send_(int, Recv_(str, End_()))

# Create dual channel endpoints
client_ch, server_ch = vm.create_channel(session_type)

# Client sends 42, receives response
client = SendProcess(
    "ch", 42,
    ReceiveProcess(
        "ch", "response",
        CloseProcess("ch")
    )
)

# Server receives number, sends response
server = ReceiveProcess(
    "ch", "num",
    SendProcess(
        "ch", "Got it!",
        CloseProcess("ch")
    )
)

# Run in parallel
import threading
t1 = threading.Thread(target=lambda: client.run({"ch": client_ch}))
t2 = threading.Thread(target=lambda: server.run({"ch": server_ch}))
t1.start(); t2.start()
t1.join(); t2.join()
```

Output:
```
✓ Created channel ch_0
  Endpoint A: !int.?str.end
  Endpoint B: ?int.!str.end

  -> Sent 42 on ch_0_A
  <- Received 42 on ch_0_B
  -> Sent Got it! on ch_0_B
  ← Received Got it! on ch_0_A
    Closed ch_0_A
    Closed ch_0_B
```

### Example: Calculator with Choice

```python
# Server offers: add, multiply, or done
session_type = Offer_({
    "add": Recv_(int, Recv_(int, Send_(int, End_()))),
    "multiply": Recv_(int, Recv_(int, Send_(int, End_()))),
    "done": End_()
})

client_ch, server_ch = vm.create_channel(session_type)

# Client chooses "add", sends 5 and 3
client = SelectProcess(
    "ch", "add",
    SendProcess("ch", 5,
        SendProcess("ch", 3,
            ReceiveProcess("ch", "result",
                CloseProcess("ch")
            )
        )
    )
)

# Server handles the choice
server = OfferProcess("ch", {
    "add": ReceiveProcess("ch", "x",
        ReceiveProcess("ch", "y",
            SendProcess("ch", 8,  # x + y
                CloseProcess("ch")
            )
        )
    ),
    "multiply": ...,
    "done": CloseProcess("ch")
})
```


### What Gets Checked

#### Type Safety
```python
# Session expects Int
session_type = Send_(int, End_())
client_ch, _ = vm.create_channel(session_type)

# ERROR: Trying to send String
SendProcess("ch", "wrong!", ...).run({"ch": client_ch})
# TypeError: Expected int, got str
```

#### Linearity
```python
# Can't use channel twice
send1 = SendProcess("ch", 42, None)
send1.run({"ch": client_ch})  # OK, first use

send2 = SendProcess("ch", 43, None)
send2.run({"ch": client_ch})  # ERROR!
# RuntimeError: Channel ch_0_A used more than once!
```

#### Protocol Adherence
```python
# Session expects Send
session_type = Send_(int, End_())
client_ch, _ = vm.create_channel(session_type)

# ERROR: Trying to Receive instead
ReceiveProcess("ch", "x", ...).run({"ch": client_ch})
# TypeError: Expected Send type, got Receive
```


### Concepts Demonstrated

#### Duality
When you create a channel, you get two endpoints with *dual* session types:
- If one side has `!Int`, the other has `?Int`
- If one side has `⊕{...}`, the other has `&{...}`
- This ensures protocols match up

#### Linearity
Each channel endpoint can only be used *once*. After using it, you get a
continuation with the rest of the protocol. This prevents:
- Race conditions (can't share channels)
- Resource leaks (must close channels)
- Protocol confusion (must follow sequence)

#### Session Types as Protocols
Session types describe the *entire conversation*, not just one message.
The type evolves as communication happens:

```
!Int.?String.end
 ↓ (send 42)
?String.end
 ↓ (receive "hi")
end
 ↓ (close)
(done)
```

### Limitations

This is a *minimal educational VM*.
It doesn't implement:
- Recursive session types (μX.S)
- Parallel composition in session types (S₁ ⊗ S₂)
- Delegation (sending channels over channels)
- Polymorphism (parametric session types)
- Advanced type checking (would need separate type checker)
- Optimisations (very slow)


### What You Can Learn

1. *How session types work* - See types enforced at runtime
2. *Linear types in practice* - Understand "use once" discipline
3. *Duality* - How two sides of a protocol relate
4. *Process calculi* - Basic π-calculus-like processes
5. *Type-driven concurrency* - Types preventing race conditions


### Extension Ideas

If you want to extend this VM:
1. *Add recursion* - `μX.S` for unbounded protocols
2. *Add delegation* - Send channels over channels
3. *Separate type checker* - Type-check before execution
4. *Better scheduler* - More efficient process execution
5. *Distributed* - Run processes on different machines
6. *DSL* - Parser for session type syntax
7. *Error messages* - Better diagnostics
8. *Visualisation* - Show protocol execution graphically


### Further Reading

- *Session Types*: Honda, Vasconcelos, Kubo (1998)
- *Linear Logic*: Girard (1987)
- *Linear Logic & Session Types*: Wadler (2012) "Propositions as Sessions"
- *Practical Session Types*: Sill language, Links language
- *π-calculus*: Milner (1999) "Communicating and Mobile Systems"

