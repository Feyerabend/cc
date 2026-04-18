
## Exercise: From Security, State, and Interface to Authentication

*This is a student exercise. No guided walkthrough is provided.*

You have already worked through *Cryptography* (Security + Randomness + Complexity).
This combination uses a different set of forces to derive a related but distinct concept:

```
Security + State + Interface  ->  Authentication
```

### Your Task

Without being guided, derive why authentication must exist.

Start here:
- A system exposes an interface through which actors interact with it.
- The system maintains state that belongs to specific actors.
- The system must behave securely: only the right actor should reach the right state.

Ask yourself:
1. What is the difference between *identification* (who claims to be who)
   and *authentication* (proving that claim)?
2. Why is interface relevant? What happens when the interface has no concept
   of identity?
3. Why is state relevant? What would authentication protect if there were
   no state to protect?
4. What makes an authentication mechanism *secure*?
   What can go wrong if it is not?
5. How does the cryptography combination connect to this one?

Build a minimal system: a store of user data, an interface that exposes it,
and a mechanism that only allows the right actor through.
Start without authentication. Observe the vulnerability.
Add authentication. Observe what changes.

Then name what you built--and consider: what comes *after* authentication?
(That is, once the system knows *who* you are, how does it decide *what*
you are allowed to do?)
