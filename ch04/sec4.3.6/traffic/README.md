
## Rubrics and Projects

These rubrics offer a framework to assess your implementation of the traffic light state machine,
ensuring you master both the technical and conceptual aspects. Use them to self-evaluate or guide
your project work.


#### 1. Code Functionality (30 points)
- *Excellent (25–30 points)*: Your code runs without errors, fully implementing the four states
  (`Green`, `Yellow`, `Yellow_Red`, `Red`) and correctly handling the pedestrian button input.
  Traffic light and walk signal LEDs behave as expected, with accurate timing and transitions.

- *Good (15–24 points)*: Your code runs with minor errors, implements most states correctly, and
  partially handles pedestrian input (e.g., walk signal activates but timing is slightly off).
  Transitions are mostly correct but may have small issues.

- *Needs Improvement (0–14 points)*: Your code has significant errors, misses states, or fails
  to handle pedestrian input. Transitions or LED controls are incorrect or incomplete.


#### 2. State Machine Design (25 points)
- *Excellent (20–25 points)*: Your state machine is clearly defined with distinct states, transitions,
  and actions. You use constants (e.g., `STATE_GREEN`, `green_time`) and modular functions (e.g.,
  `set_traffic_lights`). Pedestrian logic is seamlessly integrated.

- *Good (12–19 points)*: Your state machine has defined states and transitions, but some aspects
  (e.g., pedestrian logic or timing) are unclear or partially implemented. Modularity is present
  but could be improved (e.g., some hardcoded values).

- *Needs Improvement (0–11 points)*: Your state machine lacks clarity, has undefined or missing
  states, or deviates from FSM principles.


#### 3. Code Readability and Documentation (20 points)
- *Excellent (15–20 points)*: Your code is well-organised, uses meaningful variable names (e.g.,
  `red_light`, `walk_time`), and includes clear comments explaining states, transitions, and pedestrian
  logic. The structure is easy to follow.

- *Good (9–14 points)*: Your code is readable but has inconsistent naming or sparse comments. The
  logic is understandable but requires some effort to follow.

- *Needs Improvement (0–8 points)*: Your code is poorly organised, lacks comments, or uses unclear
  variable names, making it hard to understand.


#### 4. Handling of External Inputs (15 points)
- *Excellent (12–15 points)*: Your code correctly implements the pedestrian button using an interrupt,
  properly handling the `button_pressed` flag. The walk signal activates only when intended, with no glitches.

- *Good (7–11 points)*: Your code handles button input but has minor issues (e.g., no debouncing,
  flag not reset properly). The walk signal works but may have timing or logic errors.

- *Needs Improvement (0–6 points)*: Your code fails to handle button input correctly or lacks interrupt
  implementation, resulting in no or incorrect pedestrian functionality.


#### 5. Creativity and Extension (10 points)
- *Excellent (8–10 points)*: You extend the state machine with a creative feature (e.g., flashing
  walk signal, emergency override) that enhances functionality while adhering to FSM principles.

- *Good (5–7 points)*: You add a basic extension (e.g., adjustable timing) but it’s limited in scope
  or has minor integration issues.

- *Needs Improvement (0–4 points)*: Your code lacks extensions beyond the base implementation or
  extensions disrupt the FSM logic.


*Total: 100 points*


### Project Ideas

These projects help you deepen your understanding of state machines by extending the traffic light code
with pedestrian crossing. Each project builds on the original code, encourages hands-on learning, and
aligns with the rubrics. Choose projects based on your skill level, from beginner to advanced.


#### 1. Add a Flashing Walk Signal (Beginner)
*Objective*: Make the walk signal flash during the `STATE_RED` phase when the pedestrian button is pressed.

- *Tasks*:
  - Modify the `STATE_RED` logic to toggle the `walk_signal` LED (e.g., every 0.5 seconds)
    during the `walk_time` period.
  - Ensure the flashing stops when transitioning to `STATE_GREEN`.
- *Learning Outcomes*:
  - Practice modifying state behaviour.
  - Learn to implement sub-loops for visual effects.
- *Rubric Focus*: Code Functionality, State Machine Design.
- *Example Approach*:
  - In the `STATE_RED` block, replace `set_walk_signal(1); time.sleep(walk_time)` with a loop
    that toggles `walk_signal` every 0.5 seconds for a total of `walk_time`.


#### 2. Implement Button Debouncing (Intermediate)
*Objective*: Improve button reliability by adding software debouncing to the interrupt handler.

- *Tasks*:
  - Modify `pedestrian_button_pressed` to ignore rapid successive interrupts (e.g., within 200ms).
  - Test with multiple button presses to ensure only one `button_pressed` flag is set per cycle.
- *Learning Outcomes*:
  - Understand interrupt handling and noise filtering.
  - Practice robust input handling.
- *Rubric Focus*: Handling of External Inputs, Code Functionality.
- *Example Approach*:
  - Add a global variable to track the last button press time.
  - In `pedestrian_button_pressed`, check if the current time minus the last press time exceeds
    200ms before setting `button_pressed`.


#### 3. Adjustable Traffic Light Timing (Intermediate)
*Objective*: Allow dynamic adjustment of traffic light timings using an external input, like a potentiometer.

- *Tasks*:
  - Use a potentiometer (on an ADC pin) to adjust `green_time` and `red_time` (e.g., 3–10 seconds).
  - Ensure the state machine adapts to new timings without breaking FSM structure.
- *Learning Outcomes*:
  - Integrate analog inputs into a state machine.
  - Practice dynamic configuration.
- *Rubric Focus*: State Machine Design, Code Functionality, Creativity.
- *Example Approach*:
  - Use `machine.ADC` to read potentiometer values and scale them to a range (e.g., 3–10 seconds).
  - Update `green_time` and `red_time` in the main loop before state transitions.


#### 4. Emergency Vehicle Override (Advanced)
*Objective*: Add an emergency state to prioritise green lights for emergency vehicles,
triggered by a second button.

- *Tasks*:
  - Introduce a `STATE_EMERGENCY` that sets the green light on for 10 seconds, overriding the normal cycle.
  - Use a second button (e.g., on pin 16) with an interrupt to trigger this state.
  - Return to `STATE_GREEN` after the emergency state.
- *Learning Outcomes*:
  - Learn to add and manage new states in an FSM.
  - Handle multiple external inputs.
- *Rubric Focus*: State Machine Design, Handling of External Inputs, Creativity.
- *Example Approach*:
  - Define `STATE_EMERGENCY` and configure a second button interrupt.
  - Transition to `STATE_EMERGENCY` when the button is pressed, setting all lights off except green.


#### 5. Multi-Directional Traffic Light System (Advanced)
*Objective*: Control two sets of traffic lights for a four-way intersection.

- *Tasks*:
  - Add three LEDs for a second direction (e.g., North-South vs. East-West).
  - Alternate green lights between directions (e.g., North-South green while East-West is red).
  - Synchronise pedestrian signals for both directions.
- *Learning Outcomes*:
  - Scale state machines for complex systems.
  - Coordinate multiple outputs in a single FSM.
- *Rubric Focus*: Code Functionality, State Machine Design, Creativity.
- *Example Approach*:
  - Define states like `STATE_GREEN_NS` and `STATE_GREEN_EW` for each direction.
  - Activate pedestrian signals during the corresponding red state for each direction.


### How to Use These Rubrics and Projects
- *Start Small*: If you’re new to state machines, begin with the Flashing Walk Signal
  project to get comfortable with the code.
- *Challenge Yourself*: Try the Emergency Vehicle Override or Multi-Directional Traffic
  Light System if you’re familiar with MicroPython and interrupts.
- *Test Thoroughly*: Use a breadboard with LEDs and a button to test on hardware.
  Simulate inputs if hardware isn’t available.
- *Document Your Work*: Add comments explaining each state and transition, and use
  the rubrics to check your progress.
- *Visualise Your FSM*: Refer to the Mermaid state diagram (provided in [03](./03/))
  to map your state machine before coding, especially for complex projects.

These rubrics and projects are designed to help you understand state machines while building practical
skills in embedded programming. They align with the traffic light code’s structure, letting you extend
it while exploring concepts like interrupts, dynamic inputs, and scalability.
