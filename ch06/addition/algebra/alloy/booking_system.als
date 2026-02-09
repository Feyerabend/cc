/**
 * Meeting Room Booking System - Alloy Specification
 * 
 * Based on the algebraic specification from the document.
 * This is an executable model that can find violations of invariants
 * and verify properties of the booking system.
 */

module booking_system

/******************************************************************************
 * SORTS (Signatures in Alloy)
 ******************************************************************************/

sig User {}
sig Room {}

sig Time {
  succ: lone Time  // successor - discrete time steps (renamed to avoid conflict with integer/next)
}

// Facts about time structure
fact TimeOrdering {
  // Time is acyclic - no time loops
  no t: Time | t in t.^succ
  
  // Each time can be reached from some "start" time
  // (This ensures we have a linear timeline)
}

sig TimeSlot {
  start: one Time,
  end: one Time
} {
  // TimeSlot well-formedness: end comes after start (or they could be equal for instant slots)
  end in start.*succ  // * means reflexive transitive (includes start itself)
  // Ensure they're actually different for non-trivial slots
  start != end  // Force proper duration
}

abstract sig Result {}
one sig Success extends Result {}
one sig RoomUnavailable extends Result {}
one sig PermissionDenied extends Result {}

sig BookingID {}

sig Booking {
  id: one BookingID,
  room: one Room,
  user: one User,
  slot: one TimeSlot
}

sig State {
  bookings: set Booking,
  permissions: User -> set Room  // which users can book which rooms
}

/******************************************************************************
 * OPERATIONS (as predicates)
 ******************************************************************************/

/**
 * Spec: overlaps predicate
 * 
 * Two time slots overlap if they share any time point.
 * They DON'T overlap only if one completely ends before the other starts.
 * 
 * Key insight: "A comes before B" means "B is reachable from A by following succ"
 * which is written as: B in A.^succ (or B in A.*succ if equal times count)
 * 
 * No overlap when:
 * - s1 ends before or at s2 starts: s2.start in s1.end.*succ (s2 starts ≥ s1 ends)
 * - s2 ends before or at s1 starts: s1.start in s2.end.*succ (s1 starts ≥ s2 ends)
 */
pred overlaps[s1, s2: TimeSlot] {
  // They overlap if NEITHER slot ends before/at the other starts
  not (s2.start in s1.end.*succ or s1.start in s2.end.*succ)
}

/**
 * Test: a slot should always overlap with itself
 */
pred testOverlapsSelf {
  some ts: TimeSlot | overlaps[ts, ts]
}

/**
 * Test: slots that share the same time should overlap
 */
pred testOverlapsSameTime {
  some ts1, ts2: TimeSlot | {
    ts1.start = ts2.start
    ts1.end = ts2.end
    overlaps[ts1, ts2]
  }
}

/**
 * Spec: isAvailable query
 * 
 * isAvailable(state, room, slot) = 
 *   not exists booking where
 *     bookingRoom(booking) = room and overlaps(bookingSlot(booking), slot)
 */
pred isAvailable[s: State, r: Room, ts: TimeSlot] {
  no b: s.bookings | b.room = r and overlaps[b.slot, ts]
}

/**
 * Spec: hasPermission query
 */
pred hasPermission[s: State, u: User, r: Room] {
  r in s.permissions[u]
}

/**
 * Spec: bookRoom operation
 * 
 * bookRoom: State × User × Room × TimeSlot → State × Result
 * 
 * PRE: hasPermission(state, user, room) = true
 * 
 * POST: 
 *   CASE result OF
 *     Success:
 *       - isAvailable(newState, room, slot) = false
 *       - A new booking exists with the given user, room, slot
 *       - All other bookings unchanged
 *     RoomUnavailable:
 *       - State unchanged
 *       - isAvailable(state, room, slot) = false
 *     PermissionDenied:
 *       - State unchanged
 *       - hasPermission(state, user, room) = false
 */
pred bookRoom[s, s': State, u: User, r: Room, ts: TimeSlot, result: Result] {
  // Determine result based on pre-conditions and update state accordingly
  
  (not hasPermission[s, u, r]) => {
    // Case 1: Permission denied
    result = PermissionDenied
    s' = s  // state unchanged
  } else {
    (not isAvailable[s, r, ts]) => {
      // Case 2: Room unavailable (has permission but room is booked)
      result = RoomUnavailable
      s' = s  // state unchanged
    } else {
      // Case 3: Success (has permission and room is available)
      result = Success
      
      // Create new booking with the exact parameters provided
      some newBooking: Booking {
        newBooking.user = u
        newBooking.room = r
        newBooking.slot = ts
        newBooking not in s.bookings
        
        // POST-CONDITION: new state has the new booking
        s'.bookings = s.bookings + newBooking
        s'.permissions = s.permissions
      }
    }
  }
}

/**
 * Spec: cancelBooking operation
 * 
 * Users can only cancel their own bookings
 */
pred cancelBooking[s, s': State, u: User, bid: BookingID, result: Result] {
  some b: s.bookings | b.id = bid implies {
    // Found the booking
    let booking = s.bookings & id.bid {
      // Check if user owns this booking
      (booking.user = u) implies {
        result = Success
        s'.bookings = s.bookings - booking
        s'.permissions = s.permissions
      } else {
        result = PermissionDenied
        s' = s
      }
    }
  } else {
    // Booking doesn't exist
    result = RoomUnavailable  // reusing this for "not found"
    s' = s
  }
}

/******************************************************************************
 * INVARIANTS
 ******************************************************************************/

/**
 * Spec: INVARIANT - No double-booking
 * 
 * for all state, room, slot, booking1, booking2:
 *   (booking1 ≠ booking2) and
 *   (bookingRoom(booking1) = room) and
 *   (bookingRoom(booking2) = room) and
 *   overlaps(slot1, slot2)
 *   implies FALSE
 */
pred NoDoubleBooking[s: State] {
  no disj b1, b2: s.bookings | 
    b1.room = b2.room and overlaps[b1.slot, b2.slot]
}

/**
 * Spec: Every booking has an owner
 */
pred EveryBookingHasOwner[s: State] {
  all b: s.bookings | some b.user
}

/**
 * Spec: Booking IDs are unique
 */
pred UniqueBookingIDs[s: State] {
  all disj b1, b2: s.bookings | b1.id != b2.id
}

/**
 * Combined well-formedness predicate for states
 */
pred WellFormedState[s: State] {
  NoDoubleBooking[s]
  EveryBookingHasOwner[s]
  UniqueBookingIDs[s]
}

/******************************************************************************
 * SYSTEM DYNAMICS
 ******************************************************************************/

/**
 * Initial state: no bookings, some permissions granted
 */
pred init[s: State] {
  no s.bookings
  some s.permissions  // at least some users have permissions
}

/**
 * State transitions: book or cancel
 */
pred transition[s, s': State] {
  some u: User, r: Room, ts: TimeSlot, result: Result |
    bookRoom[s, s', u, r, ts, result]
  or
  some u: User, bid: BookingID, result: Result |
    cancelBooking[s, s', u, bid, result]
}

/**
 * System trace: initial state followed by transitions
 */
pred trace {
  some s0: State | {
    init[s0]
    WellFormedState[s0]
    
    all s: State - s0 | {
      some s_prev: State | transition[s_prev, s]
      WellFormedState[s]
    }
  }
}

/******************************************************************************
 * ASSERTIONS TO CHECK
 ******************************************************************************/

/**
 * Simple test: if a booking exists for a room+slot, the room should be unavailable
 */
pred testBasicAvailability {
  some s: State, r: Room, ts: TimeSlot | {
    // There's a booking for this room and timeslot
    some b: s.bookings | b.room = r and b.slot = ts
    // But the room shows as available (this should be impossible!)
    isAvailable[s, r, ts]
  }
}

/**
 * ASSERTION: Successfully booking makes room unavailable
 * 
 * This is the main POST-CONDITION from the spec
 */
assert BookingMakesRoomUnavailable {
  all s, s': State, u: User, r: Room, ts: TimeSlot |
    (bookRoom[s, s', u, r, ts, Success]) implies
      not isAvailable[s', r, ts]
}

/**
 * ASSERTION: No double-booking invariant is maintained
 */
assert NoDoubleBookingMaintained {
  all s: State | WellFormedState[s] implies NoDoubleBooking[s]
}

/**
 * ASSERTION: Cannot book without permission
 * 
 * This verifies the PRE-CONDITION is enforced
 */
assert CannotBookWithoutPermission {
  all s, s': State, u: User, r: Room, ts: TimeSlot, result: Result |
    (bookRoom[s, s', u, r, ts, result] and not hasPermission[s, u, r]) 
      implies result = PermissionDenied
}

/**
 * ASSERTION: Successful booking requires permission AND availability
 */
assert SuccessRequiresPermissionAndAvailability {
  all s, s': State, u: User, r: Room, ts: TimeSlot |
    (bookRoom[s, s', u, r, ts, Success]) implies
      (hasPermission[s, u, r] and isAvailable[s, r, ts])
}

/**
 * ASSERTION: Bookings from different users for same room don't overlap
 */
assert DifferentUsersSameRoomNoOverlap {
  all s: State, disj u1, u2: User |
    no disj b1, b2: s.bookings |
      b1.user = u1 and b2.user = u2 and
      b1.room = b2.room and
      overlaps[b1.slot, b2.slot]
}

/**
 * ASSERTION: Can only cancel own bookings
 */
assert CanOnlyCancelOwnBookings {
  all s, s': State, u: User, bid: BookingID |
    let booking = s.bookings & id.bid |
      (some booking and booking.user != u) implies
        no result: Result | 
          (cancelBooking[s, s', u, bid, result] and result = Success)
}

/******************************************************************************
 * CHECKS - Run these to verify the system
 ******************************************************************************/

// Check each assertion for counterexamples
check BookingMakesRoomUnavailable for 5
check NoDoubleBookingMaintained for 5
check CannotBookWithoutPermission for 5
check SuccessRequiresPermissionAndAvailability for 5
check DifferentUsersSameRoomNoOverlap for 5
check CanOnlyCancelOwnBookings for 5

/******************************************************************************
 * PREDICATES TO RUN - Generate example scenarios
 ******************************************************************************/

/**
 * Show a scenario where a booking succeeds
 */
pred showSuccessfulBooking {
  some s, s': State, u: User, r: Room, ts: TimeSlot |
    bookRoom[s, s', u, r, ts, Success]
}

/**
 * Show a scenario where a booking fails due to no permission
 */
pred showPermissionDenied {
  some s, s': State, u: User, r: Room, ts: TimeSlot |
    bookRoom[s, s', u, r, ts, PermissionDenied]
}

/**
 * Show a scenario with overlapping booking attempt
 */
pred showDoubleBookingAttempt {
  some s, s1, s2: State, u1, u2: User, r: Room, ts1, ts2: TimeSlot | {
    bookRoom[s, s1, u1, r, ts1, Success]
    overlaps[ts1, ts2]
    bookRoom[s1, s2, u2, r, ts2, RoomUnavailable]
  }
}

/**
 * Show a complex scenario with multiple bookings
 */
pred showComplexScenario {
  some disj s0, s1, s2, s3: State,
       disj u1, u2, u3: User,
       disj r1, r2: Room,
       disj ts1, ts2, ts3: TimeSlot | {
    
    // Initial state
    init[s0]
    
    // User 1 books room 1
    bookRoom[s0, s1, u1, r1, ts1, Success]
    
    // User 2 books room 2 (different room, should succeed)
    bookRoom[s1, s2, u2, r2, ts2, Success]
    
    // User 3 tries to book room 1 at overlapping time (should fail)
    overlaps[ts1, ts3]
    bookRoom[s2, s3, u3, r1, ts3, RoomUnavailable]
    
    // All states are well-formed
    WellFormedState[s0]
    WellFormedState[s1]
    WellFormedState[s2]
    WellFormedState[s3]
  }
}

// Run these to see examples
run showSuccessfulBooking for 4
run showPermissionDenied for 4
run showDoubleBookingAttempt for 5
run showComplexScenario for 6

// DEBUG: This should find NO instances (if it finds one, our logic is broken)
run testBasicAvailability for 3

/******************************************************************************
 * USAGE NOTES:
 * 
 * 1. Install Alloy Analyzer from: https://alloytools.org/
 * 
 * 2. Open this file in Alloy Analyzer
 * 
 * 3. Execute "check" commands to verify assertions:
 *    - If no counterexample is found, the property holds (within scope)
 *    - If a counterexample is found, Alloy shows you the violation
 * 
 * 4. Execute "run" commands to generate example scenarios:
 *    - These show valid instances of the system
 *    - Use the visualizer to explore states and transitions
 * 
 * 5. Scope (e.g., "for 5") limits the search space:
 *    - "for 5" means up to 5 instances of each signature
 *    - Larger scopes find more bugs but take longer
 * 
 * 6. Common workflow:
 *    a) Run examples to understand the model
 *    b) Check assertions to find bugs
 *    c) If counterexample found, examine it in visualizer
 *    d) Fix the specification or implementation
 *    e) Repeat
 ******************************************************************************/
