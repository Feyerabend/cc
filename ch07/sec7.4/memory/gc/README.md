
## Garbage Colletion: A Short Overview

* *Automatic vs Manual:* Low-level languages like C rely on manual memory management,
  while others (like C++ with smart pointers) can offer semi-automatic mechanisms.

* *Reachability:* Most garbage collectors track whether allocated objects are *reachable*
  from active variables or the call stack. Unreachable objects are candidates for collection.

* *Strategies:*

  * *Reference counting*--track how many references point to an object;
    when zero, it can be freed. Simple but can’t handle cycles.

  * *Tracing/Mark-and-sweep*--traverse reachable objects from roots,
    mark them, then sweep and free everything unmarked.

  * *Generational collection*--separate objects by age;
    young objects are collected more frequently because they tend to die quickly.

* *Trade-offs:* GC simplifies memory safety but adds runtime overhead and
  non-deterministic pauses. Manual management gives control but is error-prone.

In essence, garbage collection is often about *automating memory cleanup* while
balancing performance, safety, and complexity in programs.

