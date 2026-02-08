"""
Property-based tests for Course Enrollment System
Based on algebraic specification v1.1

Run with: pytest tests.py -v
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from state import State, ResultType


# Test helpers
@st.composite
def state_with_student(draw):
    state = State()
    name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
    state, student_id = state.register_student(name)
    return state, student_id


@st.composite
def state_with_course(draw):
    state = State()
    name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
    capacity = draw(st.integers(min_value=1, max_value=100))
    state, course_id = state.create_course(name, capacity)
    return state, course_id


@st.composite
def state_with_student_and_course(draw):
    state = State()
    student_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
    course_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
    capacity = draw(st.integers(min_value=1, max_value=100))
    
    state, student_id = state.register_student(student_name)
    state, course_id = state.create_course(course_name, capacity)
    
    return state, student_id, course_id


# Equation tests
@given(
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    capacity=st.integers(min_value=0, max_value=1000)
)
def test_eq1_capacity_set_on_creation(name, capacity):
    """Spec EQ1: capacity(createCourse(s, name, cap), courseID) = cap"""
    state = State()
    new_state, course_id = state.create_course(name, capacity)
    assert new_state.capacity(course_id) == capacity


def test_eq2_empty_state_no_enrollments():
    """Spec EQ2: currentEnrollment(emptyState, c) = 0"""
    state = State()
    state, course_id = state.create_course("Test", 10)
    assert state.current_enrollment(course_id) == 0


@given(state_with_student_and_course())
@settings(max_examples=50)
def test_eq3_enrollment_increases_count(args):
    """Spec EQ3: currentEnrollment(s', c) = currentEnrollment(s, c) + 1"""
    state, student_id, course_id = args
    old_count = state.current_enrollment(course_id)
    new_state, result = state.enroll(student_id, course_id)
    
    if result.success:
        assert new_state.current_enrollment(course_id) == old_count + 1


# Invariant tests
@given(
    capacity=st.integers(min_value=1, max_value=10),
    num_students=st.integers(min_value=1, max_value=15)
)
@settings(max_examples=50)
def test_inv1_no_over_enrollment(capacity, num_students):
    """Spec INV1: currentEnrollment(s, c) ≤ capacity(s, c)"""
    state = State()
    state, course_id = state.create_course("Popular", capacity)
    
    students = []
    for i in range(num_students):
        state, student_id = state.register_student(f"Student{i}")
        students.append(student_id)
    
    successful = 0
    for student_id in students:
        state, result = state.enroll(student_id, course_id)
        if result.success:
            successful += 1
    
    assert state.current_enrollment(course_id) <= capacity
    assert successful <= capacity
    state.check_all_invariants()


@given(st.integers(min_value=2, max_value=5))
@settings(max_examples=20)
def test_inv4_no_prerequisite_cycles(num_courses):
    """Spec INV4: c ∉ transitivePrerequisites(s, c)"""
    state = State()
    
    course_ids = []
    for i in range(num_courses):
        state, cid = state.create_course(f"Course{i}", 10)
        course_ids.append(cid)
    
    for i in range(len(course_ids)):
        next_i = (i + 1) % len(course_ids)
        state, result = state.set_prerequisites(course_ids[i], {course_ids[next_i]})
        
        if i == len(course_ids) - 1:
            assert result.result_type == ResultType.CYCLE_DETECTED
        else:
            assert result.success
    
    state.check_all_invariants()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
