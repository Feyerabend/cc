
## State Machine - A Pattern That Fits C

Earlier sections show patterns being forced onto languages that do not need
them: Builder in C producing verbose boilerplate, Singleton in Python
adding structure the module system already provides.

The State Machine is a counterpoint. It is one of the few classical patterns
that maps directly onto C's strengths rather than fighting them. The reason
is simple: C already has function pointers and indexed arrays. A state
machine's core structure - *for each (state, event) pair, select and invoke
a handler* - is just a two-dimensional lookup followed by a call.
No class hierarchy is needed. No indirection is introduced. The pattern
is not being applied to the code; the pattern *is* the code.



### The Problem It Solves

A system with distinct operating modes - where the same event means
different things in different modes - will generate nested conditionals
that grow with every new state or event:

```c
/* Naive approach - grows quadratically */
void handle_event(State s, Event ev) {
    if (s == ST_IDLE) {
        if (ev == EV_CONNECT) { /* .. */ }
        else if (ev == EV_DATA) { /* illegal, but where is that checked? */ }
        /* ... */
    } else if (s == ST_CONNECTED) {
        if (ev == EV_DATA) { /* .. */ }
        else if (ev == EV_CLOSE) { /* .. */ }
        else if (ev == EV_CONNECT) { /* illegal */ }
        /* .. */
    }
    /* .. and so on for every state */
}
```

With five states and five events, this function has 25 cases to manage.
Adding a sixth state means extending every conditional. The valid and
invalid transitions are mixed into undifferentiated prose, and the
structure of the state machine - which transitions exist, which do not -
is invisible to the reader.



### The Table Approach

The function pointer table separates *structure* from *behaviour*:

```c
typedef State (*Handler)(Conn *);

static const Handler table[NUM_STATES][NUM_EVENTS] = {
/*                  connect          ready                 data                close               error               */
/* IDLE        */ { on_idle_connect, NULL,                 NULL,               NULL,               NULL                },
/* CONNECTING  */ { NULL,            on_connecting_ready,  NULL,               NULL,               on_connecting_error },
/* CONNECTED   */ { NULL,            NULL,                 on_connected_data,  on_connected_close, on_connected_error  },
/* CLOSING     */ { NULL,            on_closing_ready,     NULL,               NULL,               on_closing_error    },
/* CLOSED      */ { NULL,            NULL,                 NULL,               NULL,               NULL                },
};
```

`NULL` means the event is not valid in that state. The table documents
this explicitly: the entire transition structure is visible in one place,
as a grid. Adding a state adds a row. Adding an event adds a column.

The dispatch function has no knowledge of individual states or events:

```c
static State dispatch(State current, Event ev, Conn *conn) {
    Handler h = table[current][ev];
    if (h == NULL) {
        /* illegal transition - stay put, log it */
        return current;
    }
    return h(conn);
}
```

This function never changes. All state-specific logic lives in the
handlers. All structural logic lives in the table.



### The Remaining Brittleness

The table approach does not eliminate the Expression Problem -
it makes it explicit.

|              | Add a new *state* | Add a new *event*                |
|--------------|-------------------|----------------------------------|
| Table        | Add one row       | Add one column - touch every row |
| Naive switch | Add one block     | Add one case per block           |

Adding a new state is cheap: write the handlers, add a row, done.
Adding a new event is expensive in both approaches, but the table
makes the cost visible. If you add `EV_TIMEOUT` to the enum and
forget to extend the table, the C compiler will warn about a
*missing initializer* - provided `-Wall` is enabled:

```
conn.c: warning: missing initializer for field 'ev_timeout'
```

The naive switch gives no such warning. You simply forget a case,
and the default branch (if any) silently handles it.

This is an unusual property for a C pattern: the table turns a
*runtime bug* (unhandled event) into a *compile-time warning*.



### When This Pattern Is Appropriate

Appropriate:
- Protocol parsers (TCP lifecycle, HTTP chunked encoding, TLS handshake)
- Embedded device control (motor controllers, sensor state)
- Lexers and tokenisers where token identity depends on current mode
- Any system where the number of states is stable and known at compile time

Less appropriate:
- Systems where states are dynamic or data-driven at runtime
- Simple two-state toggles - a boolean is sufficient
- Systems where the state space is large and sparse (most entries NULL)
  - a dispatch table or hash map may be more appropriate than a dense grid



### Comparison with the Builder Example

The PL/0 compiler in `builder/plzero/` shows the Builder pattern
implemented in C and concludes that it is *technically feasible but
conceptually misaligned* with the language. The conclusion there:
> *In C, where simplicity, explicitness, and control are primary virtues,
introducing a builder abstraction for AST construction may introduce
more complexity than it removes.*

The State Machine reaches the opposite conclusion. It does not fight C;
it exploits C. Function pointers and array indexing are C's native
mechanisms. The pattern is not layered on top of the language - it
assembles the language's existing parts into a form that the problem
already implies.

This distinction - between patterns that compensate for what a language
lacks and patterns that express what a language already provides - is
the practical test for whether a pattern belongs in a given context.



### Running the Example

```sh
cc -std=c11 -Wall -Wextra -o conn conn.c
./conn
```

The four scenarios cover: happy path, mid-connection error, illegal event
(data before handshake completes), and handshake failure. The dispatch
function handles all four identically; only the table and the handlers
determine the outcome.
