
## Security and Programming

To start off, a small anecdote from years ago:

> I think it was around 1981. We were teenagers, maybe 16 or 17 years old, when we got the chance
> to do a school internship at a mainframe computer centre. It felt like a dream come true--finally,
> a chance to spend time around a real mainframe. The hum of technology, the blinking lights, the
> rows of tape drives. We were thrilled.
>
> Of course, we were just kids, so we were only allowed to do basic tasks. Things the operators
> normally handled: mounting and removing magnetic tapes, installing those heavy disk packs, or
> sending short operator messages to users waiting for their batch jobs.
>
> It was noisy--fans running constantly to cool down the machines--and the regular staff seemed
> to live off coffee: six, seven, even eight cups before lunch.
>
> But one thing stood out the most. *Security*. Or rather--the lack of it.
>
> The IBM 3033 mainframe, which processed massive national datasets, was housed in a lower-level
> server room. To get there, you simply took the elevator. And what was the access code to that
> floor? Yes. You guessed it: `3033`.
>
> Now, sure, most of the staff probably recognised each other. But people came and went. The high
> turnover, the constant background noise, the stress--it wouldn't have been hard for an outsider
> to slip in unnoticed.
>
> And here's the thing: that computer held Sweden's entire national vehicle registry. All of it.
> No guards, no ID checks, no logs--just a code and a lift and the sound of cooling fans drowning
> out any question of security.
>
> So security hasn't always been in focus. At this time they were more concerned about uptime, as
> some operators had their own pagers. Constantly accessible.
>
> What that experience revealed--beyond the lax physical security--was a deeper issue: how easily
> trust in technical infrastructure can be misplaced. And today, even as systems grow more complex,
> the story isn't all that different.

Security in computing is often imagined in terms of firewalls, passwords, and encryption. But beneath
these mechanisms lies a deeper foundation: the *code* itself. Most digital systems--whether web apps,
operating systems, IoT devices, or embedded controllers--are ultimately shaped by the programming
languages, tools, and practices used to build them. This makes programming not just a technical
activity, but a frontline concern in cybersecurity.


### Why Software Security Matters

When systems fail, they often do so because of flaws in code: a misplaced pointer, an unchecked input,
a flawed assumption about user behaviour or concurrency. In modern computing, most security
vulnerabilities originate from software bugs, not hardware failures or cryptographic breakthroughs.
These bugs, in turn, are shaped by language design, programmer skill, and development methodology.

Programming and security are intrinsically linked. Every programming decision--from memory allocation
to data validation--carries implicit security consequences. Unlike physical security systems where
defence can be layered externally, software security must often be built in, not bolted on.

Historically, the industry treated security as a reactive process: patch after breach. But as systems
have become more complex and interconnected, that model has failed. Today's approach emphasises
proactive security through language design, automated analysis, and secure coding principles.


### Programming Languages as Security Enablers or Risks

Some languages, like C and C++, give developers enormous power and low-level control--but at the
cost of manual memory management, unchecked buffer sizes, and undefined behaviour. These become fertile
ground for vulnerabilities like buffer overflows, use-after-free, integer underflows/overflows, and
race conditions.

Languages like Rust, Go, Ada/SPARK, and high-level managed environments like Java or TypeScript try
to constrain these risks through stronger type systems, memory safety guarantees, garbage collection,
or even formal verification. A language thus becomes not just a tool for expressing logic--but a
security framework, shaping what kinds of bugs are easy, hard, or impossible to write.


### Historical Evolution of Vulnerabilities and Defences

1. *1970s--1990s:* Early systems (UNIX, MS-DOS) lacked protections, leading to exploits like the
   *Morris Worm* (1988), which exploited buffer overflows.

2. *2000s:* Network exposure expanded attack surfaces (e.g., the *Code Red worm* targeting IIS).
   Microsoft's Secure Development Lifecycle (SDL) emerged.

3. *2010s:* High-impact flaws like *Heartbleed* (OpenSSL) and *Spectre/Meltdown* (CPU side-channels)
   drove adoption of static analysis and sandboxing.

4. *2020s+:* Shift toward memory-safe languages (Rust, Go) and formal verification. High-profile
   breaches (SolarWinds, Log4j) highlight supply-chain risks.

Many of the most devastating incidents trace directly back to coding errors: misused APIs, forgotten
input validation, unsafe default settings, failure to check edge cases. These aren't abstract bugs --
they become entry points for attackers, who exploit them to steal data, hijack systems, or install malware.


### Language-Level Security

* *Memory Safety:*
    * *C/C++:* Manual management risks buffer overflows, null pointers.
    * *Rust:* Ownership/borrowing system prevents data races and leaks at compile time.
    * *Go:* Garbage collection and bounds-checked slices mitigate runtime errors.
    * *Ada/SPARK:* Formal proofs ensure absence of runtime errors for critical systems.

* *Type Safety:* Languages like Haskell and TypeScript enforce data integrity, reducing runtime surprises.

* *Static Analysis:* Tools (e.g., Rust's borrow checker, Java annotations) catch vulnerabilities early.

Approximately *70% of vulnerabilities stem from memory safety issues*, emphasising the need for safer
languages and tools.


### Preventive Methods

1. *Input Validation and Sanitisation:* Whitelisting, parameterised queries, and encoding prevent
   injection attacks.

2. *Memory Safety Tools:* AddressSanitizer, Valgrind, and fuzzers (AFL) detect runtime issues.

3. *Static and Dynamic Analysis:* SAST (code scanning) and DAST (runtime testing) complement each other.

4. *Least Privilege:* Restrict permissions for users, processes, and APIs.

5. *Reproducible Builds and Immutable Infrastructure:* Ensure integrity and reduce supply-chain risks.


### System-Level Defences

* *Compiler Protections:* ASLR, stack canaries, and DEP/NX hinder exploitation.

* *Runtime Isolation:* Sandboxing (WebAssembly), Linux namespaces, and CHERI's hardware-enforced
  capabilities.

* *Formal Verification:* Mathematically proven correctness (e.g., seL4 kernel, Amazon's s2n TLS).


### Human and Organisational Factors

Security is not just about code or compilers--it is also about the practices, assumptions, and
incentives of the people building systems. Static analysers and memory-safe languages are only effective
if integrated into workflows, code reviews, and cultural expectations.

* *Code Review and Threat Modelling:* STRIDE (threat identification) and DREAD (risk prioritisation)
  frameworks.

* *Secure Defaults:* HTTPS enforcement, least-privilege APIs.

* *Shift-Left Security:* Integrate security early in development via DevSecOps, automated testing, and
  training. This means building in security at the design, coding, and build stages rather than waiting
  until deployment or post-release, catching vulnerabilities sooner and reducing the cost of fixing them.


### Future Trends

1. *Memory-Safe Languages:* Rust adoption in critical systems (Windows, Linux) reduces vulnerabilities.

2. *Hardware-Assisted Security:* CHERI architecture enforces memory safety at the hardware level.

3. *Formal Methods:* AI-driven tools may lower the cost of formal verification.

4. *Security by Design:* Proactive practices replace reactive fixes, emphasising resilience from inception.

Secure programming demands a *multi-layered approach*: technical (memory-safe languages, static analysis,
and system-level protections), process (threat modelling, reproducible builds, and immutable
infrastructure), and human (training, code reviews, and a security-first culture). No single solution
suffices; security is an ongoing process requiring adaptation to evolving threats.

