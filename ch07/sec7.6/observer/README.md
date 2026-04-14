
## Observer - From Pattern to Runtime

The Observer pattern has a cleaner evolution than most. It does not simply
dissolve into a language feature - it passes through three distinct stages,
each of which absorbs a different part of the original machinery into a
lower layer.

Tracing those stages shows what "the pattern disappears" actually means in practice.



### Stage 1 - Manual Observer (Java)

The original GoF Observer requires three things to be written by hand:
a subscription interface, a subject that manages the list, and an explicit
notification loop.

```java
interface Observer {
    void update(String data);
}

class Subject {
    private final List<Observer> observers = new ArrayList<>();

    void subscribe(Observer o)   { observers.add(o); }
    void unsubscribe(Observer o) { observers.remove(o); }

    void notifyAll(String data) {
        for (Observer o : observers) {
            o.update(data);
        }
    }
}

class Logger implements Observer {
    public void update(String data) {
        System.out.println("log: " + data);
    }
}
```

The programmer owns the entire mechanism: the list, the loop, the subscription
protocol. Every subject in the system replicates this structure.



### Stage 2 - Function-Based (Python / JavaScript)

When functions are first-class values, the interface and class hierarchy
collapse. The list remains, but the machinery around it shrinks to almost
nothing:

```python
listeners = []

def subscribe(fn):
    listeners.append(fn)

def emit(data):
    for fn in listeners:
        fn(data)

subscribe(lambda d: print(f"log: {d}"))
emit("sensor reading")
```

The same structure in JavaScript is identical in form. The pattern
survives conceptually - subscription list, notification loop - but the
language no longer requires a class to express it.

What the programmer still owns: the list, the loop, and the `emit` call.



### Stage 3 - Async Streams (Python asyncio)

In asynchronous runtime models, the remaining machinery moves into the
runtime itself. The programmer expresses *intent* - produce values,
consume values - without writing the dispatch mechanism.

```python
async def temperature_sensor(channels):
    for temp in [22.1, 22.3, 22.8, 23.5, 22.9]:
        await asyncio.sleep(0.05)
        for ch in channels:
            await ch.put(temp)
    for ch in channels:
        await ch.put(None)   # end-of-stream sentinel

async def logger(channel):
    while True:
        temp = await channel.get()
        if temp is None:
            break
        print(f"log: {temp:.1f} °C")

async def alerter(channel):
    while True:
        temp = await channel.get()
        if temp is None:
            break
        if temp > 23.0:
            print(f"ALERT: {temp:.1f} exceeds threshold")
```

`logger` and `alerter` never call `subscribe`. `temperature_sensor` never
calls `notifyAll`. Neither consumer knows the other exists. The event loop
schedules all three coroutines concurrently; `asyncio.Queue` carries values
between them.

The wiring - the only place that names both producer and consumers -
is three lines in `main`:

```python
async def main():
    log_ch   = asyncio.Queue()
    alert_ch = asyncio.Queue()

    await asyncio.gather(
        temperature_sensor([log_ch, alert_ch]),
        logger(log_ch),
        alerter(alert_ch),
    )
```

See `async_stream.py` for the complete runnable version.



### What Each Stage Absorbed

|                     | Subscription list   | Notification loop  | Concurrency |
|---------------------|---------------------|--------------------|-------------|
| Stage 1 (Java)      | Hand-coded          | Hand-coded         | Hand-coded  |
| Stage 2 (Python/JS) | Hand-coded          | Hand-coded         | Absent      |
| Stage 3 (asyncio)   | Framework (`Queue`) | Runtime (`gather`) | Runtime     |

Each layer down eliminates one responsibility from the application code.
By Stage 3, the Observer pattern is no longer visible as a named structure.
Its concerns - subscription, dispatch, ordering - are expressed through
language primitives (`async for`, `await`, `Queue`) and runtime scheduling.



### The Residual: Fan-Out Still Requires Wiring

Stage 3 does not make subscription disappear - it moves it.

A single-consumer async generator needs no wiring at all:

```python
async for temp in temperature_sensor():
    print(temp)
```

But fan-out to multiple independent consumers requires explicit channels.
The producer must know how many channels to write to, or a broker must
be introduced. In frameworks like RxJS or Kotlin Flow, this broker is
provided by the library:

```javascript
// RxJS - the observable handles fan-out; consumers just subscribe
const temps$ = new Observable(subscriber => {
    [22.1, 22.3, 23.5].forEach(t => subscriber.next(t));
    subscriber.complete();
});

temps$.subscribe(t => console.log(`log: ${t}`));
temps$.subscribe(t => { if (t > 23) console.log(`ALERT: ${t}`); });
```

Here the subscription list and dispatch loop exist inside the RxJS
runtime. The application code never sees them. This is the endpoint of
the evolution: the Observer pattern as infrastructure, not application logic.



### What This Demonstrates

The Observer arc is the most complete example of a pattern moving downward
through abstraction layers:

- In Stage 1, the pattern is the code.
- In Stage 2, the pattern is a convention over language primitives.
- In Stage 3, the pattern is the runtime.

What persists across all three stages is the underlying problem:
*components need to react to events produced by other components without
being tightly coupled to them.* The pattern did not solve a fundamental
problem differently. It identified a fundamental problem, then progressively
delegated its solution to lower layers as those layers became capable of
expressing it.

This is why the GoF book remains useful to read even in 2025: not as a
construction manual, but as a map of the recurring pressures that languages
and runtimes were eventually built to absorb.
