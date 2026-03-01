
## `objdb`

A small but complete *object database written in C* that demonstrates
four foundational systems-programming concepts working together in one coherent codebase:
- *Frame Stack* - scoped transaction contexts that track mutations
- *Checkpoints* - named save points for targeted rollback
- *Backtracking* - unwinding the frame stack to restore prior state
- *State Machine* - driving the query lifecycle through well-defined phases

It includes an interactive shell (`repl.c`) so you can explore all of these directly.

| File | Purpose |
|------|---------|
| `objdb.h` | Types, structs, and API declarations |
| `objdb.c` | Database engine implementation |
| `main.c` | Seven self-contained demos covering every concept |
| `repl.c` | Interactive shell |


No external dependencies. C99 or later.

*Note:* `ObjDB` is large enough to overflow the default stack,
so it is always heap-allocated with `calloc`. The shell and demo
handle this for you automatically.


### Interactive shell

```bash
./objdb_repl
```

The prompt reflects your current frame stack depth in real time:

```
objdb ∅ >                          # no open frame
objdb/outer_tx >                   # one frame open
objdb/outer_tx/safe_state >        # checkpoint frame (shown in yellow)
objdb/outer_tx/safe_state/insert > # nested frame inside checkpoint
```

#### Command reference

*Objects*

```
set <key> int   <n>      store an integer
set <key> float <n>      store a float
set <key> str   <text>   store a string
get <key>                read one object
del <key>                delete an object
dump                     print all live objects
```

*Queries*

```
query              return all objects
query int          filter to integers only
query float        filter to floats only
query str          filter to strings only
```

*Frames*

```
frame push <label>   open a new transaction scope
frame commit         make all mutations in this frame permanent
frame rollback       undo every mutation in this frame
frame list           inspect the current frame stack
```

*Checkpoints & Backtracking*

```
checkpoint <name>    set a named save point (pushes a special frame)
backtrack  <name>    rewind to that save point, undoing everything since
```

*Shell*

```
help    show this list
quit    exit
```



### Concepts explained

#### Frame Stack

Every write operation (`set`, `del`) records a *before-snapshot* of the
affected object into the currently open frame's undo log before touching
anything. This happens in `record_undo()` in `objdb.c`--and only the first
mutation per object per frame is captured, so subsequent writes to the
same key within one frame don't bloat the log.

```
frame push my_tx
  set score:alice int 9999      <-- snapshot of score:alice saved
  set user:bob str DELETED      <-- snapshot of user:bob saved
frame rollback                  <-- both restored exactly as they were
```

Committing a frame simply discards the undo log--the mutations are already
in the store and are now permanent. Rolling back replays the log in reverse order.

#### Checkpoints

A checkpoint is just a frame with a name registered in a lookup table.
`db_checkpoint("safe_state")` pushes a frame marked `is_checkpoint = true`
and stores its stack depth under that name. There is no separate snapshot
mechanism--it reuses everything the frame stack already does.

```
checkpoint safe_state            <-- pushes frame, registers name→depth
  set score:alice int 1350
  set user:dave str Dave Dahl
backtrack safe_state             <-- rolls back to that depth
```

#### Backtracking

`db_backtrack_to(name)` looks up the target frame depth and then rolls
back every frame from the current top down to and including the checkpoint
frame. This means it can eat through committed sub-frames, uncommitted frames,
and the checkpoint frame itself in one pass--restoring the database to
exactly the state it was in when the checkpoint was set.

The demo in section 4 of `main.c` shows this clearly: a nested frame
(`risky_insert`) that was already committed gets fully unwound by a
backtrack, because the checkpoint was set before that nested work began.

#### Query State Machine

Queries are driven by an explicit state machine with five states:

```
IDLE --> SCAN --> FILTER --> PROJECT --> DONE
                                   \__ ERROR
```

`db_query_run()` loops on a `switch` until it reaches `DONE` or `ERROR`.
Each state does its work and sets the next state--adding a new phase
(e.g. `SORT`, `LIMIT`, `AGGREGATE`) is just a matter of adding an enum value and a `case`.

```c
typedef enum {
    QS_IDLE, QS_SCAN, QS_FILTER, QS_PROJECT, QS_DONE, QS_ERROR
} QueryState;
```



### Example session

```
objdb ∅ > set user:alice str Alice Andersson
  set user:alice
objdb ∅ > set score:alice int 1200
  set score:alice
objdb ∅ > checkpoint before_update
[frame] push 'before_update'
[checkpoint] 'before_update' set at frame depth 0

objdb/before_update > set score:alice int 9999
  set score:alice
objdb/before_update > get score:alice
  score:alice            = 9999  (int, v2)

objdb/before_update > backtrack before_update
[backtrack] rewinding to checkpoint 'before_update' (frame 0 → 0)
[frame] rollback 'before_update'  (undoing 1 mutation(s))

objdb ∅ > get score:alice
  score:alice            = 1200  (int, v1)
```



### Limitations & design notes

- The object store is a fixed-size flat array (`MAX_OBJECTS = 256`).
  Lookup is O(n) linear scan--fine for demonstration, easy to replace with a hash table.

- Undo log entries are full object snapshots, not diffs.
  Simple and correct, but not space-efficient for large values.

- The frame stack and checkpoint table are also fixed-size arrays.
  All limits are defined as constants at the top of `objdb.h` and can be raised freely.

- There is no persistence--the database lives entirely in memory and starts fresh each run.

- No thread safety. One writer, one reader, no locks needed.



### Projects extending it

Some natural next steps if you want to take this further:
- *Persistence* - `fwrite` the object array to disk on commit, `fread` on startup
- *Hash table* - replace the linear scan in `find_slot()` with an open-addressed hash map for O(1) lookup
- *Dispatch table* - add a vtable pointer to `Object` for polymorphic behaviour per type
- *Context switching* - run multiple independent query cursors concurrently using `setjmp`/`longjmp` or `ucontext`
- *Memory barriers* - add `_Atomic` fields and `atomic_thread_fence` if you introduce a second writer thread

