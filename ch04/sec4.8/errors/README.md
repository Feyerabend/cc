
## Errors ..

Errors are central to computing because virtually every computer system, program, or process operates
in an environment full of uncertainty. Inputs can be invalid, hardware can fail, networks can drop packets,
and users can behave unpredictably. Without robust error handling, even small issues can cascade into
system crashes, data corruption, or security vulnerabilities. Understanding and managing errors is
therefore foundational to designing reliable, maintainable, and safe software.


### Why errors matter

1. Reliability: Programs must continue to function correctly despite unexpected conditions. For example,
   a database should not lose data if the network temporarily fails.

2. Security: Unhandled errors can expose system vulnerabilities. Buffer overflows or invalid memory
   access often arise from poor error handling.

3. User experience: Clear error handling prevents frustration. Informing users about what went wrong,
   rather than crashing silently, improves usability.

4. Maintainability: Well-structured error handling makes it easier to trace, diagnose, and fix issues
   during development and maintenance.


### How errors occur

Errors can arise from multiple sources:
- Hardware failures: Disk errors, memory corruption, or CPU faults.
- Software bugs: Logical errors, incorrect assumptions, or coding mistakes.
- External factors: Network failures, incorrect input from users, or missing resources.
- Environment issues: OS-level constraints, concurrency conflicts, or resource limits.

General strategies for managing errors

1. Detection: Errors must be detected as soon as possible. This can include runtime checks, input
   validation, assertions, or monitoring system health.

2. Reporting: Once detected, the error should be logged or reported in a structured way, giving
   sufficient context for debugging.

3. Containment: Prevent an error from spreading or causing cascading failures. For example,
   isolating a failing module so the rest of the system can continue.

4. Recovery: Attempt to recover safely, such as retrying a failed operation, falling back to
   default behaviour, or rolling back transactions.

5. Failing gracefully: If recovery isn’t possible, the system should terminate in a controlled
   way, preserving data integrity and informing users.

Implementation patterns
- Exceptions and try/catch blocks: Common in high-level languages (Python, Java, C++), allowing structured handling of errors.
- Return codes and error values: Often used in C and system-level programming. Functions return codes indicating success or failure.
- Assertions and defensive programming: Validate assumptions to catch programming errors early.
- Logging and monitoring: Continuous insight into the system allows proactive handling and diagnostics.
- Redundancy and fault tolerance: Hardware or software redundancy can prevent errors from causing failures in critical systems.



### So .. the Ariane Rocket?

The Ariane 5 is a European expendable launch vehicle developed by the European Space Agency (ESA)
and Arianespace. Its first flight was on June 4, 1996, from the Guiana Space Centre in French Guiana.
The mission ended in failure just 37 seconds after lift-off.


#### What Happened?

The failure was traced back to the inertial reference system (IRS) software, which was largely
reused from the Ariane 4 program. Specifically:

1. Software Reuse: The Ariane 5 reused a floating-point conversion routine from Ariane 4 that
   converted a 64-bit floating-point number to a 16-bit signed integer.

2. Data Overflow: The value in Ariane 5 exceeded what could be represented in a 16-bit signed
   integer. This caused an arithmetic overflow.

3. Error Handling Failure: The software had an exception handler for the conversion error, but
  the handler disabled the inertial reference system instead of safely recovering or signalling the issue.

4. Cascade Effect: Once the IRS shut down, the control system received invalid data, leading to
   uncommanded trajectory deviations and ultimately the self-destruction of the rocket.

__Historical Significance__

1. Cost: The rocket and payload were lost, costing approximately $370 million USD.

2. Lessons in Error Handling:
- Assumptions Matter: Software that was safe for Ariane 4 failed when the physical conditions
  changed in Ariane 5. Assumptions must be verified for each new context.
- Exception Handling Strategy: The IRS software aborted on an exception that could have been
  safely caught. Error handling shouldn’t propagate failures unnecessarily.
- Testing Under Operational Conditions: The failure only occurred under flight conditions; the
  code had not been tested with Ariane 5’s higher horizontal velocity at lift-off.
- Redundancy and Recovery: Critical systems need robust fault-tolerant design. Here, both IRS
  units failed similarly because the same software was used in both.


__Broader Implications__

The Ariane 5 incident is a canonical example in software engineering and aerospace courses, illustrating:
- The dangers of blind code reuse.
- The need for proper validation of software assumptions.
- How minor software issues can escalate into catastrophic system failures.

The report by ESA afterwards became a reference for software safety standards in aerospace,
particularly the need to separate error detection from catastrophic system shutdowns.

```
Ariane 5 Flight Conditions
└─> Higher horizontal velocity than Ariane 4
      └─> Inertial Reference System (IRS) receives large velocity value
            └─> Floating-point to 16-bit integer conversion
                  └─> Arithmetic overflow occurs
                        └─> Exception triggered in IRS software
                              └─> IRS software shuts down both redundant IRS units
                                    └─> Flight control system receives invalid navigation data
                                          └─> Erroneous guidance commands issued
                                                └─> Rocket deviates from trajectory
                                                      └─> Self-destruction command triggered
                                                            └─> Catastrophic mission failure
```


### Conclusion

Errors are unavoidable in computing; they are a fundamental aspect of interacting with imperfect hardware,
software, and humans. The "why" of error handling is to maintain reliability, safety, and usability. The "how"
is a combination of detection, containment, recovery, and reporting, implemented through language constructs,
system design patterns, and operational safeguards. Effective error management transforms inevitable failures
from catastrophic events into manageable incidents.

Read more on [errors](./../../ch08/systemic/errors/).
