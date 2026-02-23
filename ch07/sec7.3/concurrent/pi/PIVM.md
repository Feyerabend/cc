
## π-vm

### 1. Basic Example (P and Q)

```pi-calculus
P = a!⟨42⟩.0
Q = a?(x).log⟨x⟩.0

System = (νa)(P | Q)
```
* `P` sends value `42` on channel `a` then terminates (`0`)
* `Q` receives on `a` (binding to `x`), logs it, then terminates
* The system creates a private channel `a` (`νa`) for communication

```mermaid
sequenceDiagram
    participant P
    participant a as Channel a
    participant Q
    
    P->>a: send(42)
    a->>Q: receive(x)
    Q->>Q: log(x=42)
```


### 2. Advanced Example (Client-Server-Coordinator)

```pi-calculus
Server = reply_ch?(reply).request?(client_msg).reply!⟨client_msg+100⟩.0

Client = reply_ch?(server_reply_ch).request!⟨42⟩.server_reply_ch?(response).log⟨response⟩.0

Coordinator = (νrequest)(νreply_ch)(νreply)(
                reply_ch!⟨reply⟩.0 
                | reply_ch!⟨reply⟩.0
              )

System = (Server | Client | Coordinator)
```

Features:
- Coordinator creates 3 private channels (`νrequest,νreply_ch,νreply`)
- Sends `reply` channel twice (to Server and Client)
- Server receives the reply channel first, then processes requests
- Client gets response on dynamically provided channel

```mermaid
sequenceDiagram
    participant Coordinator
    participant Server
    participant Client
    participant reply_ch as Channel reply_ch
    participant request as Channel request
    participant reply as Channel reply
    
    Coordinator->>reply_ch: create
    Coordinator->>request: create
    Coordinator->>reply: create
    Coordinator->>Server: spawn
    Server->>reply_ch: send(reply)
    Coordinator->>Client: send(reply_ch)
    Client->>request: send(42)
    Server->>request: receive(client_msg)
    Server->>reply: send(client_msg+100)
    Client->>reply: receive(response)
    Client->>Client: log(response)
```


### 3. Replication Example (Request Handlers)

```pi-calculus
(* Handler processes *)
Handler1 = handler1?(req).response!⟨req+1⟩.0
Handler2 = handler2?(req).response!⟨req+1⟩.0 
Handler3 = handler3?(req).response!⟨req+1⟩.0

(* Main handler with replication *)
RequestHandler = (νrequests)(νresponse)(νhandler1)(νhandler2)(νhandler3)(
                  requests?(req1).handler1!⟨req1⟩.0
                  | requests?(req2).handler2!⟨req2⟩.0
                  | requests?(req3).handler3!⟨req3⟩.0
                  | Handler1 | Handler2 | Handler3
                )

Client = requests!⟨1⟩.requests!⟨2⟩.requests!⟨3⟩.
         response?(resp1).response?(resp2).response?(resp3).
         log⟨resp1⟩.log⟨resp2⟩.log⟨resp3⟩.0

System = (RequestHandler | Client)
```

```mermaid
sequenceDiagram
    participant Client
    participant Handler
    participant h1 as Handler1
    participant h2 as Handler2
    participant h3 as Handler3
    participant requests as Channel requests
    participant response_ch as Channel response_ch
    
    Handler->>requests: create
    Handler->>response_ch: create
    Handler->>h1: spawn
    Handler->>h2: spawn
    Handler->>h3: spawn
    
    Client->>requests: send(1)
    Handler->>h1: forward(1)
    h1->>response_ch: send(2)
    
    Client->>requests: send(2)
    Handler->>h2: forward(2)
    h2->>response_ch: send(3)
    
    Client->>requests: send(3)
    Handler->>h3: forward(3)
    h3->>response_ch: send(4)
    
    Client->>response_ch: receive(resp1=2)
    Client->>response_ch: receive(resp2=3)
    Client->>response_ch: receive(resp3=4)
```


### π-calculus concepts mapped
1. *Channel creation* `(νx)` ↔ `new_channel`  
2. *Send* `x!⟨v⟩` ↔ `send(x,v)`  
3. *Receive* `x?(y)` ↔ `receive(x,y)`  
4. *Parallel* `P|Q` ↔ `spawn`/threading  
5. *Replication* `!P` ↔ Your `replicate` operation  


### Extended Example with Select

For the `select` operation, here's a π-calculus equivalent using guarded choice:
```pi-calculus
P = τ.(x?(y).P1 + y?(z).P2 + timeout.P3
```
(Where `+` represents non-deterministic choice between guarded processes)
