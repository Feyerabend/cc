
## Builder Pattern - Where It Fits in Python

The PL/0 interpreter in `builder/plzero/` concludes that Builder in C
introduces more complexity than it removes. This example reaches the
opposite verdict: a fluent HTTP request builder in Python, where the
pattern aligns naturally with the language and the problem.

The question is the same in both cases -
*does the pattern clarify or obscure?* -
but the answer depends on context.



### What Is Here

`client.py` - an `HttpRequestBuilder` that constructs and sends HTTP
requests with a fluent (method-chaining) interface.

`server.py` - a minimal `BaseHTTPRequestHandler` serving two endpoints
(`GET /users`, `POST /orders`), used to demonstrate the client against
a real server.

Run both together:
```sh
## terminal 1
python3 server.py

## terminal 2
python3 client.py
```



### The Fluent Interface

Each builder method modifies the request under construction and returns
`self`, allowing calls to be chained:

```python
users = (HttpRequestBuilder()
         .get()
         .path("/users")
         .query("role", "admin")
         .query("limit", 5)
         .timeout(8.0)
         .send())
```

The separation between `build()` and `send()` is deliberate. `build()`
validates and returns the `HttpRequest` product. `send()` calls `build()`
then executes it. This allows the constructed request to be inspected,
logged, or tested independently of actually making the network call:

```python
req = (HttpRequestBuilder()
       .post()
       .path("/orders")
       .json_body({"items": ["laptop"], "total": 999.0})
       .build())

print(req)   # inspect without sending
```



### Why Builder Fits Here

HTTP requests have many independently optional components. The alternative
to a builder is a constructor with six parameters, most of them `None`:

```python
# Without Builder - hard to read, easy to pass args in wrong order
req = HttpRequest("GET", "/users", headers={}, params={"role": "admin"},
                  body=None, timeout=8.0)
```

The builder makes optional parts optional at the call site. You set what
you need; everything else has a default. This is the canonical use case
for the pattern: complex objects with many optional parts, where
construction order should not matter to the caller.

Compare with `json_body`, which bundles two operations into one call:

```python
def json_body(self, data: dict) -> 'HttpRequestBuilder':
    self.request.body = data
    self.header("Content-Type", "application/json")   # implicit side-effect
    return self
```

This is a genuine advantage of the builder: `json_body` enforces the
invariant that a JSON body always accompanies a `Content-Type` header.
The caller cannot forget the header; the builder takes responsibility for it.



### The Comparison: Builder vs. Keyword Arguments

For a one-shot request, the `requests` library shows that keyword
arguments can achieve the same clarity without a builder class:

```python
import requests

response = requests.get(
    "http://127.0.0.1:8000/users",
    params={"role": "admin", "limit": 5},
    timeout=8.0
)
```

Four lines, no class, no chaining. For simple cases this is cleaner.

The Builder earns its keep when the configuration is reused or
built up incrementally across different code paths:

```python
# Base configuration shared across all requests to this service
base = (HttpRequestBuilder("http://api.internal")
        .header("Authorization", "Bearer " + token)
        .header("X-Request-ID", request_id)
        .timeout(5.0))

# Per-endpoint customisation - base is not modified
users  = base.get().path("/users").query("role", "admin").send()
profile = base.get().path("/profile").send()
```

Here the builder acts as a configuration template. Without it, the shared
headers and timeout would either be duplicated at every call site or
wrapped in a helper function that duplicates the builder's role informally.



### A Subtle Flaw

The current implementation is mutation-based: `build()` returns
`self.request` directly, not a copy.

```python
def build(self) -> HttpRequest:
    if not self.request.url:
        raise ValueError("URL must be set")
    return self.request           # same object, not a snapshot
```

If the builder is reused after `build()`, the returned `HttpRequest`
and the builder's internal state are the same object. A subsequent
`.query(...)` call on the builder would also modify the already-returned
request.

In practice this rarely causes problems because builders are typically
discarded after the final call to `send()`. But it violates the expectation
that `build()` produces a finished, independent product. A corrected
version would return a copy:

```python
import copy

def build(self) -> HttpRequest:
    if not self.request.url:
        raise ValueError("URL must be set")
    return copy.copy(self.request)
```

This is a common mistake in mutation-based fluent builders and illustrates
why the pattern's implementation details matter as much as its structure.



### Verdict

| Context                                   | Builder appropriate? | Reason                                               |
|-------------------------------------------|----------------------|------------------------------------------------------|
| One-shot request                          | No                   | Keyword arguments are shorter and equally clear      |
| Shared configuration, multiple endpoints  | Yes                  | Base config is set once, customised per call         |
| Enforcing invariants (e.g. JSON + header) | Yes                  | Builder bundles the constraint, caller cannot forget |
| PL/0 AST construction in C                | No                   | Direct node allocation is clearer and more idiomatic |

The HTTP Builder sits on the right side of this table because the problem -
many optional fields, shared configuration, bundled invariants - matches
what the pattern is designed to handle. The pattern is not applied because
it is a pattern; it is applied because the alternatives are worse.

That is the distinction the PL/0 example draws in the negative, and this
example draws in the positive.
