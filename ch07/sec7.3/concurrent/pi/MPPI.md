
## mp-π

### Core Primitives in π-calculus

```pi-calculus
(* Channel creation with multiprocessing semantics *)
NewChannel(name) = (νname)(!name?lock⟨⟩.name!status⟨false⟩.0 | name!queue⟨⟩.0)

(* Process definition with environment *)
Process[env](name, steps) = steps[env]

(* Shared manager process *)
Manager = !(νnew_channel)(new_channel!⟨⟩.Manager)
         | !(νnew_lock)(new_lock!⟨⟩.Manager)
         | !(νnew_value)(new_value!⟨⟩.Manager)
```

### Basic Example (P and Q) in π-calculus

```pi-calculus
(* System initialisation *)
System = (νmanager)(Manager | 
          (νprint_lock)(NewLock(print_lock) |
          (νenvP)(NewEnv(envP) |
          (νenvQ)(NewEnv(envQ) |
          (νchannels)(NewDict(channels) |
          (νregistry)(NewDict(registry) |
          P[envP] | Q[envQ]
        )

(* Process definitions *)
P[env] = (νa)(
           channels!put⟨a, (νq)(νlock)(νclosed)(Queue(q) | Lock(lock) | closed!⟨false⟩)⟩.
           env!set⟨"a", a⟩.
           a!lock⟨⟩.a!send⟨42⟩.a!unlock⟨⟩.
           env!get⟨"pid"⟩?(pid).print_lock!acquire⟨⟩.print!⟨pid, "sent 42"⟩.print_lock!release⟨⟩.0
         )

Q[env] = env!get⟨"a"⟩?(a).
         a!lock⟨⟩.a?receive⟨x⟩.a!unlock⟨⟩.
         env!set⟨"x", x⟩.
         print_lock!acquire⟨⟩.print!⟨x⟩.print_lock!release⟨⟩.0

(* Helper processes *)
Queue(q) = !q?put⟨x⟩.Queue(q) | !q?get⟨⟩.q!x⟨⟩.Queue(q)
Lock(l) = l?acquire⟨⟩.l!release⟨⟩.Lock(l)
Dict(d) = !d?put⟨k,v⟩.Dict(d) | !d?get⟨k⟩.d!v⟨⟩.Dict(d)
```

### Key Parallels

1. *Multiprocessing Manager* ↔ Replicated `Manager` process:
   ```pi-calculus
   Manager = !(νnew_channel)(new_channel!⟨⟩.Manager) | ...
   ```

2. *Channel with Lock*:
   ```pi-calculus
   MPChannel = Lock(lock) | Queue(q) | Status(closed)
   ```

3. *Process Spawning*:
   ```pi-calculus
   Spawn(P) = (νnew_pid)(P[new_env] | registry!put⟨new_pid⟩)
   ```

4. *Shared Printing*:
   ```pi-calculus
   PrintLock = !acquire⟨⟩.release⟨⟩.PrintLock
   ```


### Extended Version with Full Semantics

For the complete multiprocessing behaviour, we'd need to model:

1. *Process Isolation*:
   ```pi-calculus
   Process[env] = (νprivate_memory)(...)
   ```

2. *Serialisation* (Python's `Manager`):
   ```pi-calculus
   Proxy(x) = !x?get⟨⟩.x!val⟨⟩.Proxy(x) | !x?set⟨v⟩.Proxy(x[v])
   ```

3. *Process Termination*:
   ```pi-calculus
   Stop = registry!del⟨pid⟩.0
   ```

### Differences from Standard π-calculus

1. *Shared Memory*: Real π-calculus has no shared state--we model it with helper processes
2. *Serialisation*: Implicit in Python, explicit in our π-calculus via message forwarding
3. *OS Processes*: The `(νp)` creation maps to OS-level process forking

