
## Course Enrollment System

Algebraic specification-based implementation with Python and JavaScript versions.

### Overview

This project demonstrates how to use algebraic specifications to
design and implement software systems. It includes:
- *Formal algebraic specification* (`spec/specification-v1.1.txt`)
- *Python implementation* with property-based tests
- *JavaScript web application* with UI

All implementations follow the same algebraic specification, ensuring consistency.

### Directory Structure

```
example/
├── spec/
│   └── specification-v1.1.txt     # Algebraic specification
├── python/
│   ├── state.py                   # State implementation
│   ├── tests.py                   # Property-based tests  
│   └── requirements.txt           # Python dependencies
└── javascript/
    ├── src/
    │   ├── state.js               # Core state logic
    │   └── app.js                 # UI application
    ├── index.html                 # Web interface
    └── styles.css                 # Styling
```

### Running the Python Tests

```bash
cd python
pip install -r requirements.txt
pytest tests.py -v
```

### Running the JavaScript Web App

Simply open `javascript/index.html` in a web browser,
or use a local server:

```bash
cd javascript
python -m http.server 8000
## Visit http://localhost:8000
```

### Key Concepts

#### Algebraic Specification

The specification defines:
- *Sorts*: Types (Student, Course, State, etc.)
- *Operations*: Functions with signatures
- *Equations*: Laws operations must obey
- *Invariants*: Properties that always hold
- *Pre/Post Conditions*: What must be true before/after operations


#### Implementation

Both Python and JavaScript implementations:
- Use immutable state (operations return new State instances)
- Validate all pre-conditions
- Maintain all invariants
- Follow the same algebraic laws


#### Property-Based Testing

Tests verify that:
- All equations hold for random inputs
- All invariants are maintained after every operation
- Pre-conditions are necessary
- Post-conditions are sufficient


### Example Usage

#### Python

```python
from state import State

## Create state
state = State()

## Register student
state, student_id = state.register_student("Alice")

## Create course
state, course_id = state.create_course("Data Structures", 30)

## Enroll student
state, result = state.enroll(student_id, course_id)

if result.success:
    print("Enrollment successful!")
```


#### JavaScript

See `javascript/index.html` for the interactive web interface.


### Specification Highlights

*Invariants Maintained:*
- INV1: No over-enrollment
- INV2: Enrollment status consistency  
- INV3: Completion implies prerequisites met
- INV4: No cycles in prerequisites
- INV5: Enrolled students meet prerequisites

*Key Equations:*
- EQ1: Capacity is immutable once set
- EQ2: Empty state has zero enrollments
- EQ3: Successful enrollment increases count by 1
- EQ4: Successful drop decreases count by 1
- EQ5: Completion adds to completed courses

