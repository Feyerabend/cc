
## Common Security Vulnerabilities

A collection of minimal C and Python examples demonstrating eight recurring
vulnerability classes, each shown in its unsafe form alongside the corrected
version. The goal is to make the mistake and the fix visible in the same file.


### File Index

| File          | Language | Vulnerability class         |
|---------------|----------|-----------------------------|
| `bof.c`       | C        | Buffer overflow             |
| `cmdinj.c`    | C        | Command injection           |
| `intof.c`     | C        | Integer overflow            |
| `timing.c`    | C        | Timing side-channel         |
| `fmtstr.c`    | C        | Format-string injection     |
| `sha256.c`    | C        | Hashing via OpenSSL EVP     |
| `pycrypto.py` | Python   | Secure randomness & hashing |
| `sqlinj.py`   | Python   | SQL injection               |



### Buffer Overflow (`bof.c`)

`strcpy` copies bytes until it hits a null terminator with no regard for how
large the destination buffer is. An attacker who controls `name` can write
past the end of `buf[64]`, overwriting the saved return address on the stack
and redirecting execution to arbitrary code. The fix is `snprintf`, which
accepts the buffer's size as its second argument and truncates rather than
overflows.

The compiler flag `-fstack-protector` catches many stack overflows at run
time by placing a canary value before the return address, but that is a
mitigation, not a fix — bounds-safe code is the only reliable defense.

> *Invariant:* always pair a buffer with its length when writing into it.


### Command Injection (`cmdinj.c`)

Constructing a shell command by concatenating user-supplied input and
running it with `system()` lets the shell interpret metacharacters.
A filename of `; rm -rf /` becomes two commands separated by a semicolon.
`execlp` bypasses the shell entirely — the filename is passed as a literal
argument to `cat`, so no metacharacters are ever interpreted.

The same class of bug appears in web backends that shell out (`os.system`,
`exec`, `popen`), in CI scripts that embed branch names, and in makefiles
that forward environment variables. The pattern is always the same:
structured data (a command + arguments) is flattened into a string and
then re-parsed by a shell that has no way to recover the original structure.

> *Invariant:* never let untrusted input reach a shell interpreter.


### Integer Overflow (`intof.c`)

`count * item_size` uses signed `int` arithmetic. When the product exceeds
`INT_MAX` it wraps to a small (possibly negative) value, causing `malloc`
to allocate far less memory than the caller expects. Subsequent writes then
overflow a heap buffer. Using `size_t` (unsigned, pointer-sized) and
checking `count > SIZE_MAX / item_size` before multiplying prevents the wrap.

Integer overflows often appear in image parsers and archive extractors,
where the attacker controls dimensions or element counts read from a file
header. Even languages with bounds-safe arrays can be vulnerable if size
arithmetic is done with signed 32-bit integers before being passed to an
allocator.

> *Invariant:* validate sizes before using them to allocate memory.


### Timing Side-Channel (`timing.c`)

`strcmp` returns as soon as it finds a mismatch, so the time it takes is
proportional to how many leading bytes the supplied string shares with the
secret. An attacker with enough requests can recover the secret one byte
at a time by timing many comparisons. The constant-time replacement XORs
*all* bytes unconditionally and accumulates the result; the loop body never
branches on data values, so elapsed time carries no information about where
a mismatch occurred.

Timing attacks are practical over a local network and sometimes over the
internet. They affect token validation, HMAC comparison, and password checking.
Note that `volatile` on `diff` prevents the compiler from short-circuiting
the XOR loop as a dead-code elimination. For production use, prefer a library
implementation such as `CRYPTO_memcmp` (OpenSSL) or `timingsafe_bcmp`
(BSD libc), which are tested against compiler optimisations.

> *Invariant:* secret comparisons must take the same time regardless of input.


### Format-String Injection (`fmtstr.c`)

Passing user-controlled input directly as the format argument to `printf` lets
an attacker use `%x` to read stack values, `%s` to dereference arbitrary pointers,
and `%n` to write an integer to an arbitrary address — full arbitrary read/write
from a single string. The fix is trivially cheap: supply a literal format string
and pass the user data as the argument.

GCC and Clang will warn about non-literal format strings with `-Wformat-security`
(included in `-Wall`). The warning on line 5 of `fmtstr.c` is intentional--it
flags the exact call that is being demonstrated as dangerous.

> *Invariant:* format strings must be string literals, never user data.


### SHA-256 via OpenSSL EVP (`sha256.c`)

The EVP API is OpenSSL's high-level digest interface. Using it rather than the
deprecated low-level `SHA256()` function keeps the code algorithm-agnostic and
handles context allocation and cleanup consistently. The context is always freed
in the same function that allocates it, which matters: leaking an `EVP_MD_CTX`
is a small but real issue in long-running servers.

SHA-256 is a *cryptographic hash*, not a *password hash*. It is fast by design,
which makes it unsuitable for storing passwords--an attacker with a leaked database
can test billions of candidates per second on commodity hardware. For passwords,
use a slow, memory-hard function: `bcrypt`, `scrypt`, or `argon2id`.


### Secure Randomness & Hashing in Python (`pycrypto.py`)

`random.random()` is a pseudo-random number generator seeded from a predictable
state; it produces statistically uniform output but is not cryptographically secure.
`secrets.token_bytes` draws from the OS CSPRNG (`/dev/urandom` on Linux/macOS,
`BCryptGenRandom` on Windows) and is the correct choice for tokens, nonces,
and session identifiers.

`hashlib.sha256` provides the same digest as the C example without an external
dependency. The same password-storage caveat applies: use `hashlib.scrypt` or
the `bcrypt` package for password hashing, not `sha256`.

> *Invariant:* use `secrets` (not `random`) for any value that must be unpredictable to an adversary.


### SQL Injection (`sqlinj.py`)

Interpolating user-supplied values into a SQL string lets an attacker close the
intended fragment and append arbitrary SQL. The classic payload `' OR '1'='1`
turns a user lookup into a query that returns every row. A payload ending with
`; DROP TABLE users; --` deletes data. The canonical defense is parameterized
queries: the database driver sends the query structure and the data separately,
so the database never parses the data as SQL.

ORMs reduce but do not eliminate SQL injection risk. Raw query escape points
(`raw()`, `execute()`, f-string interpolation into queries) still require
parameterization. The safe version in `sqlinj.py` uses the `?` placeholder
supported by Python's `sqlite3` driver; other drivers use `%s` or named
placeholders but the principle is identical.

> *Invariant:* never build SQL (or any structured query) by string concatenation.



### Broader Takeaways

These eight examples cluster around a single theme: *trusting input before
validating it*. The vulnerability is almost always in the gap between what
the programmer assumed about the data and what an attacker can actually supply.

A few patterns appear repeatedly:

*Separate structure from data.* Whether the structure is a shell command,
a SQL query, or a format string, mixing it with untrusted data always creates
injection risk. The safe versions in each file share a common shape:
the program supplies the structure as a literal and passes user data
as an argument that is never re-parsed.

*Size before use.* Buffer overflows and integer overflows both arise
from using a length without checking it first. The check is always
cheap relative to the allocation or copy it guards.

*Side channels are interfaces too.* Timing, power consumption, and error
messages all carry information an attacker can observe. A comparison that
leaks the position of the first mismatch is functionally equivalent to a
comparison that returns the answer in smaller pieces.

*Use the right primitive.* `rand()` is not a CSPRNG. `SHA-256` is not a
password hash. `strcmp` is not a constant-time comparator. `system()`
is not a safe way to run a subprocess. The wrong primitive is not merely
"less secure"--it is broken for the intended purpose.


