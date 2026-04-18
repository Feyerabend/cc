
## Observability

Observability is the property of a system that allows you to understand its internal state by
examining its external outputs. The term comes from control theory, where an observable system
is one whose internal state can be inferred from its outputs over time. In computing, it has
become a discipline in its own right: the practice of instrumenting systems so that they can
be interrogated, diagnosed, and understood without modifying them when something goes wrong.

The central insight is asymmetric: it is easy to build a system that works when everything is
normal. It is far harder to build a system you can understand when something unexpected happens.
An unobservable system fails silently, fails in ways you cannot diagnose, and produces failures
you cannot reproduce. An observable system fails in ways you can examine, trace, and eventually
fix--often before the failure affects users at all.

As systems grow in complexity--distributed across many services, machines, and teams--observability
becomes less a convenience and more a survival requirement.


### Observability vs. Monitoring

These terms are often used interchangeably but describe different stances.

*Monitoring* is the practice of watching known indicators for known problems. You define thresholds
in advance: alert if CPU exceeds 90%, alert if error rate exceeds 1%, alert if the queue depth
exceeds 10,000. Monitoring answers questions you thought to ask before the system was deployed.
It is effective for known failure modes.

*Observability* is the property that lets you answer questions you did not think to ask. When a
novel failure mode appears--one you did not anticipate--an observable system allows you to explore
its behaviour by querying its outputs. You did not know you would need to slice error rates by
customer region and request size simultaneously, but an observable system lets you do it on demand.

The distinction matters practically: a well-monitored but poorly observable system will alert you
that something is wrong but leave you unable to diagnose it. A well-observable system may not have
pre-configured alerts, but when something breaks, you can find out why.

In practice, good systems need both. Monitoring for the expected; observability for the unexpected.


### The Three Pillars

Observability in modern systems is typically built from three complementary signal types, each
offering a different view of system behaviour.

#### Metrics

Metrics are numerical measurements sampled over time--counters, gauges, and histograms. They are
cheap to produce, cheap to store (as aggregates), and fast to query. A counter might track the
total number of HTTP requests. A gauge might track current memory usage. A histogram might track
the distribution of request latencies.

The strength of metrics is breadth: you can track hundreds of indicators simultaneously and alert
on anomalies in near real-time. The weakness is depth: a metric that tells you latency is high
does not tell you *which* request was slow, *why* it was slow, or what was happening in the system
at the time. Metrics are excellent for *detecting* problems; they are often insufficient for
*diagnosing* them.

Key metric properties:
- *Cardinality:* the number of distinct label combinations. A metric labelled by user ID across
  millions of users has very high cardinality and can overwhelm a metrics store. Cardinality
  management is one of the central operational challenges of large-scale metric collection.
- *Resolution:* how frequently the metric is sampled. High resolution (1-second samples) captures
  short spikes; low resolution (1-minute aggregates) misses them. Resolution trades cost for fidelity.
- *Aggregation:* sums and averages are lossy. A 99th-percentile latency of 200 ms and an average of
  20 ms tell very different stories. Always prefer percentiles (p50, p95, p99, p999) over averages
  when latency is the concern.

#### Logs

Logs are time-stamped records of discrete events. An HTTP server emits a log line for each request.
A payment service emits a log line for each transaction. A database logs each slow query. Logs are
the most detailed signal: they capture the full context of individual events rather than aggregates.

A well-structured log line contains not just a message but enough context to reconstruct what was
happening: request ID, user ID, operation name, duration, outcome, and any relevant parameters.
Structured logging (JSON, key-value pairs) rather than free-text makes log lines queryable and
amenable to analysis.

The weakness of logs is volume. A high-traffic service can emit millions of log lines per second.
Storing, indexing, and searching that volume is expensive. Sampling strategies (log 1% of successful
requests, 100% of errors) reduce cost but introduce gaps. Log analysis tools (ELK stack, Loki,
Splunk) exist precisely to manage this at scale.

#### Traces

A distributed trace follows a single request as it moves through multiple services, recording
the timing and context of each step. Where a metric tells you "p99 latency is 500 ms" and a
log tells you "request X failed", a trace tells you "request X took 500 ms: 2 ms in the
gateway, 480 ms waiting for the user-service, 18 ms assembling the response--and the
user-service spent its 480 ms retrying a failed database query".

Traces are the highest-information signal for diagnosing latency problems and cascading failures
in distributed systems. Each unit of work in a trace is called a *span*. Spans form a tree: the
root span is the top-level request; child spans are the operations it triggered. Each span
records its start time, duration, service name, and any relevant attributes.

The cost of tracing is overhead: each span must be created, propagated through the call stack,
and exported to a collection backend. In high-throughput systems, tracing every request is
impractical; *sampling*--tracing a representative subset--is standard. The challenge is ensuring
that interesting requests (errors, slow outliers) are always traced, while routine requests are
sampled aggressively.


### Tail Latency and the Importance of Percentiles

A system that has a mean latency of 20 ms but a 99th-percentile latency of 500 ms is not a
fast system. Ten percent of users of a popular service hit the 99th percentile regularly.
The worst-performing percentiles--tail latency--are disproportionately what users experience
and what cascading failure looks like.

Observability must capture tail behaviour. A dashboard showing only averages is actively
misleading. Standard practice is to track at minimum p50, p95, p99, and p999 (the 99.9th
percentile). In systems where many services call each other (fan-out architectures), tail
latency compounds: if 100 downstream calls each have 1% probability of being slow, the
probability that at least one is slow is nearly 63%. The top-level request sees the maximum,
not the average.

This is why distributed tracing was invented: to find *which* of the 100 downstream calls
was the slow one in a given request.


### Observability in Practice

#### Instrumentation

Observability begins with instrumentation: adding code to the system that emits signals. A
service that emits no metrics, logs, or traces is a black box. Instrumentation frameworks
(OpenTelemetry, Prometheus client libraries, structured logging libraries) reduce the overhead
of adding signals.

Good instrumentation is:
- *Consistent:* every service uses the same naming conventions, the same label schemas, the
  same trace propagation headers. Inconsistency makes correlation across services impossible.
- *Proportional:* instrument what matters. Every HTTP endpoint, every database query, every
  external call. Not every line of business logic.
- *Low overhead:* instrumentation must not itself become the bottleneck. Metric recording,
  log formatting, and span creation should be microseconds, not milliseconds.

#### The Cost of Observability

Observability is not free. Metrics aggregation requires compute. Log storage requires disk.
Trace collection requires network and CPU. At scale, the infrastructure for observability can
rival the infrastructure for the product itself.

This cost is almost always worth paying. The alternative--debugging a production incident
on a system you cannot see into--costs orders of magnitude more in engineer time, customer
impact, and organisational stress. But the cost must be managed. Aggressive sampling, log
level controls, and metric cardinality limits are practical tools for keeping observability
affordable.

#### Alerting and On-Call

Observability signals feed alerting systems, which notify engineers when something requires
human attention. Good alerting is:
- *Actionable:* every alert should describe something an engineer can do.
- *Rare:* alert fatigue--too many alerts, most of which resolve themselves--causes engineers
  to ignore alerts. When the critical alert fires, nobody sees it.
- *Symptom-based rather than cause-based:* alert on "error rate is elevated" rather than
  "CPU is high", because high CPU that does not affect users does not require waking someone up.

#### Observability and Debugging

The primary use of observability is debugging production behaviour. The classic debugging
workflow--attach a debugger, inspect variables, step through code--is impossible in a distributed
production system. Observability replaces it: you reason about the system's behaviour by
correlating signals across time.

A practical workflow:
1. An alert fires: p99 latency of the checkout service has exceeded 1 second.
2. Metrics show the degradation began 12 minutes ago and correlates with a deployment.
3. Logs from the affected time window show a pattern of timeouts to the inventory service.
4. A trace from an affected request shows the checkout service waiting 950 ms for an inventory
   lookup that normally takes 10 ms.
5. Logs from the inventory service show it is in garbage collection for 30% of the time since
   the deployment increased its heap allocation.

Without observability, each of those steps would be a guess. With it, the diagnosis took minutes.


### Observability as a Design Discipline

Observable systems are not produced by adding monitoring after the fact. They are designed from
the start with the question: "when this fails in an unexpected way, what will I need to know?"

This means:
- Defining meaningful request IDs that propagate across all services and appear in all logs.
- Emitting latency histograms, not just counters, for every operation that can be slow.
- Logging errors with enough context to reproduce the failure without a debugger.
- Thinking about failure modes at design time and ensuring each mode is distinguishable
  from the outside.

The discipline connects directly to other systemic concepts: *complexity* makes systems harder
to understand without observation; *errors* and *resilience* require that failures be detectable
and diagnosable; *latency* problems are only visible if latency is measured at fine granularity;
*concurrency* bugs manifest as timing-dependent behaviour that only traces can reveal.

*You cannot improve what you cannot see.*
*You cannot debug what you cannot observe.*
*Observability is the precondition for everything else.*
