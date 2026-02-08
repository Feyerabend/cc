/**
 * Course Enrollment System - UI Application Logic
 */

class EnrollmentApp {
  constructor() {
    this.state = new State();
    this.currentStudent = null;
    this.initializeEventListeners();
    this.render();
  }

  initializeEventListeners() {
    document.getElementById('registerStudent').addEventListener('click', () => this.registerStudent());
    document.getElementById('selectStudent').addEventListener('change', (e) => this.selectStudent(e.target.value));
    document.getElementById('createCourse').addEventListener('click', () => this.createCourse());
    document.getElementById('enrollInCourse').addEventListener('click', () => this.enrollInCourse());
    document.getElementById('dropCourse').addEventListener('click', () => this.dropCourse());
    document.getElementById('completeCourse').addEventListener('click', () => this.completeCourse());
  }

  registerStudent() {
    const name = document.getElementById('studentName').value.trim();
    if (!name) {
      this.showMessage('Please enter a student name', 'error');
      return;
    }
    const [newState, studentId] = this.state.registerStudent(name);
    this.state = newState;
    document.getElementById('studentName').value = '';
    this.showMessage(`Student ${name} registered successfully!`, 'success');
    this.render();
  }

  selectStudent(studentId) {
    this.currentStudent = studentId || null;
    this.render();
  }

  createCourse() {
    const name = document.getElementById('courseName').value.trim();
    const capacity = parseInt(document.getElementById('courseCapacity').value);
    if (!name || isNaN(capacity) || capacity < 1) {
      this.showMessage('Please enter valid course name and capacity', 'error');
      return;
    }
    const [newState, courseId] = this.state.createCourse(name, capacity);
    this.state = newState;
    document.getElementById('courseName').value = '';
    document.getElementById('courseCapacity').value = '';
    this.showMessage(`Course ${name} created successfully!`, 'success');
    this.render();
  }

  enrollInCourse() {
    if (!this.currentStudent) {
      this.showMessage('Please select a student first', 'error');
      return;
    }
    const courseId = document.getElementById('courseSelect').value;
    if (!courseId) {
      this.showMessage('Please select a course', 'error');
      return;
    }
    const [newState, result] = this.state.enroll(this.currentStudent, courseId);
    if (result.success) {
      this.state = newState;
      this.showMessage('Enrollment successful!', 'success');
    } else {
      this.showMessage(`Enrollment failed: ${result.message}`, 'error');
    }
    this.render();
  }

  dropCourse() {
    if (!this.currentStudent) {
      this.showMessage('Please select a student first', 'error');
      return;
    }
    const courseId = document.getElementById('enrolledCourseSelect').value;
    if (!courseId) {
      this.showMessage('Please select an enrolled course', 'error');
      return;
    }
    const [newState, result] = this.state.drop(this.currentStudent, courseId);
    if (result.success) {
      this.state = newState;
      this.showMessage('Course dropped successfully!', 'success');
    } else {
      this.showMessage(`Drop failed: ${result.message}`, 'error');
    }
    this.render();
  }

  completeCourse() {
    if (!this.currentStudent) {
      this.showMessage('Please select a student first', 'error');
      return;
    }
    const courseId = document.getElementById('enrolledCourseSelect').value;
    if (!courseId) {
      this.showMessage('Please select an enrolled course', 'error');
      return;
    }
    const [newState, result] = this.state.completeCourse(this.currentStudent, courseId);
    if (result.success) {
      this.state = newState;
      this.showMessage('Course completed successfully!', 'success');
    } else {
      this.showMessage(`Completion failed: ${result.message}`, 'error');
    }
    this.render();
  }

  showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    setTimeout(() => messageDiv.style.display = 'none', 3000);
  }

  render() {
    this.renderStudentSelect();
    this.renderCourseList();
    this.renderCourseSelect();
    this.renderStudentInfo();
    this.renderEnrolledCourses();
  }

  renderStudentSelect() {
    const select = document.getElementById('selectStudent');
    select.innerHTML = '<option value="">-- Select Student --</option>';
    for (const [id, name] of this.state.students) {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = name;
      if (id === this.currentStudent) option.selected = true;
      select.appendChild(option);
    }
  }

  renderCourseList() {
    const tbody = document.getElementById('courseList');
    tbody.innerHTML = '';
    for (const [id, course] of this.state.courses) {
      const row = tbody.insertRow();
      row.innerHTML = `<td>${course.name}</td><td>${this.state.currentEnrollment(id)}/${course.capacity}</td><td>None</td>`;
    }
  }

  renderCourseSelect() {
    const select = document.getElementById('courseSelect');
    select.innerHTML = '<option value="">-- Select Course --</option>';
    for (const [id, course] of this.state.courses) {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = `${course.name} (${this.state.currentEnrollment(id)}/${course.capacity})`;
      select.appendChild(option);
    }
  }

  renderStudentInfo() {
    const infoDiv = document.getElementById('studentInfo');
    if (!this.currentStudent) {
      infoDiv.innerHTML = '<p>No student selected</p>';
      return;
    }
    const name = this.state.getStudentName(this.currentStudent);
    const enrolled = this.state.studentCourses(this.currentStudent);
    infoDiv.innerHTML = `<h3>${name}</h3><p><strong>Enrolled Courses:</strong> ${enrolled.size}</p>`;
  }

  renderEnrolledCourses() {
    const select = document.getElementById('enrolledCourseSelect');
    select.innerHTML = '<option value="">-- Select Enrolled Course --</option>';
    if (!this.currentStudent) return;
    const enrolled = this.state.studentCourses(this.currentStudent);
    for (const courseId of enrolled) {
      const courseName = this.state.getCourseName(courseId);
      const option = document.createElement('option');
      option.value = courseId;
      option.textContent = courseName;
      select.appendChild(option);
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new EnrollmentApp();
});
