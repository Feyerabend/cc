
## Session Types: Types for Communication Protocols

Session types are a type system for describing *communication protocols*
between concurrent processes. Instead of typing what values a function takes,
session types describe the *sequence and structure of messages*
exchanged over a channel.

Think of them as a contract:
"If you want to talk to me on this channel, here's the conversation we're going to have."



### Basic Idea

*Traditional types:*
```
function add(x: Int, y: Int) -> Int
```
Says what values go in and out.

*Session types:*
```
channel: !Int.?String.end
```
Says what conversation happens:
- ! means "send" (output)
- ? means "receive" (input)
- This reads: "send an Int, then receive a String, then close"

The channel itself is typed by the protocol it supports.



#### Basic Session Type Constructors


__Sequential Communication__

*!T.S* - Send a value of type T, then continue with protocol S
```
!Int.?String.end
```
"I'll send you an integer, you'll send me a string, we're done"

*?T.S* - Receive a value of type T, then continue with protocol S
```
?String.!Bool.end
```
"You send me a string, I'll send you a boolean, we're done"


__Choice and Branching__

*⊕{l₁: S₁, l₂: S₂, ...}* - External choice (I choose which branch)
```
⊕{ok: !Int.end, error: !String.end}
```
"I'll tell you either 'ok' (and send an int) or 'error' (and send a string)"

*&{l₁: S₁, l₂: S₂, ...}* - Internal choice (you choose which branch)
```
&{get: ?Int.!Data.end, put: !Data.end}
```
"You tell me whether you want to 'get' (I'll ask for an int, send data) or 'put' (you send data)"


__Parallel Communication__

*S₁ ⊗ S₂* - Both protocols happen in parallel
```
!Int.end ⊗ ?String.end
```
"Simultaneously: I send you an int on one channel AND you send me a string on another"


__Recursion__

*μX.S* - Recursive protocol
```
μX.(?Int.!Int.X)
```
"Forever: receive an int, send an int back, repeat"



#### Duality: The Two Sides of a Channel

Every session type has a *dual*--the other end of the conversation.

*Rules:*
- Dual of !T.S is ?T.S̄ (send ↔ receive)
- Dual of ?T.S is !T.S̄
- Dual of ⊕{...} is &{...} (choice ↔ offering)
- Dual of S₁ ⊗ S₂ is S̄₁ ⊗ S̄₂

*Example:*
```
Client:  !String.?Int.end
Server:  ?String.!Int.end  (dual)
```

If one side sends, the other must receive. The types enforce this.



### A Complete Example: Client-Server Protocol

*Server offers a calculation service:*

```
Server type:
  μX.&{ calculate: ?Int.?Int.!Int.X,
        shutdown: end }

Client type (dual):
  μX.⊕{ calculate: !Int.!Int.?Int.X,
        shutdown: end }
```

*What this means:*
- Server offers a choice: "calculate" or "shutdown"
- If client chooses "calculate": client sends two ints, server sends result, repeat
- If client chooses "shutdown": both end

*Actual code (pseudo):*
```
// Server process
loop:
  choice = receive_label()
  match choice:
    calculate:
      x = receive_int()
      y = receive_int()
      send_int(x + y)
      goto loop
    shutdown:
      close()

// Client process
send_label(calculate)
send_int(5)
send_int(7)
result = receive_int()  // gets 12
send_label(shutdown)
close()
```

The session types guarantee they can't get out of sync.



### What Session Types Guarantee

__1. Communication Safety__

*You can't send the wrong type*

```
Channel type: !Int.end
send_string(ch, "hello")  // TYPE ERROR!
```

The type checker catches protocol violations at compile time.


__2. Session Fidelity__

*Both ends agree on the protocol*

If the client has type !Int.?String.end, the server MUST have
type ?Int.!String.end (the dual). The type system enforces this.


__3. Deadlock Freedom__

*Well-typed processes can't deadlock*

This is remarkable. If your session-typed program type checks,
it cannot deadlock (under certain conditions about channel usage).

*Why?* The linear discipline ensures:
- Every send has a matching receive
- Channels are used in compatible orders
- No circular dependencies between channels


__4. Progress__

*Communication will eventually happen*

If one side is ready to send, the other will eventually be
ready to receive. No one gets stuck waiting forever.



### Linearity: Use Each Channel Exactly Once

Session types are *linear types*--each channel endpoint must be used exactly once.

*This prevents:*

```
// ERROR: Using channel twice
send(ch, 42)
send(ch, 43)  // ch already consumed!

// ERROR: Not using channel
let ch = create_channel()
// forgot to use it - TYPE ERROR

// ERROR: Using channel in both branches
if condition:
  send(ch, 1)
else:
  send(ch, 2)  // ch used in both branches - violates linearity
```

You must explicitly handle both branches:
```
if condition:
  send(ch, 1)
else:
  send(ch, 2)
// Now ch is consumed on both paths
```



### Parallel Protocols with Tensor (⊗)

The tensor ⊗ lets you express truly parallel communication:

*Example: Parallel file server*
```
Server: ?Filename.(!FileData ⊗ !Metadata).end
```
"Receive a filename, then IN PARALLEL send the file data AND send metadata"

*Two clients can connect:*
```
Client1: !Filename.?FileData.end
Client2: !Filename.?Metadata.end
```

The server talks to both clients simultaneously on different channels.
The ⊗ makes the parallelism explicit in the type.



### Delegation: Passing Channels

Session types support *channel passing*--sending a channel over another channel.

*Type:*
```
!S.end
```
"Send a channel with protocol S"

*Example: Web server delegating to workers*
```
Dispatcher: μX.(?Request.!WorkerChannel.X)
  where WorkerChannel: !Request.?Response.end

Worker: ?Request.?Response.end
```

Dispatcher receives requests and sends each to a worker by
passing them a channel to handle that specific request.



### Real-World Applications

__1. Network Protocols__
```
HTTP_Response: 
  !StatusCode.
  !Headers.
  ⊕{ no_body: end,
     body: !Chunk*.end }
```

__2. Database Transactions__
```
Transaction:
  &{ begin: μX.⊕{ query: !SQL.?ResultSet.X,
                  commit: end,
                  rollback: end }}
```

__3. Distributed Systems__
```
Consensus:
  μX.(&{ propose: !Value.?Decision.X,
         accept: ?Value.!Ack.X })
```

__4. API Protocols__
```
AuthService:
  &{ login: ?Credentials.
           ⊕{ success: !Token.ServiceMenu,
              failure: !Error.end },
     logout: end }
```



### Session Types vs Traditional Types

| Traditional Types | Session Types |
|-------------------|---------------|
| Type values | Type conversations |
| Static structure | Protocol sequence |
| "What data is this?" | "What happens next?" |
| Prevent bad data | Prevent protocol violations |
| Function signatures | Communication patterns |



### Advanced: Multiparty Session Types

Regular session types describe two-party (binary) protocols.
*Multiparty session types* describe protocols among N participants.

*Example: Three-way auction*
```
Auctioneer → Bidder1: request_bid
Auctioneer → Bidder2: request_bid
Bidder1 → Auctioneer: bid(amount1)
Bidder2 → Auctioneer: bid(amount2)
Auctioneer → Winner: you_won
Auctioneer → Loser: you_lost
```

Each participant has a *local type* (their view),
and these must be *compatible* (form a valid global protocol).



### Languages with Session Types

*Research languages:*
- *Sill* - Pure session-typed functional language
- *Links* - Web programming with session types
- *LinearML* - ML with linear session types

*Practical influence:*
- *Rust* - Ownership/borrowing inspired by linear types
- *Go* - Channels (untyped protocols, but similar ideas)
- *Scala* - Libraries for session types (lchannels, effpi)
- *Erlang/Elixir* - Actor patterns (informal protocols)



### Why Session Types Matter for Parallelism

Session types bring *type-level guarantees* to concurrent programming:

1. *No race conditions* - Linear discipline prevents shared state issues
2. *No deadlocks* - Type checking proves deadlock freedom
3. *Protocol compliance* - Both sides guaranteed to follow the script
4. *Compositional* - Build complex protocols from simple ones
5. *Local reasoning* - Each process typed independently

They answer the question: *"How do we know our parallel programs communicate correctly?"*

Traditional types tell us values are correct.
Session types tell us *interactions* are correct.



### Insight ..

Communication is not just sending data - it's *following a protocol*.

Session types make protocols first-class, checkable, and enforced by the type system.
This transforms concurrent programming from "hope we synchronized correctly"
to "proved correct by types."

In a world where parallel systems are everywhere (web services, distributed databases,
IoT, cloud computing), session types offer a path to reliable concurrent code.

