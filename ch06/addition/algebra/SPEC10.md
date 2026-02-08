

SPECIFICATION: CourseEnrollmentSystem v1.0

IMPORTS:
  NaturalNumbers, Sets, Booleans

SORTS:
  State
  StudentID
  CourseID
  Student
  Course
  EnrollmentStatus = Enrolled | Waitlisted | Completed | Dropped
  Result = Success | CourseFull | AlreadyEnrolled | PrerequisitesNotMet | 
           NotEnrolled | HasDependentEnrollments

STATE: State

OPERATIONS:
  // Constructors
  emptyState: → State
  
  // Student Management
  registerStudent: State × String → State × StudentID
  
  // Course Management  
  createCourse: State × String × Nat → State × CourseID
    // createCourse(state, courseName, maxCapacity) → (newState, courseID)
  
  setPrerequisites: State × CourseID × Set(CourseID) → State
  
  // Enrollment Operations (Commands)
  enroll: State × StudentID × CourseID → State × Result
  drop: State × StudentID × CourseID → State × Result
  completeCourse: State × StudentID × CourseID → State × Result
  
  // Query Operations
  isEnrolled: State × StudentID × CourseID → Bool
  hasCompleted: State × StudentID × CourseID → Bool
  currentEnrollment: State × CourseID → Nat
  capacity: State × CourseID → Nat
  isFull: State × CourseID → Bool
  prerequisites: State × CourseID → Set(CourseID)
  studentCourses: State × StudentID → Set(CourseID)
  completedCourses: State × StudentID → Set(CourseID)
  enrollmentStatus: State × StudentID × CourseID → EnrollmentStatus

DERIVED OPERATIONS:
  // Computed from other operations
  hasMetPrerequisites(s, student, course) =
    prerequisites(s, course) ⊆ completedCourses(s, student)
  
  availableSpots(s, course) = 
    capacity(s, course) - currentEnrollment(s, course)
  
  isFull(s, course) = 
    currentEnrollment(s, course) ≥ capacity(s, course)
  

