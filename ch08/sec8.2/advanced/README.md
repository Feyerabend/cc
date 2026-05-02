
## Advanced Security – Designing Before You Code

The examples in [../basic/code/](./../basic/code/) show individual vulnerability
classes in isolation. This section steps back and asks a harder question:
*how do you build a system that is unlikely to have those vulnerabilities in the first place?*
Patching bugs one at a time is a losing strategy. The attackers only need
to find one; the defenders have to close every one. The asymmetry is only
addressed by designing security in from the start.



### 1. Why "Bolt-On" Security Fails

Security added after the fact almost always fails to cover the whole system.
The canonical reason is that security properties are *systemic*--they depend
on invariants that hold across component boundaries, across the call stack,
and across time. You cannot retrofit a property that was never expressed
in the design.

A concrete example: you cannot add authentication to a system where the
internal services were designed to trust one another unconditionally.
Adding a token check at the API gateway is not authentication if internal
services remain reachable from the network without any credential.
The vulnerability is architectural, not a missing function call.

This is why the question "is feature X secure?" is almost always wrong.
The right question is "under what threat model does component X maintain
what invariants?"



### 2. Threat Modeling

Threat modeling is the practice of answering *what can go wrong* before writing
a line of code. It produces a structured description of assets, adversaries,
and the paths by which adversaries can reach assets. Every serious mitigation
decision traces back to a threat model.

#### 2.1 STRIDE

Microsoft's STRIDE taxonomy names six threat categories. Applying them
systematically to a design forces you to think about each class of attack,
not just the ones that come to mind spontaneously.

| Letter | Threat                 | Violated property | Example                            |
|--------|------------------------|-------------------|------------------------------------|
| S      | Spoofing               | Authentication    | Claiming another user's identity   |
| T      | Tampering              | Integrity         | Modifying a request in transit     |
| R      | Repudiation            | Non-repudiation   | Denying an action you took         |
| I      | Information disclosure | Confidentiality   | Reading another user's data        |
| D      | Denial of service      | Availability      | Exhausting server memory           |
| E      | Elevation of privilege | Authorization     | Acting as admin without permission |

Apply STRIDE to every component in your data-flow diagram. For each combination
of (component, threat class), ask:
does a control exist?
Is it sufficient?
Is it tested?

#### 2.2 Attack Trees

An attack tree roots at an attacker goal ("exfiltrate the database") and branches
into sub-goals the attacker must achieve to reach it. Each leaf is an atomic action.
The structure reveals which mitigations are most valuable: a mitigation that cuts
every path to the root is more valuable than one that cuts a single leaf.

```
Goal: read another user's private messages
├── Exploit SQL injection in the message query     --> parameterized queries
├── Steal session token
│   ├── XSS that reads document.cookie             --> HttpOnly flag, CSP
│   └── Network interception                       --> TLS, HSTS
└── Compromise the server process
    ├── RCE via dependency CVE                     --> dependency pinning, SCA
    └── RCE via file upload + path traversal       --> allowlist extensions, jail
```

Reading the tree, you can see that TLS and HttpOnly are complementary mitigations
for the same sub-goal, and that parameterised queries are necessary to close the
SQL path entirely. A denylist on filenames is a *weak* mitigation for the upload
path--the allowlist + realpath check in `input_validation.py` is the strong form.

#### 2.3 Data-Flow Diagrams and Trust Boundaries

Draw a DFD (data-flow diagram) for your system at the component level. Every arrow
crossing a *trust boundary*--a line between zones with different privilege
levels--is a potential vulnerability. Inputs crossing a trust boundary should be
validated; outputs crossing one in the other direction should be filtered to
prevent data leakage.

Common trust boundaries:
internet --> load balancer,
load balancer --> API service,
API service --> database,
API service --> internal microservice,
user space --> kernel,
browser --> web worker.
Each one is a place where an attacker operating in the less-trusted zone
attempts to influence behaviour in the more-trusted zone.



### 3. Security Design Principles

These are the principles that recur throughout secure systems design.
They are not rules that prevent specific bugs; they are structural
properties that make bugs less likely and less exploitable.

#### Least Privilege

Every component should operate with the minimum capabilities required
to do its job, and no more. A web server process that reads a database
should not be able to drop tables. A background job that sends email
should not have network access to the payment service.
A user who can view reports should not be able to modify them.

Least privilege limits the *blast radius* of a compromise. If the web
server process is hijacked via an RCE, an attacker operating as that
process inherits its capabilities--nothing more. The principle does
not prevent the compromise; it limits what the attacker can do after it.

In practice: run services as dedicated low-privilege users, use read-only
database credentials where writes are not needed, restrict filesystem access
with chroot or namespaces, use seccomp to limit the syscalls a process
can make, apply IAM policies at the resource level rather than the role level.

#### Defence in Depth

No single control is assumed to be sufficient. Multiple independent controls
are layered so that bypassing one does not give an attacker what they want.
The word *independent* is critical--if two controls share the same failure
mode (both depend on the same key, or both are bypassed by the same privilege
level), they are not independent.

The path-traversal defence in `input_validation.py` has two independent layers:
the allowlist regex rejects anything that doesn't look like a valid filename,
and the realpath comparison catches anything that slips through (including
symlinks, case normalization, null bytes in some systems).
Either check alone is weaker than both together.

#### Fail-Safe Defaults

The default result of any decision should be *deny*. A whitelist of permitted actions is
safer than a blacklist of forbidden ones, because new cases default to denied rather than
permitted. An access-control check that returns `True` on any error is catastrophically
unsafe; one that returns `False` on any error is correct.

The `read_file_bad` function in `input_validation.py` is a denylist: it blocks known-bad
strings but permits everything else. The `read_file_good` function allowlists the structure
of valid filenames and denies everything else--new encodings and bypass techniques default
to rejected.

#### Economy of Mechanism (Simplicity)

Security mechanisms should be as simple as possible. Complex systems have more paths through
them; more paths means more untested combinations of state; more untested combinations means
more vulnerabilities. If you cannot explain how a security mechanism works to a colleague in
five minutes, it is probably too complex to be trustworthy.

This principle argues against custom cryptography (use a vetted library), custom authentication
(use a standard protocol), and complex access-control logic (push it into a dedicated policy
engine). It also argues against large, long-lived codebases where security-critical code is
spread across many files.

#### Complete Mediation

Every access to every resource must be checked for authorization, every time. Caching the result
of an authorization check (and not re-checking when the underlying policy changes) violates this
principle. So does checking authorization at the API layer but not at the database query layer.

Complete mediation is what makes confused-deputy vulnerabilities possible when it is *absent*:
a higher-privilege process performs an action on behalf of a lower-privilege caller without
re-checking whether the caller has the right to request it.

#### Separation of Privilege

A capability should require more than one independent condition to be exercised. Two-factor
authentication is the obvious example: a stolen password alone does not grant access. A deploy
key that requires both a signed commit and a CI/CD approval gate is another.

Separation of privilege also applies to code structure: a function that both parses input and
executes a privileged action is harder to audit than two functions with a clear boundary between them.

#### Zero Trust

The traditional network-perimeter model assumed that traffic inside the network was trustworthy.
Zero trust rejects that assumption: every request is authenticated and authorized regardless of
where it originates. Internal services authenticate to one another with short-lived certificates
or tokens; no service is trusted merely because it shares a VLAN.

Zero trust is a response to the observation that perimeters routinely fail--through phishing,
through VPN vulnerabilities, through supply chain compromise--and that "inside the perimeter"
therefore tells you nothing about the trustworthiness of a request.



### 4. Memory Safety in Depth

The examples in `../basic/code/bof.c` and `../basic/code/intof.c` show the surface form of
memory bugs. The deeper issue is that C and C++ give the programmer direct control over memory
lifetime, and lifetime mistakes have security consequences that go beyond crashes.

#### Use-After-Free (`code/uaf.c`)

When a heap allocation is freed, the allocator may immediately reuse that memory for a subsequent
allocation. If a stale pointer to the freed object remains in scope, reading through it returns
whatever the new allocation wrote, and writing through it corrupts the new allocation. If the
new allocation contains a function pointer (vtable, callback), an attacker who controls the
contents of the new allocation can redirect execution.

Use-after-free is one of the most exploited vulnerability classes in browsers and operating
system kernels. The mitigation in `uaf.c`--nulling the pointer after free--turns silent memory
corruption into a clean crash. For C++ code, `std::unique_ptr` and `std::shared_ptr` make this automatic.

The stronger answer is a memory-safe language. Rust's borrow checker makes use-after-free a
compile-time error: a reference cannot outlive the value it refers to. Android, Linux kernel
modules, and Chrome are progressively migrating security-critical components to Rust for this reason.

#### Heap Metadata Attacks

Modern allocators maintain metadata (free lists, size fields, chunk headers) adjacent to user
allocations. A heap overflow that overwrites metadata can corrupt the allocator's internal state
and eventually be parlayed into arbitrary write. Allocator hardening (guard pages, randomised
free lists, out-of-band metadata) raises the bar but does not eliminate the class.

The implication for design: bounds-check every write before it happens. Do not rely on the
allocator catching the overflow.

#### Compiler and OS Mitigations

These are useful layers in the defence-in-depth stack, but they are mitigations, not fixes.

| Mitigation                           | What it does                                                         | What it does not do                                           |
|--------------------------------------|----------------------------------------------------------------------|---------------------------------------------------------------|
| Stack canaries (`-fstack-protector`) | Detects stack overflows before return                                | Stops only simple overflows; does not prevent heap corruption |
| ASLR                                 | Randomises load addresses, making ROP gadget addresses unpredictable | Does not help if an info-leak reveals the base address first  |
| NX/W^X                               | Marks memory as either writable or executable, not both              | Does not prevent return-oriented programming (ROP)            |
| CFI (Control-Flow Integrity)         | Restricts valid indirect call targets                                | Coarse-grained CFI still permits large gadget sets            |
| SafeStack                            | Separates control data from data on the stack                        | Per-compiler extension; not universal                         |

The mitigations interact: ASLR is significantly weakened without CFI, because an
info-leak can defeat ASLR and then ROP can bypass NX. A layered configuration
is stronger than any individual flag.



### 5. Cryptographic Design

Getting cryptography wrong is easy. Using a well-reviewed library correctly
is hard in a different way--it requires understanding what the library actually
guarantees, and what it does not.

#### Authenticated Encryption

Encryption without authentication is almost always wrong. A ciphertext produced
by AES-CBC without a MAC can be modified by an attacker who does not know the
key but knows something about the plaintext structure (padding oracle attacks,
bit-flipping attacks). The correct primitive for most use cases is *AES-GCM*
or *ChaCha20-Poly1305*: both provide confidentiality and authenticity in one operation.

```
AES-CBC + HMAC (encrypt-then-MAC)  <-- correct but easy to get wrong
AES-GCM                            <-- correct; prefer this
AES-CBC alone                      <-- broken for most purposes
```

Never implement encrypt-then-MAC yourself unless you have a specific reason
to avoid AEAD--the composition has subtle requirements (MAC covers the IV,
MAC is verified before decryption) that are easy to get wrong.

#### Nonce Reuse

AES-GCM requires that the nonce (IV) never be reused with the same key.
A single nonce reuse leaks the authentication key and potentially the plaintext.
If the nonce is a counter, persist the counter across restarts. If the nonce
is random, use 96 bits from a CSPRNG--the collision probability for 2³²
messages is then below 2⁻³².

#### Key Derivation

Raw passwords must never be used as encryption keys. Even if the password is strong,
hashing it with SHA-256 does not produce a key suitable for AES--the entropy
is concentrated in a small subset of 256-bit strings. Use a proper KDF:

- *PBKDF2*--widely available, but parallelisable on GPU; prefer scrypt or Argon2 for new systems.
- *scrypt*--memory-hard; forces GPU attackers to use DRAM bandwidth, not just compute.
- *Argon2id*--current recommendation; resists both time-memory tradeoff and side-channel attacks.

`code/password_hashing.py` shows the progression from plain SHA-256 through salted SHA-256 to scrypt.

#### HMAC vs. Plain Hash (`code/hmac_vs_hash.py`)

A plain hash of `(key || message)` is *not* a MAC for SHA-2 variants--it is vulnerable
to length-extension attacks. HMAC wraps the key into both the inner and outer hash in
a way that closes this attack. Use `hmac.new` or `HMAC` from a vetted library;
do not construct the envelope manually.

#### Algorithm Agility

Design key-management systems so that the algorithm can be changed without a full migration.
Store algorithm identifiers alongside ciphertext and derived keys (a version byte,
or a structured header). This makes it possible to migrate from AES-128-GCM to AES-256-GCM,
or from SHA-256 to SHA-3, without breaking existing data.



### 6. Concurrency and TOCTOU

Race conditions in security-sensitive code are subtle because the failure mode depends
on timing that is not visible in the code. The most common form is *time-of-check time-of-use (TOCTOU)*:
a condition is checked, then time passes, then an action is taken based on the result
of the check--but the condition may have changed between the check and the action.

`code/toctou.c` shows the classic form: `access()` checks whether a path is readable,
but `fopen()` opens whatever the path now points to. An attacker who can replace the
file with a symlink in the window between the two calls reads an arbitrary file with
the process's elevated privileges.

The fix is to *open first, check later*: open the file descriptor (binding it to a
specific inode), then call `fstat()` on the descriptor. The descriptor is immune to
path swaps. `O_NOFOLLOW` prevents the open itself from following a symlink.

The same pattern appears in database transactions: checking a balance, then debiting,
is vulnerable to a concurrent debit that reduces the balance between the check and
the debit. The fix is to perform the check and the debit atomically--either in a single
`UPDATE ... WHERE balance >= amount` statement, or under a row-level lock held for
the duration of both operations.



### 7. Input Validation Architecture

Input validation is not a single check at the entry point. It is a strategy that
spans the full depth of the system.

#### Allowlisting vs. Denylisting

A denylist blocks known-bad inputs and permits everything else. It requires the
list to be complete--any encoding, character class, or bypass not on the list is
permitted. Completeness is impossible to guarantee. A new encoding (Punycode,
overlong UTF-8 sequences, Unicode normalisation forms) may bypass every check on the list.

An allowlist specifies exactly what is permitted and denies everything else. New
encodings and bypass techniques default to rejected. Allowlists are harder to write
(you must know what valid input looks like) but structurally sound.

`code/input_validation.py` demonstrates the difference for path handling. The denylist
version is bypassed by any encoding of `..` not in the list; the allowlist version
is bypassed only if the allowable characters somehow produce a path-traversal after
`realpath` resolution--which the suffix check closes.

#### Parser Differentials

A parser differential occurs when two components parse the same input differently.
An attacker crafts input that is interpreted benignly by one component (a WAF, a filter,
a sanitizer) but maliciously by another (the application logic, the database).
This is the basis for many WAF bypasses and for HTTP request smuggling.

The implication: do not sanitize input at one layer and trust the sanitized form
at another layer that uses a different parser. Validate as close to the point of
use as possible, using the same parser the consuming component will use.

#### Canonical Form

Always validate input in its canonical (fully decoded, fully normalised) form.
Validate the URL-decoded form of a URL path, not the raw form. Validate the Unicode NFC
or NFKC form of a string, not a random normalisation. Operating on non-canonical
forms creates opportunities for bypasses that look different before and after normalisation.



### 8. Error Handling and Information Leakage

Error messages are a channel. The information they carry (stack traces,
SQL error text, internal file paths, library versions) helps an attacker
understand the system's structure and refine their approach.

*For external-facing errors:* return a generic message with a correlation ID.
Log the full detail internally, keyed by the correlation ID. The user gets
enough to file a support ticket; the attacker gets nothing useful.

*For internal-facing errors:* fail explicitly, not silently. A function that
encounters an unexpected state should return an error that propagates up,
not a default value that allows processing to continue on incorrect assumptions.
Silent failures are the hardest category of security bug to detect.

*Do not log secrets.* Authorization headers, session tokens, passwords,
private keys, and personal data should never appear in log files.
Structured logging libraries (Python's `logging`, Java's `logback`) make it
straightforward to tag fields as sensitive and suppress them in certain
outputs. Review log ingestion pipelines periodically to confirm that
tagged fields are not inadvertently persisted.



### 9. Dependency and Supply Chain Security

A modern application has hundreds of transitive dependencies. Each one
is a potential attack surface--a dependency can be hijacked (typosquatting,
account takeover), maliciously updated, or abandoned and allowed to
accumulate unfixed CVEs.

*Pin versions.* Lock files (`requirements.txt`, `package-lock.json`,
`Cargo.lock`) record exact versions of every transitive dependency.
Without pinning, a `pip install` a week later may pull a different
(potentially compromised) version.

*Software Composition Analysis (SCA).* Tools like `pip-audit`, `npm audit`,
`cargo audit`, and GitHub Dependabot scan lock files against vulnerability
databases and alert when a pinned version has a known CVE.

*Verify provenance.* SLSA (Supply-chain Levels for Software Artifacts)
is a framework for verifying that a build artifact was produced by the
expected build process from the expected source. Signed release artifacts
(Sigstore, PGP) let you confirm that a downloaded package was produced
by the maintainer, not a third party.

**Minimal dependencies.** Every dependency is a trust decision. A dependency
with a large transitive graph (hundreds of packages) multiplies the attack
surface. Prefer narrow, well-audited dependencies; avoid importing a large
framework to use one function.



### 10. Security Testing

Testing for security is structurally different from functional testing.
Functional testing verifies that the code does what it is supposed to do.
Security testing looks for inputs that cause the code to do things it is
*not* supposed to do. The space of invalid inputs is large, and many
security bugs manifest only at boundaries that functional tests never reach.

#### Static Analysis (SAST)

Static analysis tools examine source code without running it. They find
patterns that are often indicative of bugs: format string arguments that
are not literals, calls to dangerous functions (`gets`, `strcpy`, `system`),
unchecked return values from security-sensitive functions.

Useful tools: `clang-tidy`, `cppcheck` (C/C++), `semgrep` (language-agnostic
pattern rules), `bandit` (Python), `cargo-clippy` (Rust). Configure them in
CI so that new violations block the merge rather than accumulating.

#### Fuzzing

A fuzzer generates large volumes of malformed input and monitors the target
for crashes, assertion failures, or sanitizer reports. Coverage-guided fuzzers
(libFuzzer, AFL++) instrument the binary to track which code paths each input
exercises and mutate inputs specifically to reach new paths. This is how many
of the most severe real-world memory corruption bugs are found.

For parsers, protocol implementations, and anything that processes untrusted
bytes, fuzzing is more productive than manual review. The barrier to entry is
low: wrap the parsing function in a `LLVMFuzzerTestOneInput` harness, compile
with `-fsanitize=address,fuzzer`, and run.

#### Dynamic Analysis (DAST)

DAST tools probe a running application from the outside, injecting payloads and
observing responses. OWASP ZAP and Burp Suite automate detection of XSS, SQL injection,
path traversal, and common misconfigurations. They are most effective when run
against a test environment that mirrors production.

#### Penetration Testing

Manual penetration testing by a skilled adversary finds vulnerabilities that automated
tools miss--business logic flaws, authentication bypasses, trust boundary violations,
and chained exploits that require understanding the system end-to-end. Schedule a
pentest before major releases and after significant architectural changes,
not as a one-time event.



### 11. The Security Development Lifecycle (SDL)

The SDL integrates security activities into every phase of development.
The key insight is that the cost of fixing a security issue grows by roughly
an order of magnitude at each phase: a design flaw fixed in the design review
costs 10× less than the same flaw found in code review, which costs 10×
less than one found in testing, which costs 10× less than one found in production.

| Phase          | Security activity                                                                       |
|----------------|-----------------------------------------------------------------------------------------|
| Requirements   | Identify security requirements; write abuse cases alongside use cases                   |
| Design         | Threat model; define trust boundaries; identify required security controls              |
| Implementation | Enforce coding standards; use vetted libraries; run SAST in CI                          |
| Testing        | Fuzz parsers; run DAST on staging; review auth and authorization flows manually         |
| Release        | Sign artifacts; verify dependencies; update the threat model                            |
| Maintenance    | Monitor CVEs for dependencies; triage vulnerability reports; post-mortems for incidents |

The threat model produced in the design phase is a living document.
It should be updated whenever the architecture changes, not left as a snapshot from the original design.



### Code Examples in This Folder

| File                       | Concept demonstrated                                                           |
|----------------------------|--------------------------------------------------------------------------------|
| `code/toctou.c`            | TOCTOU race: `access()`+`fopen()` vs. `open(O_NOFOLLOW)`+`fstat()`             |
| `code/uaf.c`               | Use-after-free: stale pointer vs. null-after-free                              |
| `code/hmac_vs_hash.py`     | HMAC vs. plain hash; length-extension attack; constant-time comparison         |
| `code/password_hashing.py` | SHA-256 --> salted SHA-256 --> scrypt; why fast hashes are wrong for passwords |
| `code/input_validation.py` | Denylist path traversal vs. allowlist + realpath confinement                   |



### Summary

The central insight behind all of these principles is that security is not a
feature--it is a property of a system under a threat model. Features can be added;
properties must be designed in. Every one of the techniques in this section
is a way of making the threat model explicit, verifying that controls exist
for each threat, and ensuring that the controls are independent enough that
a single failure does not collapse the whole stack.

The most valuable thing a developer can do before writing a line of security-sensitive
code is to write down, precisely, what the adversary is assumed to be able to do
and what the system must prevent. That document is the threat model. Every design
decision, every choice of primitive, every layer of validation traces back to it.
