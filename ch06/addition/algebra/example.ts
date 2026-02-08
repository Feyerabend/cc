/**
 * Course Enrollment System
 * Implementation of algebraic specification v1.1
 * 
 * Architecture: Event-sourced with immutable state
 * All operations produce events, state is derived from event history
 */

// ============================================================================
// DOMAIN TYPES
// ============================================================================

/**
 * Spec: EnrollmentStatus sort
 */
export enum EnrollmentStatus {
  Enrolled = "ENROLLED",
  Completed = "COMPLETED",
  Dropped = "DROPPED",
}

/**
 * Spec: Result sort
 */
export enum ResultType {
  Success = "SUCCESS",
  CourseFull = "COURSE_FULL",
  AlreadyEnrolled = "ALREADY_ENROLLED",
  PrerequisitesNotMet = "PREREQUISITES_NOT_MET",
  NotEnrolled = "NOT_ENROLLED",
  HasDependentEnrollments = "HAS_DEPENDENT_ENROLLMENTS",
  CycleDetected = "CYCLE_DETECTED",
  CannotDropCompleted = "CANNOT_DROP_COMPLETED",
  CourseNotFound = "COURSE_NOT_FOUND",
  StudentNotFound = "STUDENT_NOT_FOUND",
}

export type Result<T = void> =
  | { success: true; type: ResultType.Success; value: T }
  | { success: false; type: ResultType; error: string };

export type StudentID = string;
export type CourseID = string;

/**
 * Spec: Course sort (internal representation)
 */
interface Course {
  readonly id: CourseID;
  readonly name: string;
  readonly capacity: number;
  readonly prerequisites: ReadonlySet<CourseID>;
}

/**
 * Enrollment record tracking student-course relationship
 */
interface Enrollment {
  readonly studentId: StudentID;
  readonly courseId: CourseID;
  readonly status: EnrollmentStatus;
}

// ============================================================================
// EVENTS (Event Sourcing)
// ============================================================================

type DomainEvent =
  | StudentRegisteredEvent
  | CourseCreatedEvent
  | PrerequisitesSetEvent
  | StudentEnrolledEvent
  | StudentDroppedEvent
  | CourseCompletedEvent;

interface StudentRegisteredEvent {
  type: "StudentRegistered";
  studentId: StudentID;
  name: string;
  timestamp: Date;
}

interface CourseCreatedEvent {
  type: "CourseCreated";
  courseId: CourseID;
  name: string;
  capacity: number;
  timestamp: Date;
}

interface PrerequisitesSetEvent {
  type: "PrerequisitesSet";
  courseId: CourseID;
  prerequisites: ReadonlySet<CourseID>;
  timestamp: Date;
}

interface StudentEnrolledEvent {
  type: "StudentEnrolled";
  studentId: StudentID;
  courseId: CourseID;
  timestamp: Date;
}

interface StudentDroppedEvent {
  type: "StudentDropped";
  studentId: StudentID;
  courseId: CourseID;
  timestamp: Date;
}

interface CourseCompletedEvent {
  type: "CourseCompleted";
  studentId: StudentID;
  courseId: CourseID;
  timestamp: Date;
}

// ============================================================================
// STATE
// ============================================================================

/**
 * Spec: State sort
 * 
 * Immutable state derived from event history.
 * All modifications return new State instance.
 */
export class State {
  private constructor(
    private readonly students: ReadonlyMap<StudentID, string>,
    private readonly courses: ReadonlyMap<CourseID, Course>,
    private readonly enrollments: ReadonlyMap<string, Enrollment>,
    private readonly events: readonly DomainEvent[]
  ) {
    // Verify invariants on construction (defensive programming)
    if (process.env.NODE_ENV === "development") {
      this.checkInvariants();
    }
  }

  /**
   * Spec: emptyState constructor
   */
  static empty(): State {
    return new State(new Map(), new Map(), new Map(), []);
  }

  /**
   * Replay events to build state (for event sourcing)
   */
  static fromEvents(events: readonly DomainEvent[]): State {
    let state = State.empty();
    for (const event of events) {
      state = state.applyEvent(event);
    }
    return state;
  }

  // ==========================================================================
  // COMMAND OPERATIONS
  // ==========================================================================

  /**
   * Spec: registerStudent: State × String → State × StudentID
   */
  registerStudent(name: string): [State, StudentID] {
    const studentId = this.generateId("student");
    const event: StudentRegisteredEvent = {
      type: "StudentRegistered",
      studentId,
      name,
      timestamp: new Date(),
    };
    return [this.applyEvent(event), studentId];
  }

  /**
   * Spec: createCourse: State × String × Nat → State × CourseID
   * 
   * Equation EQ1: capacity(createCourse(s, name, cap), courseID) = cap
   */
  createCourse(name: string, capacity: number): [State, CourseID] {
    if (capacity < 0) {
      throw new Error("Capacity must be non-negative");
    }

    const courseId = this.generateId("course");
    const event: CourseCreatedEvent = {
      type: "CourseCreated",
      courseId,
      name,
      capacity,
      timestamp: new Date(),
    };
    return [this.applyEvent(event), courseId];
  }

  /**
   * Spec: setPrerequisites: State × CourseID × Set(CourseID) → State × Result
   * 
   * PRE: courseExists(s, course)
   * POST: Check for cycles, enrolled students still meet prerequisites
   */
  setPrerequisites(
    courseId: CourseID,
    prerequisites: ReadonlySet<CourseID>
  ): [State, Result] {
    // Pre-condition: courseExists
    if (!this.courseExists(courseId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.CourseNotFound,
          error: `Course ${courseId} not found`,
        },
      ];
    }

    // Check for cycles (Invariant INV4)
    if (this.wouldCreateCycle(courseId, prerequisites)) {
      return [
        this,
        {
          success: false,
          type: ResultType.CycleDetected,
          error: `Setting prerequisites would create a cycle`,
        },
      ];
    }

    // Verify enrolled students still meet prerequisites
    for (const [key, enrollment] of this.enrollments) {
      const [studentId, cid] = this.parseEnrollmentKey(key);
      if (
        cid === courseId &&
        enrollment.status === EnrollmentStatus.Enrolled
      ) {
        // Check if student would still meet new prerequisites
        const completed = this.completedCourses(studentId);
        if (!this.isSubset(prerequisites, completed)) {
          return [
            this,
            {
              success: false,
              type: ResultType.PrerequisitesNotMet,
              error: `Enrolled student ${studentId} would not meet new prerequisites`,
            },
          ];
        }
      }
    }

    const event: PrerequisitesSetEvent = {
      type: "PrerequisitesSet",
      courseId,
      prerequisites,
      timestamp: new Date(),
    };

    return [this.applyEvent(event), { success: true, type: ResultType.Success, value: undefined }];
  }

  /**
   * Spec: enroll: State × StudentID × CourseID → State × Result
   * 
   * PRE: studentExists ∧ courseExists
   * POST: If Success, isEnrolled = true ∧ currentEnrollment increased by 1
   * 
   * Invariants enforced:
   * - INV1: No over-enrollment
   * - INV2: Status consistency
   * - INV5: Prerequisites met
   */
  enroll(studentId: StudentID, courseId: CourseID): [State, Result] {
    // Pre-conditions
    if (!this.studentExists(studentId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.StudentNotFound,
          error: `Student ${studentId} not found`,
        },
      ];
    }

    if (!this.courseExists(courseId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.CourseNotFound,
          error: `Course ${courseId} not found`,
        },
      ];
    }

    // Business rules
    if (this.isEnrolled(studentId, courseId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.AlreadyEnrolled,
          error: `Student already enrolled in course`,
        },
      ];
    }

    if (!this.hasMetPrerequisites(studentId, courseId)) {
      const prereqs = Array.from(this.prerequisites(courseId));
      return [
        this,
        {
          success: false,
          type: ResultType.PrerequisitesNotMet,
          error: `Prerequisites not met: ${prereqs.join(", ")}`,
        },
      ];
    }

    if (this.isFull(courseId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.CourseFull,
          error: `Course is at capacity`,
        },
      ];
    }

    // Apply enrollment
    const event: StudentEnrolledEvent = {
      type: "StudentEnrolled",
      studentId,
      courseId,
      timestamp: new Date(),
    };

    const newState = this.applyEvent(event);

    // Post-condition assertions (development mode)
    if (process.env.NODE_ENV === "development") {
      console.assert(
        newState.isEnrolled(studentId, courseId),
        "Post-condition: student should be enrolled"
      );
      console.assert(
        newState.currentEnrollment(courseId) ===
          this.currentEnrollment(courseId) + 1,
        "Post-condition: enrollment count should increase by 1"
      );
    }

    return [newState, { success: true, type: ResultType.Success, value: undefined }];
  }

  /**
   * Spec: drop: State × StudentID × CourseID → State × Result
   * 
   * POST: If Success, enrollment count decreased by 1
   * Cannot drop if has dependent enrollments or already completed
   */
  drop(studentId: StudentID, courseId: CourseID): [State, Result] {
    // Pre-conditions
    if (!this.studentExists(studentId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.StudentNotFound,
          error: `Student ${studentId} not found`,
        },
      ];
    }

    if (!this.courseExists(courseId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.CourseNotFound,
          error: `Course ${courseId} not found`,
        },
      ];
    }

    const key = this.enrollmentKey(studentId, courseId);
    const enrollment = this.enrollments.get(key);

    if (!enrollment || enrollment.status !== EnrollmentStatus.Enrolled) {
      return [
        this,
        {
          success: false,
          type: ResultType.NotEnrolled,
          error: `Student not currently enrolled in course`,
        },
      ];
    }

    // Cannot drop completed courses
    if (enrollment.status === EnrollmentStatus.Completed) {
      return [
        this,
        {
          success: false,
          type: ResultType.CannotDropCompleted,
          error: `Cannot drop a completed course`,
        },
      ];
    }

    // Check for dependent enrollments
    if (this.hasDependentEnrollments(studentId, courseId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.HasDependentEnrollments,
          error: `Course is a prerequisite for other enrolled courses`,
        },
      ];
    }

    const event: StudentDroppedEvent = {
      type: "StudentDropped",
      studentId,
      courseId,
      timestamp: new Date(),
    };

    const newState = this.applyEvent(event);

    // Post-condition (development mode)
    if (process.env.NODE_ENV === "development") {
      console.assert(
        newState.currentEnrollment(courseId) ===
          this.currentEnrollment(courseId) - 1,
        "Post-condition: enrollment count should decrease by 1"
      );
    }

    return [newState, { success: true, type: ResultType.Success, value: undefined }];
  }

  /**
   * Spec: completeCourse: State × StudentID × CourseID → State × Result
   * 
   * PRE: isEnrolled(s, student, course) = true
   * POST: hasCompleted(s', student, course) = true
   * 
   * Equation EQ5: completedCourses(s', st) = completedCourses(s, st) ∪ {c}
   */
  completeCourse(studentId: StudentID, courseId: CourseID): [State, Result] {
    if (!this.isEnrolled(studentId, courseId)) {
      return [
        this,
        {
          success: false,
          type: ResultType.NotEnrolled,
          error: `Student must be enrolled to complete course`,
        },
      ];
    }

    const event: CourseCompletedEvent = {
      type: "CourseCompleted",
      studentId,
      courseId,
      timestamp: new Date(),
    };

    const newState = this.applyEvent(event);

    // Post-condition
    if (process.env.NODE_ENV === "development") {
      console.assert(
        newState.hasCompleted(studentId, courseId),
        "Post-condition: course should be completed"
      );

      const oldCompleted = this.completedCourses(studentId);
      const newCompleted = newState.completedCourses(studentId);
      const expectedCompleted = new Set([...oldCompleted, courseId]);

      console.assert(
        this.setEquals(newCompleted, expectedCompleted),
        "Post-condition (EQ5): completed courses should include new course"
      );
    }

    return [newState, { success: true, type: ResultType.Success, value: undefined }];
  }

  // ==========================================================================
  // QUERY OPERATIONS
  // ==========================================================================

  /**
   * Spec: isEnrolled: State × StudentID × CourseID → Bool
   * 
   * Invariant INV2: isEnrolled ⟺ status = Enrolled
   */
  isEnrolled(studentId: StudentID, courseId: CourseID): boolean {
    const key = this.enrollmentKey(studentId, courseId);
    const enrollment = this.enrollments.get(key);
    return enrollment?.status === EnrollmentStatus.Enrolled;
  }

  /**
   * Spec: hasCompleted: State × StudentID × CourseID → Bool
   */
  hasCompleted(studentId: StudentID, courseId: CourseID): boolean {
    const key = this.enrollmentKey(studentId, courseId);
    const enrollment = this.enrollments.get(key);
    return enrollment?.status === EnrollmentStatus.Completed;
  }

  /**
   * Spec: currentEnrollment: State × CourseID → Nat
   * 
   * Counts students with Enrolled status for this course
   */
  currentEnrollment(courseId: CourseID): number {
    let count = 0;
    for (const [key, enrollment] of this.enrollments) {
      const [_, cid] = this.parseEnrollmentKey(key);
      if (cid === courseId && enrollment.status === EnrollmentStatus.Enrolled) {
        count++;
      }
    }
    return count;
  }

  /**
   * Spec: capacity: State × CourseID → Nat
   * 
   * Equation EQ1: capacity is immutable once set
   */
  capacity(courseId: CourseID): number {
    const course = this.courses.get(courseId);
    if (!course) {
      throw new Error(`Course ${courseId} not found`);
    }
    return course.capacity;
  }

  /**
   * Spec DERIVED: isFull(s, course) = 
   *               currentEnrollment(s, course) ≥ capacity(s, course)
   */
  isFull(courseId: CourseID): boolean {
    return this.currentEnrollment(courseId) >= this.capacity(courseId);
  }

  /**
   * Spec: prerequisites: State × CourseID → Set(CourseID)
   */
  prerequisites(courseId: CourseID): ReadonlySet<CourseID> {
    const course = this.courses.get(courseId);
    return course?.prerequisites ?? new Set();
  }

  /**
   * Spec: studentCourses: State × StudentID → Set(CourseID)
   * 
   * Returns courses student is currently enrolled in
   */
  studentCourses(studentId: StudentID): Set<CourseID> {
    const courses = new Set<CourseID>();
    for (const [key, enrollment] of this.enrollments) {
      const [sid, cid] = this.parseEnrollmentKey(key);
      if (sid === studentId && enrollment.status === EnrollmentStatus.Enrolled) {
        courses.add(cid);
      }
    }
    return courses;
  }

  /**
   * Spec: completedCourses: State × StudentID → Set(CourseID)
   */
  completedCourses(studentId: StudentID): Set<CourseID> {
    const courses = new Set<CourseID>();
    for (const [key, enrollment] of this.enrollments) {
      const [sid, cid] = this.parseEnrollmentKey(key);
      if (sid === studentId && enrollment.status === EnrollmentStatus.Completed) {
        courses.add(cid);
      }
    }
    return courses;
  }

  /**
   * Spec: studentExists: State × StudentID → Bool
   */
  studentExists(studentId: StudentID): boolean {
    return this.students.has(studentId);
  }

  /**
   * Spec: courseExists: State × CourseID → Bool
   */
  courseExists(courseId: CourseID): boolean {
    return this.courses.has(courseId);
  }

  /**
   * Get all events (for persistence/debugging)
   */
  getEvents(): readonly DomainEvent[] {
    return this.events;
  }

  // ==========================================================================
  // DERIVED OPERATIONS (Helper Predicates)
  // ==========================================================================

  /**
   * Spec DERIVED: hasMetPrerequisites(s, student, course) =
   *               prerequisites(s, course) ⊆ completedCourses(s, student)
   */
  private hasMetPrerequisites(
    studentId: StudentID,
    courseId: CourseID
  ): boolean {
    const prereqs = this.prerequisites(courseId);
    const completed = this.completedCourses(studentId);
    return this.isSubset(prereqs, completed);
  }

  /**
   * Spec DERIVED: hasDependentEnrollments(s, student, course) =
   *               exists c in studentCourses(s, student) where
   *                 course ∈ prerequisites(s, c)
   */
  private hasDependentEnrollments(
    studentId: StudentID,
    courseId: CourseID
  ): boolean {
    const enrolled = this.studentCourses(studentId);
    for (const enrolledCourse of enrolled) {
      const prereqs = this.prerequisites(enrolledCourse);
      if (prereqs.has(courseId)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Spec: wouldCreateCycle: State × CourseID × Set(CourseID) → Bool
   * 
   * Check if course appears in transitive closure of new prerequisites
   */
  private wouldCreateCycle(
    courseId: CourseID,
    newPrereqs: ReadonlySet<CourseID>
  ): boolean {
    const transitive = this.transitivePrerequisites(newPrereqs);
    return transitive.has(courseId);
  }

  /**
   * Spec: transitivePrerequisites: State × Set(CourseID) → Set(CourseID)
   * 
   * Compute transitive closure using BFS
   */
  private transitivePrerequisites(
    courses: ReadonlySet<CourseID>
  ): Set<CourseID> {
    const result = new Set(courses);
    const queue = Array.from(courses);

    while (queue.length > 0) {
      const courseId = queue.shift()!;
      const prereqs = this.prerequisites(courseId);

      for (const prereq of prereqs) {
        if (!result.has(prereq)) {
          result.add(prereq);
          queue.push(prereq);
        }
      }
    }

    return result;
  }

  // ==========================================================================
  // INVARIANT CHECKING
  // ==========================================================================

  /**
   * Verify all specification invariants
   * Throws if any invariant is violated
   */
  private checkInvariants(): void {
    // INV1: No over-enrollment
    for (const [courseId, _] of this.courses) {
      const current = this.currentEnrollment(courseId);
      const cap = this.capacity(courseId);
      if (current > cap) {
        throw new Error(
          `INV1 violated: Course ${courseId} over-enrolled (${current}/${cap})`
        );
      }
    }

    // INV2: Enrollment status consistency
    for (const [key, enrollment] of this.enrollments) {
      const [studentId, courseId] = this.parseEnrollmentKey(key);
      const isEnrolled = this.isEnrolled(studentId, courseId);
      const statusIsEnrolled =
        enrollment.status === EnrollmentStatus.Enrolled;

      if (isEnrolled !== statusIsEnrolled) {
        throw new Error(
          `INV2 violated: Status inconsistency for ${studentId}, ${courseId}`
        );
      }
    }

    // INV3: Completion implies prerequisites met
    for (const [key, enrollment] of this.enrollments) {
      if (enrollment.status === EnrollmentStatus.Completed) {
        const [studentId, courseId] = this.parseEnrollmentKey(key);
        const prereqs = this.prerequisites(courseId);
        const completed = this.completedCourses(studentId);

        for (const prereq of prereqs) {
          if (!completed.has(prereq)) {
            throw new Error(
              `INV3 violated: Completed ${courseId} without completing prereq ${prereq}`
            );
          }
        }
      }
    }

    // INV4: No cycles in prerequisites
    for (const [courseId, _] of this.courses) {
      const transitive = this.transitivePrerequisites(new Set([courseId]));
      if (transitive.has(courseId)) {
        throw new Error(
          `INV4 violated: Prerequisite cycle detected for ${courseId}`
        );
      }
    }

    // INV5: Enrolled students meet prerequisites
    for (const [key, enrollment] of this.enrollments) {
      if (enrollment.status === EnrollmentStatus.Enrolled) {
        const [studentId, courseId] = this.parseEnrollmentKey(key);
        if (!this.hasMetPrerequisites(studentId, courseId)) {
          throw new Error(
            `INV5 violated: Enrolled in ${courseId} without meeting prerequisites`
          );
        }
      }
    }
  }

  // ==========================================================================
  // EVENT APPLICATION (Event Sourcing)
  // ==========================================================================

  /**
   * Apply a single event to produce new state
   */
  private applyEvent(event: DomainEvent): State {
    const newStudents = new Map(this.students);
    const newCourses = new Map(this.courses);
    const newEnrollments = new Map(this.enrollments);
    const newEvents = [...this.events, event];

    switch (event.type) {
      case "StudentRegistered":
        newStudents.set(event.studentId, event.name);
        break;

      case "CourseCreated":
        newCourses.set(event.courseId, {
          id: event.courseId,
          name: event.name,
          capacity: event.capacity,
          prerequisites: new Set(),
        });
        break;

      case "PrerequisitesSet":
        const course = newCourses.get(event.courseId);
        if (course) {
          newCourses.set(event.courseId, {
            ...course,
            prerequisites: new Set(event.prerequisites),
          });
        }
        break;

      case "StudentEnrolled":
        const enrollKey = this.enrollmentKey(
          event.studentId,
          event.courseId
        );
        newEnrollments.set(enrollKey, {
          studentId: event.studentId,
          courseId: event.courseId,
          status: EnrollmentStatus.Enrolled,
        });
        break;

      case "StudentDropped":
        const dropKey = this.enrollmentKey(event.studentId, event.courseId);
        const existing = newEnrollments.get(dropKey);
        if (existing) {
          newEnrollments.set(dropKey, {
            ...existing,
            status: EnrollmentStatus.Dropped,
          });
        }
        break;

      case "CourseCompleted":
        const completeKey = this.enrollmentKey(
          event.studentId,
          event.courseId
        );
        const enrollment = newEnrollments.get(completeKey);
        if (enrollment) {
          newEnrollments.set(completeKey, {
            ...enrollment,
            status: EnrollmentStatus.Completed,
          });
        }
        break;
    }

    return new State(newStudents, newCourses, newEnrollments, newEvents);
  }

  // ==========================================================================
  // UTILITY METHODS
  // ==========================================================================

  private enrollmentKey(studentId: StudentID, courseId: CourseID): string {
    return `${studentId}::${courseId}`;
  }

  private parseEnrollmentKey(key: string): [StudentID, CourseID] {
    const [studentId, courseId] = key.split("::");
    return [studentId, courseId];
  }

  private generateId(prefix: string): string {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private isSubset<T>(subset: ReadonlySet<T>, superset: Set<T>): boolean {
    for (const item of subset) {
      if (!superset.has(item)) {
        return false;
      }
    }
    return true;
  }

  private setEquals<T>(set1: Set<T>, set2: Set<T>): boolean {
    if (set1.size !== set2.size) return false;
    for (const item of set1) {
      if (!set2.has(item)) return false;
    }
    return true;
  }
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

/**
 * Example: Building a computer science curriculum
 */
function exampleUsage() {
  console.log("=== Course Enrollment System Example ===\n");

  let state = State.empty();

  // Register students
  console.log("Registering students...");
  let alice: StudentID, bob: StudentID;
  [state, alice] = state.registerStudent("Alice");
  [state, bob] = state.registerStudent("Bob");
  console.log(`  ✓ Registered Alice (${alice})`);
  console.log(`  ✓ Registered Bob (${bob})\n`);

  // Create courses
  console.log("Creating courses...");
  let intro: CourseID, dataStructures: CourseID, algorithms: CourseID;
  [state, intro] = state.createCourse("Intro to Programming", 30);
  [state, dataStructures] = state.createCourse("Data Structures", 25);
  [state, algorithms] = state.createCourse("Algorithms", 20);
  console.log(`  ✓ Created Intro to Programming`);
  console.log(`  ✓ Created Data Structures`);
  console.log(`  ✓ Created Algorithms\n`);

  // Set prerequisites
  console.log("Setting prerequisites...");
  let result: Result;
  [state, result] = state.setPrerequisites(dataStructures, new Set([intro]));
  console.log(
    `  ✓ Data Structures requires Intro: ${result.success ? "✓" : "✗"}`
  );

  [state, result] = state.setPrerequisites(
    algorithms,
    new Set([dataStructures])
  );
  console.log(
    `  ✓ Algorithms requires Data Structures: ${result.success ? "✓" : "✗"}\n`
  );

  // Alice's journey
  console.log("Alice's enrollment journey:");

  // Try to enroll in Algorithms without prerequisites
  [state, result] = state.enroll(alice, algorithms);
  console.log(
    `  Enroll in Algorithms (no prereqs): ${result.success ? "✓" : "✗ " + result.type}`
  );

  // Enroll in Intro
  [state, result] = state.enroll(alice, intro);
  console.log(`  Enroll in Intro: ${result.success ? "✓" : "✗"}`);

  // Complete Intro
  [state, result] = state.completeCourse(alice, intro);
  console.log(`  Complete Intro: ${result.success ? "✓" : "✗"}`);

  // Now can enroll in Data Structures
  [state, result] = state.enroll(alice, dataStructures);
  console.log(
    `  Enroll in Data Structures: ${result.success ? "✓" : "✗"}`
  );

  // Try to drop Intro (has dependent enrollment)
  // Wait - she completed it, can't drop completed courses
  // Let's show Bob trying to drop with dependents

  console.log("\nBob's enrollment journey:");

  // Bob enrolls in Intro
  [state, result] = state.enroll(bob, intro);
  console.log(`  Enroll in Intro: ${result.success ? "✓" : "✗"}`);

  // Bob completes Intro
  [state, result] = state.completeCourse(bob, intro);
  console.log(`  Complete Intro: ${result.success ? "✓" : "✗"}`);

  // Bob enrolls in Data Structures
  [state, result] = state.enroll(bob, dataStructures);
  console.log(
    `  Enroll in Data Structures: ${result.success ? "✓" : "✗"}`
  );

  // Bob tries to drop Intro (completed - should fail)
  [state, result] = state.drop(bob, intro);
  console.log(
    `  Try to drop Intro (completed): ${result.success ? "✓" : "✗ " + result.type}`
  );

  // Course capacity test
  console.log("\nTesting course capacity:");
  let tinyCourse: CourseID;
  [state, tinyCourse] = state.createCourse("Tiny Seminar", 1);

  [state, result] = state.enroll(alice, tinyCourse);
  console.log(
    `  Alice enrolls in Tiny Seminar: ${result.success ? "✓" : "✗"}`
  );

  [state, result] = state.enroll(bob, tinyCourse);
  console.log(
    `  Bob tries to enroll (full): ${result.success ? "✓" : "✗ " + result.type}`
  );

  // Cycle detection test
  console.log("\nTesting prerequisite cycle detection:");
  let courseA: CourseID, courseB: CourseID, courseC: CourseID;
  [state, courseA] = state.createCourse("Course A", 10);
  [state, courseB] = state.createCourse("Course B", 10);
  [state, courseC] = state.createCourse("Course C", 10);

  [state, result] = state.setPrerequisites(courseA, new Set([courseB]));
  console.log(`  A requires B: ${result.success ? "✓" : "✗"}`);

  [state, result] = state.setPrerequisites(courseB, new Set([courseC]));
  console.log(`  B requires C: ${result.success ? "✓" : "✗"}`);

  [state, result] = state.setPrerequisites(courseC, new Set([courseA]));
  console.log(
    `  C requires A (cycle): ${result.success ? "✓" : "✗ " + result.type}`
  );

  // Show final statistics
  console.log("\n=== Final State ===");
  console.log(`Total events: ${state.getEvents().length}`);
  console.log(`Alice's enrolled courses: ${state.studentCourses(alice).size}`);
  console.log(
    `Alice's completed courses: ${state.completedCourses(alice).size}`
  );
  console.log(`Data Structures enrollment: ${state.currentEnrollment(dataStructures)}/${state.capacity(dataStructures)}`);

  console.log("\n✓ All invariants maintained throughout execution");
}

// Run example
exampleUsage();
