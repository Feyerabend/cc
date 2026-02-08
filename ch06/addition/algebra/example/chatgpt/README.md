

---

1. COMPLETENESS

---

### Issue C1: Missing existence preconditions in several operations

Some operations assume entities exist but do not state it uniformly.

* `completeCourse` lacks explicit `studentExists` / `courseExists`.
* Query operations (`isEnrolled`, `capacity`, `prerequisites`, etc.) have no stated domain conditions.

**Risk**
Undefined behavior when called with non-existing students/courses.

**Suggested fix**

```
completeCourse:
  PRE:
    studentExists(s, student) ∧ courseExists(s, course) ∧
    isEnrolled(s, student, course) = true
```

For queries (example pattern):

```
isEnrolled(s, st, c) is defined only if
  studentExists(s, st) ∧ courseExists(s, c)
```

---

### Issue C2: Missing postconditions for non-success results

`completeCourse` only specifies behavior when `result = Success`.

**Risk**
State changes for failure cases are underspecified.

**Suggested fix**

```
POST:
  let (s', result) = completeCourse(s, student, course) in
  CASE result OF
    Success →
      hasCompleted(s', student, course) = true ∧
      completedCourses(s', student) =
        completedCourses(s, student) ∪ {course}
    NotEnrolled → s' = s ∧ ¬isEnrolled(s, student, course)
```

---

### Issue C3: No postcondition for `setPrerequisites` capacity/invariant preservation

`setPrerequisites` does not state that unrelated state is preserved.

**Suggested fix**

```
Success →
  prerequisites(s', course) = newPrereqs ∧
  (∀ c' ≠ course. prerequisites(s', c') = prerequisites(s, c'))
```

---

2. CONSISTENCY

---

### Issue K1: Redundant and conflicting enrollment constraints

`INV3` and `INV5` both constrain prerequisites, but at different lifecycle stages.

* `INV3` applies to **completion**
* `INV5` applies to **enrollment**

**Problem**
If a course has prerequisites, `INV5` requires them completed *during enrollment*, making prerequisite checks at enrollment mandatory, yet `PrerequisitesNotMet` is only handled in `enroll` POST, not as a global invariant.

**Suggested fix (clarify separation)**

```
INV5':
  ∀ s, st, c.
    enrollmentStatus(s, st, c) = Enrolled ⇒
      hasMetPrerequisites(s, st, c)
```

and remove prerequisite reasoning from `INV3`, keeping it completion-only.

---

### Issue K2: `isFull` defined twice

* Declared as query operation
* Redefined in DERIVED OPERATIONS

**Risk**
Potential mismatch if later modified.

**Suggested fix**
Remove primitive declaration and keep only derived form:

```
isFull(s, course) =
  currentEnrollment(s, course) ≥ capacity(s, course)
```

---

### Issue K3: `wouldCreateCycle` vs `INV4`

`INV4` states:

```
c ∉ transitivePrerequisites(s, c)
```

but `wouldCreateCycle` checks:

```
course ∈ transitivePrerequisites(s, newPrereqs)
```

**Problem**
`INV4` assumes acyclicity globally, but `setPrerequisites` only checks local cycles.

**Suggested fix**
Strengthen postcondition:

```
Success →
  prerequisites(s', course) = newPrereqs ∧
  (∀ c'. c' ∉ transitivePrerequisites(s', c'))
```

---

3. EDGE CASES

---

### Issue E1: Dropping enrollment at zero count

`drop` decrements `currentEnrollment` without guarding against zero.

**Invariant violation**

```
currentEnrollment(s, c) ≥ 0
```

is assumed but not stated.

**Suggested fix**
Add invariant:

```
INV6: ∀ s, c. currentEnrollment(s, c) ≥ 0
```

and precondition:

```
drop PRE:
  isEnrolled(s, student, course) = true
```

---

### Issue E2: Completing a course twice

No rule prevents `completeCourse` being applied multiple times.

**Risk**
Idempotency unclear.

**Suggested fix**

```
completeCourse PRE:
  isEnrolled(s, student, course) = true ∧
  ¬hasCompleted(s, student, course)
```

---

### Issue E3: Changing prerequisites after students are enrolled

`setPrerequisites` can invalidate existing enrollments.

**Risk**
Violates `INV5`.

**Suggested fix**

```
setPrerequisites PRE:
  ∀ st.
    isEnrolled(s, st, course) ⇒
      newPrereqs ⊆ completedCourses(s, st)
```

---

4. AMBIGUITIES

---

### Issue A1: Meaning of `studentCourses`

Unclear whether it includes:

* only enrolled courses
* completed courses
* both

**Suggested clarification**

```
studentCourses(s, st) =
  { c | enrollmentStatus(s, st, c) = Enrolled }
```

or explicitly define as union if intended:

```
studentCourses(s, st) =
  enrolledCourses(s, st) ∪ completedCourses(s, st)
```

---

### Issue A2: Relationship between `hasCompleted` and `enrollmentStatus`

Both model completion, but redundancy is not specified.

**Suggested fix**

```
INV7:
  hasCompleted(s, st, c) = true ⇔
    enrollmentStatus(s, st, c) = Completed
```

---

### Issue A3: Behavior of `capacity` on nonexistent courses

No definition given.

**Suggested fix**

```
capacity(s, c) is defined only if courseExists(s, c)
```

---

## SUMMARY

Main weaknesses are:

* underspecified failure behavior,
* overlapping invariants,
* missing guards for lifecycle transitions,
* ambiguous domain definitions.

With the suggested fixes, the specification becomes:

* invariant-preserving,
* lifecycle-complete,
* algebraically tighter,
* and safer under edge conditions.
