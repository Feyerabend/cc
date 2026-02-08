

## 1. Specification Analysis

### 1.1 Completeness (missing or underspecified conditions)

**Missing preconditions**

* `enroll`

  * No explicit precondition that the student is *not already completed* the course.
  * No explicit check for `CourseFull` in PRE (handled implicitly in POST).
* `drop`

  * PRE does not require that the student is enrolled (handled via result).
* `completeCourse`

  * PRE only says `isEnrolled = true`, but does not specify:

    * what happens if the course is already completed
    * whether completion removes enrollment (it probably should)
* `setPrerequisites`

  * No precondition that all `newPrereqs` courses actually exist.

**Missing postconditions**

* `enroll`

  * Does not state that `enrollmentStatus` becomes `Enrolled`.
* `drop`

  * Does not state what happens to `enrollmentStatus` (should become Dropped).
* `completeCourse`

  * Does not state that the student is no longer enrolled afterward.
* `registerStudent`

  * No postcondition defining initial student state.
* `createCourse`

  * No postcondition defining initial enrollment or prerequisites.

---

### 1.2 Consistency (contradictions or tension)

Mostly consistent, but a few **soft conflicts**:

* **INV2 vs lifecycle**

  * `isEnrolled ⇔ enrollmentStatus = Enrolled`
  * But `Completed` exists as a separate status.
  * Spec never explicitly says whether `Completed` implies *not enrolled*.
  * However `drop` forbids dropping completed courses → implies completed ≠ enrolled.

* **INV3 vs INV5**

  * Both enforce prerequisites completion.
  * INV5 is redundant given INV3 + enrollment rules.

* **EQ3 / EQ4 vs CourseFull**

  * Equations assume `Success`; okay, but relies on invariant enforcement elsewhere.

No outright logical contradiction, but lifecycle semantics are underdefined.

---

### 1.3 Edge Cases (invariant violations)

Important edge scenarios:

1. **Completing a course does not decrement enrollment**

   * `completeCourse` does not specify updating `currentEnrollment`.
   * If completion implies unenrollment, INV1 may break unless handled.

2. **Dropping a course with dependents**

   * `hasDependentEnrollments` only checks *current enrollments*, not completed ones.
   * A student could drop a prerequisite after completing a dependent course.

3. **Cycle detection**

   * `transitivePrerequisites` is recursively defined without a base case guard.
   * Requires careful implementation to avoid infinite recursion.

4. **Capacity = 0**

   * Legal per spec (`Nat`), but course can never be enrolled.
   * Must still behave consistently.

5. **Multiple enroll → complete → enroll again**

   * Spec does not forbid re-enrolling in a completed course.

---

### 1.4 Ambiguities (needs clarification)

Key ambiguous points:

* Does **completion automatically remove enrollment**?
* Can a student **enroll in a completed course again**?
* Should `drop` change status to `Dropped` or delete enrollment entirely?
* Are **prerequisites immutable once students are enrolled**?
* Should `setPrerequisites` fail if students are already enrolled?

These don’t break the spec, but different reasonable implementations exist.

---

## 2. Python Reference Implementation

Below is a **faithful, conservative implementation**:

* Completion **removes enrollment**
* Enrollment lifecycle is explicit
* All results are enforced exactly as specified
* Defensive checks preserve invariants

```python
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Set, Tuple


class EnrollmentStatus(Enum):
    ENROLLED = auto()
    COMPLETED = auto()
    DROPPED = auto()


class Result(Enum):
    SUCCESS = auto()
    COURSE_FULL = auto()
    ALREADY_ENROLLED = auto()
    PREREQUISITES_NOT_MET = auto()
    NOT_ENROLLED = auto()
    HAS_DEPENDENT_ENROLLMENTS = auto()
    CYCLE_DETECTED = auto()
    CANNOT_DROP_COMPLETED = auto()
    COURSE_NOT_FOUND = auto()
    STUDENT_NOT_FOUND = auto()


@dataclass
class Course:
    name: str
    capacity: int
    prerequisites: Set[int] = field(default_factory=set)


@dataclass
class State:
    students: Set[int] = field(default_factory=set)
    courses: Dict[int, Course] = field(default_factory=dict)
    enrollments: Dict[Tuple[int, int], EnrollmentStatus] = field(default_factory=dict)
    completed: Dict[int, Set[int]] = field(default_factory=dict)


class CourseEnrollmentSystem:
    def __init__(self):
        self.state = State()
        self._next_student_id = 1
        self._next_course_id = 1

    # ---------- Helpers ----------

    def current_enrollment(self, course_id: int) -> int:
        return sum(
            1 for (st, c), status in self.state.enrollments.items()
            if c == course_id and status == EnrollmentStatus.ENROLLED
        )

    def has_met_prerequisites(self, student_id: int, course_id: int) -> bool:
        completed = self.state.completed.get(student_id, set())
        return self.state.courses[course_id].prerequisites.issubset(completed)

    def transitive_prerequisites(self, course_ids: Set[int], visited=None) -> Set[int]:
        if visited is None:
            visited = set()
        result = set(course_ids)
        for c in course_ids:
            if c in visited:
                continue
            visited.add(c)
            prereqs = self.state.courses.get(c, Course("", 0)).prerequisites
            result |= self.transitive_prerequisites(prereqs, visited)
        return result

    # ---------- Constructors ----------

    def empty_state(self):
        self.__init__()

    def register_student(self, name: str) -> int:
        sid = self._next_student_id
        self._next_student_id += 1
        self.state.students.add(sid)
        self.state.completed[sid] = set()
        return sid

    def create_course(self, name: str, cap: int) -> int:
        cid = self._next_course_id
        self._next_course_id += 1
        self.state.courses[cid] = Course(name, cap)
        return cid

    # ---------- Commands ----------

    def enroll(self, student_id: int, course_id: int) -> Result:
        if student_id not in self.state.students:
            return Result.STUDENT_NOT_FOUND
        if course_id not in self.state.courses:
            return Result.COURSE_NOT_FOUND

        key = (student_id, course_id)
        if key in self.state.enrollments:
            return Result.ALREADY_ENROLLED

        if self.current_enrollment(course_id) >= self.state.courses[course_id].capacity:
            return Result.COURSE_FULL

        if not self.has_met_prerequisites(student_id, course_id):
            return Result.PREREQUISITES_NOT_MET

        self.state.enrollments[key] = EnrollmentStatus.ENROLLED
        return Result.SUCCESS

    def drop(self, student_id: int, course_id: int) -> Result:
        key = (student_id, course_id)
        status = self.state.enrollments.get(key)

        if status is None:
            return Result.NOT_ENROLLED
        if status == EnrollmentStatus.COMPLETED:
            return Result.CANNOT_DROP_COMPLETED

        # dependent enrollments
        for (st, c), s in self.state.enrollments.items():
            if st == student_id and s == EnrollmentStatus.ENROLLED:
                if course_id in self.state.courses[c].prerequisites:
                    return Result.HAS_DEPENDENT_ENROLLMENTS

        del self.state.enrollments[key]
        return Result.SUCCESS

    def complete_course(self, student_id: int, course_id: int) -> Result:
        key = (student_id, course_id)
        if self.state.enrollments.get(key) != EnrollmentStatus.ENROLLED:
            return Result.NOT_ENROLLED

        self.state.enrollments[key] = EnrollmentStatus.COMPLETED
        self.state.completed[student_id].add(course_id)
        return Result.SUCCESS

    def set_prerequisites(self, course_id: int, new_prereqs: Set[int]) -> Result:
        if course_id not in self.state.courses:
            return Result.COURSE_NOT_FOUND

        if course_id in self.transitive_prerequisites(new_prereqs):
            return Result.CYCLE_DETECTED

        self.state.courses[course_id].prerequisites = set(new_prereqs)
        return Result.SUCCESS
```

---

## Final thoughts

* The **spec is solid**, but clearly academic: lifecycle semantics need tightening.
* The implementation above chooses *safe defaults* that preserve invariants.
* If you want, I can:

  * tighten the spec formally (v1.2),
  * generate property-based tests from the invariants,
  * or refactor this into a pure functional model closer to algebraic specs.

Just say the word.
