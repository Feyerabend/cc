
## Exercise: From Time, Concurrency, and Determinism to Scheduling

*This is a student exercise. No guided walkthrough is provided.*

You have already worked through:
- *Synchronisation* (Concurrency + State + Determinism)
- *Real-Time Systems* (Determinism + Time + Latency)

This combination uses three of the same forces in a different configuration:

```
Time + Concurrency + Determinism  ->  Scheduling
```

### Your Task

Without being guided, derive why scheduling must exist.

Start here:
- Multiple tasks want to run concurrently.
- Only a finite number of CPUs exist (perhaps just one).
- The system must behave predictably.

Ask yourself:
1. Who decides which task runs next?
2. What happens if no one decides?
3. What makes a scheduling decision *correct*?
4. How do real-time constraints (deadlines) change what "correct" means?
5. What is the relationship between scheduling and the synchronisation
   and real-time systems you have already derived?

Build a small simulation. Observe what happens with no scheduler,
a naive scheduler, and a principled one. Measure the outcomes.

Then name what you built.
