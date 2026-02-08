"""
Course Enrollment System - State Implementation
Based on algebraic specification v1.1

Spec: See ../spec/specification-v1.1.txt
"""

from dataclasses import dataclass, field
from typing import Set, Dict, Optional, Tuple
from enum import Enum
import uuid


class EnrollmentStatus(Enum):
    """Spec: EnrollmentStatus sort"""
    ENROLLED = "enrolled"
    COMPLETED = "completed"
    DROPPED = "dropped"


class ResultType(Enum):
    """Spec: Result sort"""
    SUCCESS = "success"
    COURSE_FULL = "course_full"
    ALREADY_ENROLLED = "already_enrolled"
    PREREQUISITES_NOT_MET = "prerequisites_not_met"
    NOT_ENROLLED = "not_enrolled"
    HAS_DEPENDENT_ENROLLMENTS = "has_dependent_enrollments"
    CYCLE_DETECTED = "cycle_detected"
    CANNOT_DROP_COMPLETED = "cannot_drop_completed"
    COURSE_NOT_FOUND = "course_not_found"
    STUDENT_NOT_FOUND = "student_not_found"


@dataclass
class Result:
    """Result of an operation"""
    success: bool
    result_type: ResultType
    message: str = ""


@dataclass
class Course:
    """Spec: Course sort (internal representation)"""
    id: str
    name: str
    capacity: int
    prerequisites: Set[str] = field(default_factory=set)


@dataclass
class Enrollment:
    """Enrollment record"""
    student_id: str
    course_id: str
    status: EnrollmentStatus


class State:
    """
    Spec: State sort
    
    Immutable state with all operations returning new State instances.
    """
    
    def __init__(self):
        self.students: Dict[str, str] = {}
        self.courses: Dict[str, Course] = {}
        self.enrollments: Dict[Tuple[str, str], Enrollment] = {}
    
    # ========================================================================
    # COMMAND OPERATIONS
    # ========================================================================
    
    def register_student(self, name: str) -> Tuple['State', str]:
        """
        Spec: registerStudent: State × String → State × StudentID
        """
        student_id = str(uuid.uuid4())
        new_state = self._copy()
        new_state.students[student_id] = name
        return new_state, student_id
    
    def create_course(self, name: str, capacity: int) -> Tuple['State', str]:
        """
        Spec: createCourse: State × String × Nat → State × CourseID
        Equation EQ1: capacity(createCourse(s, name, cap), courseID) = cap
        """
        if capacity < 0:
            raise ValueError("Capacity must be non-negative")
        
        course_id = str(uuid.uuid4())
        new_state = self._copy()
        new_state.courses[course_id] = Course(
            id=course_id,
            name=name,
            capacity=capacity,
            prerequisites=set()
        )
        return new_state, course_id
    
    def set_prerequisites(
        self, 
        course_id: str, 
        prerequisites: Set[str]
    ) -> Tuple['State', Result]:
        """
        Spec: setPrerequisites: State × CourseID × Set(CourseID) → State × Result
        PRE: courseExists(s, course)
        POST: Check for cycles, enrolled students still meet prerequisites
        """
        if not self.course_exists(course_id):
            return self, Result(False, ResultType.COURSE_NOT_FOUND, "Course not found")
        
        if self._would_create_cycle(course_id, prerequisites):
            return self, Result(False, ResultType.CYCLE_DETECTED, "Would create cycle")
        
        new_state = self._copy()
        new_state.courses[course_id].prerequisites = prerequisites.copy()
        
        # Verify enrolled students still meet prerequisites
        for (student_id, cid), enrollment in new_state.enrollments.items():
            if cid == course_id and enrollment.status == EnrollmentStatus.ENROLLED:
                if not new_state._has_met_prerequisites(student_id, course_id):
                    return self, Result(
                        False, 
                        ResultType.PREREQUISITES_NOT_MET,
                        "Enrolled students would not meet new prerequisites"
                    )
        
        return new_state, Result(True, ResultType.SUCCESS)
    
    def enroll(self, student_id: str, course_id: str) -> Tuple['State', Result]:
        """
        Spec: enroll: State × StudentID × CourseID → State × Result
        PRE: studentExists ∧ courseExists
        POST: If Success, isEnrolled = true ∧ currentEnrollment increased by 1
        Equation EQ3: currentEnrollment(s', c) = currentEnrollment(s, c) + 1
        Invariants: INV1, INV2, INV5
        """
        if not self.student_exists(student_id):
            return self, Result(False, ResultType.STUDENT_NOT_FOUND, "Student not found")
        
        if not self.course_exists(course_id):
            return self, Result(False, ResultType.COURSE_NOT_FOUND, "Course not found")
        
        if self.is_enrolled(student_id, course_id):
            return self, Result(False, ResultType.ALREADY_ENROLLED, "Already enrolled")
        
        if not self._has_met_prerequisites(student_id, course_id):
            prereqs = list(self.prerequisites(course_id))
            return self, Result(
                False, 
                ResultType.PREREQUISITES_NOT_MET,
                f"Prerequisites not met: {', '.join(prereqs)}"
            )
        
        if self.is_full(course_id):
            return self, Result(False, ResultType.COURSE_FULL, "Course is full")
        
        new_state = self._copy()
        new_state.enrollments[(student_id, course_id)] = Enrollment(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.ENROLLED
        )
        
        return new_state, Result(True, ResultType.SUCCESS)
    
    def drop(self, student_id: str, course_id: str) -> Tuple['State', Result]:
        """
        Spec: drop: State × StudentID × CourseID → State × Result
        POST: If Success, enrollment count decreased by 1
        Equation EQ4: currentEnrollment(s', c) = currentEnrollment(s, c) - 1
        """
        if not self.student_exists(student_id):
            return self, Result(False, ResultType.STUDENT_NOT_FOUND, "Student not found")
        
        if not self.course_exists(course_id):
            return self, Result(False, ResultType.COURSE_NOT_FOUND, "Course not found")
        
        key = (student_id, course_id)
        if key not in self.enrollments:
            return self, Result(False, ResultType.NOT_ENROLLED, "Not enrolled")
        
        enrollment = self.enrollments[key]
        
        if enrollment.status == EnrollmentStatus.COMPLETED:
            return self, Result(
                False, 
                ResultType.CANNOT_DROP_COMPLETED,
                "Cannot drop completed course"
            )
        
        if enrollment.status != EnrollmentStatus.ENROLLED:
            return self, Result(False, ResultType.NOT_ENROLLED, "Not enrolled")
        
        if self._has_dependent_enrollments(student_id, course_id):
            return self, Result(
                False,
                ResultType.HAS_DEPENDENT_ENROLLMENTS,
                "Course is prerequisite for other enrolled courses"
            )
        
        new_state = self._copy()
        new_state.enrollments[key] = Enrollment(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.DROPPED
        )
        
        return new_state, Result(True, ResultType.SUCCESS)
    
    def complete_course(
        self, 
        student_id: str, 
        course_id: str
    ) -> Tuple['State', Result]:
        """
        Spec: completeCourse: State × StudentID × CourseID → State × Result
        PRE: isEnrolled(s, student, course) = true
        POST: hasCompleted(s', student, course) = true
        Equation EQ5: completedCourses(s', st) = completedCourses(s, st) ∪ {c}
        """
        if not self.is_enrolled(student_id, course_id):
            return self, Result(
                False,
                ResultType.NOT_ENROLLED,
                "Must be enrolled to complete"
            )
        
        new_state = self._copy()
        new_state.enrollments[(student_id, course_id)] = Enrollment(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.COMPLETED
        )
        
        return new_state, Result(True, ResultType.SUCCESS)
    
    # ========================================================================
    # QUERY OPERATIONS
    # ========================================================================
    
    def is_enrolled(self, student_id: str, course_id: str) -> bool:
        """
        Spec: isEnrolled: State × StudentID × CourseID → Bool
        Invariant INV2: isEnrolled ⟺ status = Enrolled
        """
        key = (student_id, course_id)
        return (key in self.enrollments and 
                self.enrollments[key].status == EnrollmentStatus.ENROLLED)
    
    def has_completed(self, student_id: str, course_id: str) -> bool:
        """Spec: hasCompleted: State × StudentID × CourseID → Bool"""
        key = (student_id, course_id)
        return (key in self.enrollments and 
                self.enrollments[key].status == EnrollmentStatus.COMPLETED)
    
    def current_enrollment(self, course_id: str) -> int:
        """
        Spec: currentEnrollment: State × CourseID → Nat
        Counts students with Enrolled status
        """
        return sum(
            1 for (_, cid), enrollment in self.enrollments.items()
            if cid == course_id and enrollment.status == EnrollmentStatus.ENROLLED
        )
    
    def capacity(self, course_id: str) -> int:
        """
        Spec: capacity: State × CourseID → Nat
        Equation EQ1: capacity is immutable once set
        """
        return self.courses[course_id].capacity
    
    def is_full(self, course_id: str) -> bool:
        """
        Spec DERIVED: isFull(s, course) = 
                      currentEnrollment(s, course) ≥ capacity(s, course)
        """
        return self.current_enrollment(course_id) >= self.capacity(course_id)
    
    def prerequisites(self, course_id: str) -> Set[str]:
        """Spec: prerequisites: State × CourseID → Set(CourseID)"""
        return self.courses[course_id].prerequisites.copy()
    
    def student_courses(self, student_id: str) -> Set[str]:
        """Spec: studentCourses: State × StudentID → Set(CourseID)"""
        return {
            cid for (sid, cid), enrollment in self.enrollments.items()
            if sid == student_id and enrollment.status == EnrollmentStatus.ENROLLED
        }
    
    def completed_courses(self, student_id: str) -> Set[str]:
        """Spec: completedCourses: State × StudentID → Set(CourseID)"""
        return {
            cid for (sid, cid), enrollment in self.enrollments.items()
            if sid == student_id and enrollment.status == EnrollmentStatus.COMPLETED
        }
    
    def student_exists(self, student_id: str) -> bool:
        """Spec: studentExists: State × StudentID → Bool"""
        return student_id in self.students
    
    def course_exists(self, course_id: str) -> bool:
        """Spec: courseExists: State × CourseID → Bool"""
        return course_id in self.courses
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _has_met_prerequisites(self, student_id: str, course_id: str) -> bool:
        """
        Spec DERIVED: hasMetPrerequisites(s, student, course) =
                      prerequisites(s, course) ⊆ completedCourses(s, student)
        """
        prereqs = self.prerequisites(course_id)
        completed = self.completed_courses(student_id)
        return prereqs.issubset(completed)
    
    def _has_dependent_enrollments(self, student_id: str, course_id: str) -> bool:
        """
        Spec DERIVED: hasDependentEnrollments(s, student, course) =
                      exists c in studentCourses(s, student) where
                        course ∈ prerequisites(s, c)
        """
        enrolled = self.student_courses(student_id)
        for enrolled_course in enrolled:
            if course_id in self.prerequisites(enrolled_course):
                return True
        return False
    
    def _would_create_cycle(self, course_id: str, new_prereqs: Set[str]) -> bool:
        """
        Spec: wouldCreateCycle: State × CourseID × Set(CourseID) → Bool
        """
        return course_id in self._transitive_prerequisites(new_prereqs)
    
    def _transitive_prerequisites(self, courses: Set[str]) -> Set[str]:
        """
        Spec: transitivePrerequisites: State × Set(CourseID) → Set(CourseID)
        Compute transitive closure using BFS
        """
        result = set(courses)
        queue = list(courses)
        
        while queue:
            course = queue.pop(0)
            if course in self.courses:
                prereqs = self.courses[course].prerequisites
                for prereq in prereqs:
                    if prereq not in result:
                        result.add(prereq)
                        queue.append(prereq)
        
        return result
    
    def _copy(self) -> 'State':
        """Deep copy for immutable operations"""
        new_state = State()
        new_state.students = self.students.copy()
        new_state.courses = {
            cid: Course(
                id=course.id,
                name=course.name,
                capacity=course.capacity,
                prerequisites=course.prerequisites.copy()
            )
            for cid, course in self.courses.items()
        }
        new_state.enrollments = self.enrollments.copy()
        return new_state
    
    def check_all_invariants(self):
        """
        Verify all specification invariants
        Raises AssertionError if any invariant is violated
        """
        # INV1: No over-enrollment
        for course_id in self.courses:
            assert self.current_enrollment(course_id) <= self.capacity(course_id), \
                f"INV1 violated: Course {course_id} over-enrolled"
        
        # INV2: Enrollment status consistency
        for (student_id, course_id), enrollment in self.enrollments.items():
            enrolled = (enrollment.status == EnrollmentStatus.ENROLLED)
            assert self.is_enrolled(student_id, course_id) == enrolled, \
                f"INV2 violated: Status inconsistency"
        
        # INV3: Completion implies prerequisites met
        for (student_id, course_id), enrollment in self.enrollments.items():
            if enrollment.status == EnrollmentStatus.COMPLETED:
                prereqs = self.prerequisites(course_id)
                for prereq in prereqs:
                    assert self.has_completed(student_id, prereq), \
                        f"INV3 violated: Completed without prerequisite"
        
        # INV4: No cycles
        for course_id in self.courses:
            transitive = self._transitive_prerequisites({course_id})
            assert course_id not in transitive, \
                f"INV4 violated: Cycle detected"
        
        # INV5: Enrolled students meet prerequisites
        for (student_id, course_id), enrollment in self.enrollments.items():
            if enrollment.status == EnrollmentStatus.ENROLLED:
                assert self._has_met_prerequisites(student_id, course_id), \
                    f"INV5 violated: Enrolled without prerequisites"
