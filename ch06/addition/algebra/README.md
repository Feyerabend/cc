
## From Algebraic Specifications to Code: A Programmer's Guide

So if an LLM can generate code, what remains for the programmer?

One answer is that programming shifts toward *specification* rather 
than *implementation*.[^shift] Instead of writing detailed code
in a particular  language, the programmer "crafts" the problem
in more abstract, often mathematical, terms. Much of today's
low-level detail is pushed down or automated.

This idea is not new. In the 1980s and 1990s, algebraic and formal
methods aimed to do something similar: describe systems through equations,
invariants, and transformations, and derive implementations from
those descriptions. At the time, these approaches saw limited adoption,
partly because the upfront effort was high, the tools were immature,
and the benefits were not obvious for everyday software development.

LLMs change the cost–benefit balance. The time-consuming art of "crafting"
may now pay off, because a precise, high-level specification can be
rapidly turned into working code, explored, and revised. The
programmer's role shifts from writing lines of code to choosing abstractions,
defining constraints, and judging whether the generated behaviour
actually matches the intended system.

Let's explore one way ..

[^shift]: This was very much __close__ to the idea behind the interest
in the beginning of the 80s around *logic programming*: 
You should be able to specify in code *what* should happen, rather then *how*.


### Why Should You Care?

You've probably written code where:
- The client says "wait, that's not what I meant" after you've already built it ..
- Edge cases emerge in production that no one thought about
- Six months later, you can't remember why a particular validation exists?
- Different parts of the codebase handle the "same" business rule differently

*Algebraic specifications* give you a precise, mathematical way to describe
*what* your code should do before you write *how* it does it. And now, with LLMs,
you can use these specifications to *generate* correct implementations rather
than writing everything by hand.

Think of it as types tell you what kind of data flows through your functions,
algebraic specs tell you what *laws* your functions must obey.


### The Core Idea

```
// Instead of jumping straight to this:
function withdraw(accountId, amount) {
  const account = db.get(accountId);
  if (account.balance < amount) throw new Error("Insufficient funds");
  account.balance -= amount;
  db.save(account);
  return account;
}

// You first write THIS (the specification):
withdraw: Account × Money → Account
  pre: balance(account) ≥ amount
  post: balance(withdraw(account, amount)) = balance(account) - amount
  invariant: balance(account) ≥ 0

// Then use an LLM to generate the code that provably satisfies the spec
// And automatically generate tests from the mathematical properties
```

The spec is a *contract* that's precise enough for a machine to reason about.


### Part 1: The Mathematical Foundation

#### Many-Sorted Algebra: Just Types + Functions + Rules

If you understand types, you already get 80% of this.

*A many-sorted algebra has three parts:*

1. *Sorts* (think: types)
   ```
   Account, Money, Bool, String
   ```

2. *Operations* (think: function signatures)
   ```
   create: → Account
   deposit: Account × Money → Account
   balance: Account → Money
   add: Money × Money → Money
   ```
   (Here, × denotes the Cartesian product of sorts, i.e. the types of function
   arguments, not numeric multiplication.)

3. *Equations* (think: laws your functions must obey)
   ```
   balance(create()) = 0
   balance(deposit(a, m)) = add(balance(a), m)
   add(m, 0) = m
   add(m1, m2) = add(m2, m1)  // commutative
   ```

That's it. You're defining a "calculator" where you specify
what operations exist and what rules they follow.

*Why "many-sorted"?* Because you have many types (sorts),
unlike basic algebra which just uses numbers.

#### Example: A Simple Banking Algebra

```
SORTS:
  Account, Money

OPERATIONS:
  // Constructors (create new things)
  create: → Account
  zero: → Money
  dollars: Int → Money
  
  // Commands (change things)
  deposit: Account × Money → Account
  withdraw: Account × Money → Account
  
  // Queries (ask about things)
  balance: Account → Money
  
  // Money operations
  add: Money × Money → Money
  subtract: Money × Money → Money
  greaterThan: Money × Money → Bool

EQUATIONS:
  // What we know about new accounts
  balance(create()) = zero
  
  // What deposit does
  balance(deposit(a, m)) = add(balance(a), m)
  
  // What withdraw does
  balance(withdraw(a, m)) = subtract(balance(a), m)
  
  // Money behaves like you'd expect
  add(m, zero) = m
  add(m1, m2) = add(m2, m1)
  subtract(m, zero) = m
```

*Notice:* We haven't said *how* to implement `Account` or `Money`. We've just
said what operations exist and how they relate. You could implement `Account`
as a class, a struct, a row in a database, or a JSON blob--as long as the equations hold.

#### Adding State: The Real World

Pure algebra is timeless--`add(2, 3)` is always 5.
But real systems have *state* that changes over time:
- Your account balance *now* vs *after* a deposit
- Whether a room is booked *now* vs *tomorrow*
- Who has permission *before* vs *after* a promotion

*State-based algebra* makes this explicit:

```
SORTS:
  State, AccountID, Money

OPERATIONS:
  // Commands return new state
  createAccount: State → State × AccountID
  deposit: State × AccountID × Money → State
  withdraw: State × AccountID × Money → State × Result
  
  // Queries just read state
  balance: State × AccountID → Money
  exists: State × AccountID → Bool
```

Now operations take the *current state* and return the *next state*.
This is like Redux or event sourcing--state transitions are explicit.

#### Pre/Post Conditions: What Must Be True

Equations tell you how operations relate. *Pre and post conditions*
tell you what must be true before/after an operation:

```
withdraw: State × AccountID × Money → State × Result

  PRE-CONDITIONS (must be true to call this):
    exists(state, accountId) = true
    balance(state, accountId) ≥ amount
    amount > 0
  
  POST-CONDITIONS (guaranteed true after):
    let (newState, result) = withdraw(state, accountId, amount)
    
    if result = Success then
      balance(newState, accountId) = balance(state, accountId) - amount
      // All other accounts unchanged
      for all otherId ≠ accountId:
        balance(newState, otherId) = balance(state, otherId)
```

*Why this matters:* 
- Pre-conditions become defensive checks in your code
- Post-conditions become assertions/tests
- LLMs can verify their generated code satisfies these

#### Invariants: What's Always True

*Invariants* are properties that hold across *all* states:

```
INVARIANTS:
  // Account balances never go negative
  for all state, accountId:
    exists(state, accountId) = true 
      implies balance(state, accountId) ≥ 0
  
  // Account IDs are unique
  for all state, id1, id2:
    (id1 ≠ id2) implies (account(state, id1) ≠ account(state, id2))
  
  // Conservation of money
  totalMoney(state) = sum of all balances
```

These become:
- Runtime assertions in debug builds
- Property-based tests
- Design constraints

### Part 2: Beyond Basic Algebra

#### Ordered Structures: When Things Have Levels

Many domains have natural *orderings*:
- Permissions: `read < write < admin`
- Priority: `low < medium < high < critical`
- Versions: `v1.0 < v1.1 < v2.0`

You can specify these as *partial orders*:

```
SORT: Permission with ordering ≤

VALUES:
  none, read, write, admin
  
ORDER:
  none ≤ read ≤ write ≤ admin

OPERATIONS:
  grantPermission: State × User × Permission → State
    POST: newPermission(user) ≥ oldPermission(user)
         // Permissions only increase, never decrease
         
  hasPermission: User × Permission → Bool
    // User has permission p if their permission ≥ p
    hasPermission(user, p) = (userPermission(user) ≥ p)
```

*Why useful:* You can now specify monotonicity (things only go up),
access control, and upgrade paths mathematically.

#### Lattices: When Things Can Be Combined

Sometimes you need to *combine* values.
*Lattices* give you two operations:
- *Join (∨)*: least upper bound - "either/or" 
- *Meet (∧)*: greatest lower bound - "both"

Example with permissions:

```
LATTICE: Permission

OPERATIONS:
  join: Permission × Permission → Permission  // combine permissions
  meet: Permission × Permission → Permission  // common permissions

LAWS:
  join(read, write) = write        // taking either gives you the higher
  meet(write, admin) = write       // common permission is the lower
  join(p, p) = p                   // idempotent
  join(p1, p2) = join(p2, p1)     // commutative
```

*Real-world use:* 
- Merging user permissions from multiple roles
- Combining feature flags
- Resolving concurrent updates (CRDTs)

#### Groups: When You Can Undo Things

Some operations are *reversible*. *Groups* formalise this:

```
GROUP: Transform

OPERATIONS:
  identity: → Transform              // do nothing
  compose: Transform × Transform → Transform
  inverse: Transform → Transform     // undo
  
LAWS:
  compose(t, identity) = t
  compose(t, inverse(t)) = identity  // undo brings you back
  compose(t1, compose(t2, t3)) = compose(compose(t1, t2), t3)
  
APPLIED TO STATE:
  apply: State × Transform → State
  
  apply(state, identity) = state
  apply(apply(state, t), inverse(t)) = state  // undo works!
```

*Use cases:*
- Undo/redo in editors
- Rollback in databases
- Reversible migrations

### Part 3: Writing Specifications (The Practical Part)

#### Template for a New Spec

When starting a feature, use this template:

```
SPECIFICATION: [FeatureName]

SORTS:
  [List your domain types]
  State, [Entity1], [Entity2], ...

OPERATIONS:
  // Constructors
  [how to create new things]
  
  // Commands (State → State × ...)
  [operations that change state]
  
  // Queries (State × ... → ...)
  [operations that just read]

PRE/POST CONDITIONS:
  [For each command, specify]:
    PRE: what must be true before
    POST: what's guaranteed after

INVARIANTS:
  [Properties that always hold]
  
EQUATIONS:
  [Laws relating operations]
```

#### Worked Example: Meeting Room Booking

Let's spec a real feature from scratch.

*Stakeholder says:* *"Users can book meeting rooms for time slots,
but only if the room is available and they have permission."*

##### Step 1: Identify Sorts

```
SORTS:
  State
  User
  Room  
  TimeSlot
  Booking
  BookingID
  Result = Success | RoomUnavailable | PermissionDenied
```

##### Step 2: Define Operations

```
OPERATIONS:
  // Constructors
  emptyState: → State
  
  // Commands
  bookRoom: State × User × Room × TimeSlot → State × Result
  cancelBooking: State × User × BookingID → State × Result
  
  // Queries
  isAvailable: State × Room × TimeSlot → Bool
  hasPermission: State × User × Room → Bool
  owner: State × BookingID → User
  bookings: State × Room → Set(Booking)
  overlaps: TimeSlot × TimeSlot → Bool
```

##### Step 3: Specify the Core Operation

```
bookRoom: State × User × Room × TimeSlot → State × Result

  PRE:
    // User must have permission for this room
    hasPermission(state, user, room) = true
  
  POST:
    let (newState, result) = bookRoom(state, user, room, slot)
    
    CASE result OF
      Success:
        // Room is now unavailable for that slot
        isAvailable(newState, room, slot) = false
        
        // A new booking exists
        exists bookingId where:
          owner(newState, bookingId) = user
          bookingRoom(newState, bookingId) = room
          bookingSlot(newState, bookingId) = slot
        
        // All other bookings unchanged
        for all otherBooking in bookings(state):
          otherBooking still exists in newState
      
      RoomUnavailable:
        // State unchanged
        newState = state
        isAvailable(state, room, slot) = false
      
      PermissionDenied:
        // State unchanged  
        newState = state
        hasPermission(state, user, room) = false
```

##### Step 4: Add Invariants

```
INVARIANTS:
  // No double-booking
  for all state, room, slot, booking1, booking2:
    (booking1 ≠ booking2) and
    (bookingRoom(state, booking1) = room) and
    (bookingRoom(state, booking2) = room) and
    (bookingSlot(state, booking1) = slot1) and
    (bookingSlot(state, booking2) = slot2)
    implies
    not overlaps(slot1, slot2)
  
  // Every booking has an owner
  for all state, bookingId:
    exists user where owner(state, bookingId) = user
  
  // Can only cancel your own bookings
  // (This would be in the cancelBooking pre-condition)
```

##### Step 5: Define Helper Predicates

```
isAvailable(state, room, slot) =
  not exists booking where
    bookingRoom(state, booking) = room and
    overlaps(bookingSlot(state, booking), slot)

overlaps(slot1, slot2) =
  not (endTime(slot1) ≤ startTime(slot2) or
       endTime(slot2) ≤ startTime(slot1))
```

#### This Is Now Your Contract

You can:
1. Show this to stakeholders - it's precise but readable
2. Use it to generate tests - every equation becomes a test
3. Give it to an LLM to generate code
4. Check edge cases - what if `overlaps` is exactly equal?

### Part 4: Working with LLMs

#### The Development Workflow

```
┌----------------------------------------┐
│ 1. Write Specification (Human + LLM)   │
│    - Extract from requirements         │
│    - Formalize in algebraic notation   │
│    - Validate completeness             │
└----------------------------------------┘
                     │
┌----------------------------------------┐
│ 2. Generate Tests (LLM)                │
│    - Property-based from equations     │
│    - Invariant checks                  │
│    - Pre/post condition validation     │
└----------------------------------------┘
                     │
┌----------------------------------------┐
│ 3. Generate Implementation (LLM)       │
│    - Satisfying the spec               │
│    - With defensive checks             │
│    - Documented with spec references   │
└----------------------------------------┘
                     │
┌----------------------------------------┐
│ 4. Verify (Human)                      │
│    - Run tests                         │
│    - Review code against spec.         │
│    - Iterate                           │
└----------------------------------------┘
```

#### Prompt Pattern 1: Specification Validation

```md
I have this algebraic specification for a meeting room booking system:

[paste your spec]

Please analyse it for:
1. Completeness - are there missing pre/post conditions?
2. Consistency - do any equations contradict?
3. Edge cases - what scenarios might violate invariants?
4. Ambiguities - what needs clarification?

For each issue, suggest a fix in the same algebraic notation.
```

The LLM will catch things like:
- "What happens if a user books the same room twice simultaneously?"
- "Your `overlaps` predicate doesn't handle equal times"
- "The post-condition doesn't specify what happens to existing bookings"

#### Prompt Pattern 2: Test Generation

```markdown
From this specification:

bookRoom: State × User × Room × TimeSlot → State × Result
  PRE: hasPermission(state, user, room) = true
  POST: [your post-conditions]
  INVARIANT: [no double-booking]

Generate property-based tests in Python using Hypothesis that verify:
1. Pre-conditions are necessary (trying to violate them fails)
2. Post-conditions hold (all guarantees are met)
3. Invariants are maintained (never double-book)
4. Equations hold for random test data

Use this state representation:
- State is a class with a dictionary of bookings
- Booking is a dataclass with room, user, time_slot fields
```

The LLM will produce something like:

```python
from hypothesis import given, strategies as st
from datetime import datetime, timedelta
import pytest

@given(
    room=st.text(min_size=1),
    user=st.text(min_size=1),
    start=st.datetimes(),
    duration=st.integers(min_value=1, max_value=480)  ## up to 8 hours
)
def test_booking_makes_room_unavailable(room, user, start, duration):
    """Property: Successfully booking makes room unavailable
    
    Spec: POST condition from bookRoom
    """
    state = State()
    state.grant_permission(user, room)
    
    slot = TimeSlot(start, start + timedelta(minutes=duration))
    
    ## Room should be available before booking
    assert state.is_available(room, slot)
    
    ## Book it
    new_state, result = state.book_room(user, room, slot)
    
    ## Property from spec: if successful, room is unavailable
    if result == Result.SUCCESS:
        assert not new_state.is_available(room, slot)

@given(
    room=st.text(min_size=1),
    user1=st.text(min_size=1),
    user2=st.text(min_size=1),
    start=st.datetimes(),
    duration=st.integers(min_value=1, max_value=480)
)
def test_no_double_booking_invariant(room, user1, user2, start, duration):
    """Invariant: No two bookings can overlap for same room
    
    Spec: INVARIANT no double-booking
    """
    state = State()
    state.grant_permission(user1, room)
    state.grant_permission(user2, room)
    
    slot = TimeSlot(start, start + timedelta(minutes=duration))
    
    ## First user books
    state, result1 = state.book_room(user1, room, slot)
    assert result1 == Result.SUCCESS
    
    ## Second user tries to book overlapping time
    overlapping_slot = TimeSlot(
        start + timedelta(minutes=duration//2),
        start + timedelta(minutes=duration*2)
    )
    
    _, result2 = state.book_room(user2, room, overlapping_slot)
    
    ## Invariant: must fail
    assert result2 == Result.ROOM_UNAVAILABLE

def test_permission_precondition_is_necessary():
    """Pre-condition test: booking without permission must fail
    
    Spec: PRE hasPermission(state, user, room) = true
    """
    state = State()
    user = "unauthorized_user"
    room = "conference_room_a"
    slot = TimeSlot(datetime.now(), datetime.now() + timedelta(hours=1))
    
    ## Don't grant permission
    
    _, result = state.book_room(user, room, slot)
    
    ## Must fail due to pre-condition
    assert result == Result.PERMISSION_DENIED
```

#### Prompt Pattern 3: Implementation Generation

```markdown
Implement this specification in TypeScript:

[paste spec]

Requirements:
- Use immutable data structures (State should be readonly)
- Validate all pre-conditions, throwing errors with clear messages
- Include post-condition assertions in debug mode
- Add JSDoc comments linking code to spec elements
- Use Result type for operations (don't throw on business rule violations)

State representation:
- State contains Map<BookingID, Booking>
- State contains Map<User, Set<Room>> for permissions
- Use UUIDs for BookingID
```

The LLM generates:

```typescript
/*
 * Meeting room booking system
 * 
 * Spec: BookingSystem algebraic specification v1.0
 */

type Result<T> = 
  | { success: true; value: T }
  | { success: false; error: BookingError };

enum BookingError {
  ROOM_UNAVAILABLE = "ROOM_UNAVAILABLE",
  PERMISSION_DENIED = "PERMISSION_DENIED",
}

/*
 * Spec: TimeSlot sort
 */
interface TimeSlot {
  readonly start: Date;
  readonly end: Date;
}

/*
 * Spec: overlaps predicate
 * 
 * overlaps(slot1, slot2) = 
 *   not (end(slot1) ≤ start(slot2) or end(slot2) ≤ start(slot1))
 */
function overlaps(slot1: TimeSlot, slot2: TimeSlot): boolean {
  return !(slot1.end <= slot2.start || slot2.end <= slot1.start);
}

/*
 * Spec: Booking sort
 */
interface Booking {
  readonly id: string;
  readonly room: string;
  readonly user: string;
  readonly timeSlot: TimeSlot;
}

/*
 * Spec: State sort
 */
class State {
  private constructor(
    private readonly bookings: ReadonlyMap<string, Booking>,
    private readonly permissions: ReadonlyMap<string, ReadonlySet<string>>
  ) {
    // Verify invariant on construction
    this.checkInvariants();
  }
  
  /*
   * Spec: emptyState constructor
   */
  static empty(): State {
    return new State(new Map(), new Map());
  }
  
  /*
   * Spec: bookRoom operation
   * 
   * bookRoom: State × User × Room × TimeSlot → State × Result
   * 
   * PRE: hasPermission(state, user, room) = true
   * POST: if Success then isAvailable(newState, room, slot) = false
   */
  bookRoom(
    user: string, 
    room: string, 
    timeSlot: TimeSlot
  ): [State, Result<string>] {
    // Pre-condition: hasPermission(state, user, room)
    if (!this.hasPermission(user, room)) {
      return [this, { 
        success: false, 
        error: BookingError.PERMISSION_DENIED 
      }];
    }
    
    // Check availability (part of operation logic)
    if (!this.isAvailable(room, timeSlot)) {
      return [this, {
        success: false,
        error: BookingError.ROOM_UNAVAILABLE
      }];
    }
    
    // Create new booking
    const bookingId = crypto.randomUUID();
    const booking: Booking = {
      id: bookingId,
      room,
      user,
      timeSlot
    };
    
    // Create new state (immutable update)
    const newBookings = new Map(this.bookings);
    newBookings.set(bookingId, booking);
    const newState = new State(newBookings, this.permissions);
    
    // Post-condition assertion (debug mode)
    if (process.env.NODE_ENV === 'development') {
      console.assert(
        !newState.isAvailable(room, timeSlot),
        "Post-condition violated: room should be unavailable after booking"
      );
      console.assert(
        newState.owner(bookingId) === user,
        "Post-condition violated: booking owner should be the user"
      );
    }
    
    return [newState, { success: true, value: bookingId }];
  }
  
  /*
   * Spec: isAvailable query
   * 
   * isAvailable(state, room, slot) = 
   *   not exists booking where
   *     bookingRoom(booking) = room and overlaps(bookingSlot(booking), slot)
   */
  isAvailable(room: string, timeSlot: TimeSlot): boolean {
    for (const booking of this.bookings.values()) {
      if (booking.room === room && overlaps(booking.timeSlot, timeSlot)) {
        return false;
      }
    }
    return true;
  }
  
  /*
   * Spec: hasPermission query
   */
  hasPermission(user: string, room: string): boolean {
    const userRooms = this.permissions.get(user);
    return userRooms?.has(room) ?? false;
  }
  
  /*
   * Spec: owner query
   */
  owner(bookingId: string): string | undefined {
    return this.bookings.get(bookingId)?.user;
  }
  
  /*
   * Spec: INVARIANT - no double-booking
   * 
   * for all booking1, booking2:
   *   (booking1 ≠ booking2) and (room1 = room2) 
   *     implies not overlaps(slot1, slot2)
   */
  private checkInvariants(): void {
    const bookingsByRoom = new Map<string, Booking[]>();
    
    // Group bookings by room
    for (const booking of this.bookings.values()) {
      const roomBookings = bookingsByRoom.get(booking.room) ?? [];
      roomBookings.push(booking);
      bookingsByRoom.set(booking.room, roomBookings);
    }
    
    // Check no overlaps within each room
    for (const roomBookings of bookingsByRoom.values()) {
      for (let i = 0; i < roomBookings.length; i++) {
        for (let j = i + 1; j < roomBookings.length; j++) {
          if (overlaps(roomBookings[i].timeSlot, roomBookings[j].timeSlot)) {
            throw new Error(
              `Invariant violated: overlapping bookings detected ` +
              `${roomBookings[i].id} and ${roomBookings[j].id}`
            );
          }
        }
      }
    }
  }
  
  // Helper for granting permissions (not in core spec)
  grantPermission(user: string, room: string): State {
    const userRooms = new Set(this.permissions.get(user) ?? []);
    userRooms.add(room);
    const newPermissions = new Map(this.permissions);
    newPermissions.set(user, userRooms);
    return new State(this.bookings, newPermissions);
  }
}
```

Notice how:
- Every operation has a comment linking back to the spec
- Pre-conditions are checked defensively
- Post-conditions are asserted in debug mode
- Invariants are enforced on state construction
- The code structure mirrors the algebraic structure

#### What to Watch For

*1. Abstraction Mismatch*
The spec might be too abstract for direct implementation:

```
// Spec says:
accounts: State → Set(AccountID)

// But efficient implementation needs:
class State {
  private accountsById: Map<AccountID, Account>  // O(1) lookup
  private accountIndex: Set<AccountID>          // cached for iteration
}
```

Tell the LLM: "Implement this spec, but optimise the `accounts` query to O(1) lookup.
Document the representation choice."

*2. Concurrency*
Your spec might be for a single-threaded model:

```
// Spec is sequential
withdraw: State × AccountID × Money → State

// But you need concurrent access
```

Extend the spec with version numbers or use CRDTs, or tell
the LLM: "Wrap all state-modifying operations in a transaction boundary."

*3. Error Handling Beyond Business Rules*
The spec handles business errors (insufficient funds), but what about:
- Network failures
- Database crashes  
- Invalid input encoding

Tell the LLM: "Add a technical error layer separate from the business Result type in the spec."

### Part 5: Practical Considerations

#### When to Use This Approach

*Good Fit:*
- Complex business logic with many edge cases
- Financial, healthcare, booking systems - where correctness matters
- Systems that will evolve over time (spec documents intent)
- When multiple stakeholders need to agree on behaviour
- APIs and service boundaries (spec becomes contract)

*Poor Fit:*
- UI layout and styling
- One-off scripts
- Prototype/throwaway code
- When requirements are extremely vague

#### How Much to Specify

You don't need to specify everything. Focus on:

1. *Critical invariants* - things that must never be violated
2. *Complex operations* - ones with subtle pre/post conditions
3. *Domain boundaries* - public APIs, service interfaces
4. *Business rules* - the "why" behind the code

Leave unspecified:
- Obvious CRUD operations
- Pure implementation details
- Performance optimisations (unless they affect correctness)

#### Living Documentation

The spec should evolve:

```
// In code:
/*
 * Implements: withdraw operation from AccountSpec.alg v2.3
 * 
 * Spec difference: Added overdraft protection (2024-01-15)
 * See: docs/specs/account-spec-v2.3.md
 */
function withdraw(accountId: string, amount: Money): Result {
  // .. implementation
}
```

Keep a changelog in the spec:

```
SPECIFICATION: AccountSystem

VERSION: 2.3
CHANGES:
  v2.3 (2024-01-15): Added overdraft protection invariant
  v2.2 (2023-12-01): Refined withdraw post-condition for concurrent access
  v2.1 (2023-10-15): Initial version

[rest of spec]
```

#### Integration with Existing Codebases

You don't need to rewrite everything. Start small:

1. *Pick one critical module* (e.g., payment processing)
2. *Extract its specification* (document current behaviour formally)
3. *Generate tests from spec* (find bugs in existing code!)
4. *Refactor toward spec* (incrementally fix discrepancies)
5. *New features use spec-first* (from now on)

#### Team Adoption

*Phase 1: Introduce Concepts (1-2 weeks)*
- Share this document
- Do a workshop on one real feature
- Generate tests from a spec together

*Phase 2: Pilot (1-2 months)*
- One team member specs new features
- Others review both spec and code
- Collect feedback on what works

*Phase 3: Scale (ongoing)*
- Specs become part of design docs
- Code reviews check spec compliance
- Tests reference spec properties

### Summary: Your New Workflow

```
Old way:
Requirements → Code → Tests → "Wait, that's not what I meant"

New way:
Requirements → Algebraic Spec → (LLM generates) Tests + Code
                      ↓
              Stakeholder validates spec
                      ↓
              Tests verify code matches spec
```

*The spec is the source of truth.* Code and tests are derived from it.

*LLMs amplify precision.* They can:
- Help formalise vague requirements into specs
- Generate comprehensive tests from equations
- Produce correct implementations from specifications
- Check for logical inconsistencies

*You stay in control* of the *what* (the spec), while delegating
more of the *how* (the implementation).



### Next Steps

1. *Try it:* Take a feature you're working on. Write down its sorts, operations,
   and key equations. See what feels natural and what's awkward.

2. *Experiment with an LLM:* Give it a small spec and ask for tests. See what it produces.

3. *Read deeper:* Pick one reference from the reading list based on what interests you most:
   - Want formalism? → Guttag's papers on algebraic ADTs[^guttag]
   - Want practical tools? → Jackson's "Software Abstractions" + Alloy[^jackson]
   - Want state-based? → Lamport's TLA+ book[^lamport]

4. *Eventually: Join a community:* TLA+, Alloy, and formal methods communities are welcoming.
   Lots of practitioners sharing real-world experiences.

The goal isn't mathematical perfection. But it is *clarity about what your code should do*,
precise enough that both humans and LLMs can reason about it.




[^guttag]: The core idea is to treat data types as a mathematical theory.
An abstract data type is defined by a set of sorts, a set of operations,
and	a set of axioms (equations). Meaning precedes implementation.
A program is correct if it is a model of the specification.
This is deeply influenced by algebra and model theory.

[^jackson]: Alloy is a lightweight relational logic with bounded model
checking. You describe sets, relations, and constraints.
Then the tool searches for counterexamples within a finite scope.
Design is the act of excluding bad worlds. You do not prove correctness;
you aggressively hunt for small counterexamples.
This is a fundamentally falsificationist stance.
Alloy becomes a conversational design partner rather than a niche tool.

[^lamport]: Lamport’s TLA+ (Temporal Logic of Actions) models systems as
states, actions (state transitions), and temporal properties over executions.
You do not write code; you write a mathematical description of how the system may evolve.
Concurrency, distribution, and time are fundamental.
You cannot reason about such systems by reading code alone.
Correctness is about behaviors, not functions.
This lowers the barrier without weakening the formal core.
