
## Availability

*This entry is an open exploration. A starting framework is provided below, but you are
expected to investigate, extend, and form your own understanding.*

Availability is the fraction of time a system is operational and able to serve its intended
purpose. It is often expressed as a percentage--"five nines" (99.999%) availability means
the system is down for no more than about 5 minutes per year. It sounds close to fault
tolerance and resilience, and it is related to both. But it is distinct in a way worth
understanding precisely.

- *Fault tolerance* asks: can the system survive a failure?
- *Resilience* asks: can the system degrade gracefully and recover?
- *Availability* asks: what fraction of time is the system actually usable?

A system can be fault-tolerant and still have low availability--if it survives failures by
taking 20 minutes to restart. A system can be resilient and still have low availability--if
it degrades to a state users consider unusable. Availability is the outcome metric; fault
tolerance and resilience are design strategies for achieving it.


### Starting Points for Exploration

*The mathematics of availability:*

For two independent components connected in series (both must work for the system to work):
```
A_system = A1 × A2
```
For two independent components in parallel (either can work for the system to work):
```
A_system = 1 - (1 - A1) × (1 - A2)
```

Explore: what does this imply for a system with ten components in series, each at 99.9%?
What does adding a parallel redundant path do to that number?

*Planned vs. unplanned downtime:*

Not all downtime is a failure. Deployments, maintenance windows, and database migrations take
systems offline deliberately. How do you account for planned downtime in availability calculations?
Should you? Does a user care whether downtime was planned?

*The CAP theorem:*

In a distributed system, you cannot simultaneously guarantee Consistency, Availability, and
Partition Tolerance when a network partition occurs. You must choose which two to preserve.
Availability is one of the three. When you choose it over consistency, what does the system
promise to users that it cannot also guarantee is correct?

*Availability at different layers:*

A service can be "available" (accepting requests) while depending on a database that is not.
Does availability apply to the service or to the system as a whole? How do you define the
boundary of what must be available?

*The nine nines:*

| Availability | Downtime per year |
|--------------|-------------------|
| 99%          | ~3.65 days        |
| 99.9%        | ~8.76 hours       |
| 99.99%       | ~52.6 minutes     |
| 99.999%      | ~5.26 minutes     |

What does it take to achieve each level? What changes in your architecture as you move from
99% to 99.9%? From 99.9% to 99.99%?


### Questions to Answer

1. What is the difference between availability and reliability? (Reliability is about
   correct behaviour; availability is about being operational. A system can be available
   but returning wrong answers.)
2. How do you measure availability in practice? What is the unit of measurement?
3. What is an SLA (Service Level Agreement) and what role does availability play in it?
4. What is the relationship between availability and cost? Can you always buy more availability?
5. What architectural decisions most improve availability? Which are most expensive?
6. Can a system have 100% availability? What would that require?

Write your answers. Discuss them with your peers. Then look at how real systems--cloud
providers, databases, operating systems--define and measure their availability guarantees.
