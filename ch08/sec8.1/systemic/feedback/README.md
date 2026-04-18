
## Feedback

Feedback is the process by which a system uses information about its own output to adjust its
future behaviour. It is one of the most pervasive and powerful principles in engineering, appearing
in contexts as varied as the thermostat on a wall, the congestion control algorithm in TCP, the
frequency scaling logic in a modern CPU, and the garbage collector in a managed runtime. In each
case, the same structure is present: the system senses its current state, compares it to a desired
state, and acts to reduce the difference.

Without feedback, systems must operate open-loop: they act based on a fixed plan, with no knowledge
of whether the plan is working. Open-loop systems are brittle--any deviation from assumed conditions
produces uncorrected errors. Feedback makes systems adaptive, allowing them to maintain desired
behaviour in the presence of uncertainty, variation, and change. It is, in a precise sense, the
mechanism by which systems become self-regulating.


### The Feedback Loop

Every feedback system has the same core structure:

1. *Sense:* Measure some aspect of the system's current state or output.
2. *Compare:* Evaluate the measurement against a target or reference value.
3. *Act:* Apply a corrective action proportional to the difference (the *error*).
4. *Wait:* Allow time for the action to take effect before sensing again.

This loop repeats continuously. The *control signal* is the output of the comparison step.
The *actuator* is the component that carries out the corrective action. The *plant* is the
system being controlled.

The crucial property is the direction of the feedback. *Negative feedback* opposes deviations:
if the system output is too high, the control signal reduces it; if too low, it increases it.
Negative feedback produces stability--it pulls the system toward the target. *Positive feedback*
amplifies deviations: if the system output is too high, the control signal increases it further.
Positive feedback produces instability, runaway growth, or collapse. Almost all useful control
systems use negative feedback.


### Feedback in Computing Systems

#### TCP Congestion Control

TCP congestion control is one of the most important and elegant applications of feedback in
computing. The problem: a sender sends data over a network whose capacity is unknown and variable.
If it sends too fast, packets are dropped, and retransmissions waste bandwidth. If it sends too
slowly, it wastes available capacity.

TCP uses the network itself as the sensor. When a packet is dropped (detected via timeout or
duplicate acknowledgements), the sender infers congestion and *reduces* its sending rate--negative
feedback from the implicit signal of a dropped packet. When acknowledgements arrive promptly, it
infers spare capacity and *increases* its sending rate. The result is a self-tuning system that
probes available bandwidth continuously and backs off when it finds the limit.

Different TCP congestion control variants (Reno, CUBIC, BBR) differ in how they interpret
signals and how aggressively they probe--but all are feedback control loops with the same
structure. The internet's stability under varying load depends on millions of TCP connections
simultaneously running these loops and collectively reaching an equilibrium.

#### CPU Frequency Scaling (DVFS)

Dynamic Voltage and Frequency Scaling (DVFS) is a feedback mechanism that adjusts CPU clock
speed and voltage in response to workload demand and thermal conditions.

Sensors: CPU utilisation, temperature, battery level, power consumption.
Target: maintain performance within thermal and power envelopes.
Actuator: the clock frequency and supply voltage of each CPU core.

When a CPU core is at 100% utilisation for several milliseconds, the governor increases its
frequency, providing more throughput at the cost of higher power. When the core is idle, it
reduces frequency, saving energy. When temperature exceeds a threshold, it reduces frequency
regardless of utilisation--thermal throttling--to prevent hardware damage.

Modern CPUs have multiple feedback loops operating simultaneously at different timescales:
a fast loop for immediate thermal protection (microseconds), a medium loop for
performance-per-watt optimisation (milliseconds), and a slow loop for sustained workload
characterisation (seconds). Each loop corrects for different sources of disturbance.

#### Garbage Collection

A garbage collector must balance competing goals: collect unused memory frequently enough that
the programme does not run out of heap space, but infrequently enough that collection pauses do
not dominate execution time. This is a feedback problem.

The JVM's G1 garbage collector, for example, uses feedback to meet a user-specified pause time
target. It observes how long recent collection pauses took, models the relationship between
collection work and pause duration, and adjusts how much work it schedules per collection to
stay within the target. If recent pauses have been short, it schedules more work per cycle. If
pauses have been long, it schedules less, accepting slower collection to meet the latency target.

This is negative feedback: long pauses --> reduce work per cycle --> shorter pauses. The system
continuously adapts to the actual behaviour of the heap rather than relying on fixed parameters.

#### Backpressure in Streaming Systems

In a data processing pipeline, a slow consumer can be overwhelmed by a fast producer. Without
feedback, the producer continues at its natural rate, the consumer's buffer fills, and eventually
data is lost or the system crashes.

Backpressure is feedback from consumer to producer: "I am falling behind; slow down." In reactive
streaming systems (Reactive Streams, Akka Streams, Go channels), backpressure is a first-class
mechanism. The consumer signals demand (how many items it can accept), and the producer sends no
more than demanded. When the consumer is slow, it signals low demand, and the producer slows.
When the consumer recovers, it signals more demand, and the producer speeds up.

Without this feedback, a streaming pipeline can appear to work under normal conditions but fail
catastrophically under any sustained load imbalance.

#### Circuit Breakers

A circuit breaker is a feedback mechanism for managing dependencies between services. When a
service calls a dependency that is slow or failing, the calls pile up, consuming threads and
connections, and the calling service eventually fails too--cascading failure.

A circuit breaker monitors the outcome of calls to the dependency. When the error rate or
latency exceeds a threshold, it *opens*: subsequent calls are immediately rejected with a
failure, without attempting the dependency. After a timeout, it *half-opens*: it allows a
single test call through to check whether the dependency has recovered. If it succeeds, the
circuit closes and normal operation resumes. If it fails, the circuit stays open.

The feedback signal is the health of the dependency. The actuator is the circuit state.
The target is a functioning service. The loop allows the calling service to degrade gracefully
and recover automatically without human intervention.

#### Load Balancers and Auto-Scaling

A load balancer that distributes traffic across servers based on their current queue depth is
a feedback system: it senses server load, compares it against balanced distribution, and adjusts
routing to reduce the imbalance.

Auto-scaling goes further: when the load across all servers exceeds a threshold, it provisions
additional instances; when load drops, it removes them. The feedback loop operates at a longer
timescale (provisioning takes seconds to minutes) and must avoid oscillation--rapidly adding and
removing instances in response to brief spikes. Hysteresis (requiring the condition to persist
for a period before acting) is a common technique for damping oscillations in slow feedback loops.


### Stability, Oscillation, and Overshoot

Feedback is powerful but not automatically stable. A poorly tuned feedback loop can oscillate
(continuously overshooting and undershooting the target), diverge (growing corrections that
make the error larger), or respond too slowly to be useful.

Three classic failure modes:

*Overshoot:* the corrective action is too strong, pushing the system past the target in the
opposite direction. The next correction overshoots in return, and the system oscillates around
the target rather than settling at it. TCP's early congestion control algorithms had this
problem: cutting the window in half on congestion sometimes produced throughput oscillations.

*Oscillation:* sustained overshoot. The system never converges. In distributed systems, this
can appear as coordinated bursts of traffic: all clients back off simultaneously, then all
retry simultaneously, then all back off again. Adding random jitter to retry intervals is
a practical remedy--it breaks the synchronisation that drives collective oscillation.

*Sluggishness:* the corrective action is too weak or too delayed. The system is slow to respond
to disturbances. A thermostat that only updates temperature readings every 10 minutes will
allow significant temperature excursion before responding.

The PID controller (Proportional-Integral-Derivative) is the classical tool for tuning feedback
loops in physical control systems. Its three terms address different aspects:
- *Proportional:* correct in proportion to the current error.
- *Integral:* correct for accumulated past error (eliminates steady-state offset).
- *Derivative:* correct based on the rate of change of error (damps oscillation).

Computing systems rarely use PID explicitly, but the same intuitions apply: a feedback loop that
responds only to the current error (proportional), ignores history, and does not anticipate
rate-of-change will often oscillate or respond sluggishly.


### Feedback and System Design

Recognising feedback loops in the systems you build is a design skill of considerable value.
Systems that lack negative feedback loops tend to be brittle: they work at the operating point
they were designed for and fail outside it. Systems with well-designed feedback loops are
self-regulating: they maintain acceptable behaviour across a range of conditions.

Questions to ask when designing a system component:
- What can go wrong with this component's output?
- How will the system know that something has gone wrong?
- What mechanism will act to correct it?
- How quickly must the correction happen?
- Could the correction itself make things worse?

Feedback does not eliminate the need for careful design--a poorly designed feedback loop is worse
than none, because it introduces dynamic instability. But the *absence* of feedback in a component
that operates in a variable environment is almost always a design gap waiting to manifest as a
production incident.

*A system that cannot sense its own behaviour cannot correct it.*
*Feedback is how systems remain functional when the world does not cooperate.*
