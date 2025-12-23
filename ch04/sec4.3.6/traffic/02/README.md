
## Enhanced Traffic Light State Machine with Pedestrian Crossing

This updated code extends the previous traffic light state machine by incorporating
a pedestrian crossing feature, adding interactivity and real-world applicability.
It introduces a pedestrian signal (via an onboard LED) and a button input to trigger
a walk signal, demonstrating how state machines can handle external events while
maintaining deterministic behaviour.


### Enhancements

- Pedestrian Signal: A new LED (walk_signal on pin 25) indicates when pedestrians can
  cross ("Walk" when on, "Don't Walk" when off).
- Button Input: A push button (button on pin 15) allows pedestrians to request a crossing,
  detected via an interrupt (pedestrian_button_pressed).
- Interrupt Handling: The button uses an interrupt request (IRQ) with a rising edge trigger
  to set a button_pressed flag, enabling asynchronous event detection.
- State Behaviour: The pedestrian crossing is integrated into the STATE_RED state, where
  the walk signal is activated only if the button was pressed, extending the red light
  duration to walk_time (5 seconds).

### State Machine Analysis
The state machine retains the four states (STATE_GREEN, STATE_YELLOW, STATE_YELLOW_RED, STATE_RED)
but enhances the STATE_RED logic:

- If button_pressed is True, the walk signal turns on for walk_time, allowing pedestrians to cross.
- If no button press is detected, the red light stays on for red_time without activating the walk signal.
- The button_pressed flag is reset implicitly by transitioning back to STATE_GREEN, preparing for the next cycle.


### State Flow

- Green: Green light on, walk signal off (green_time = 5s).
- Yellow: Yellow light on, walk signal off (yellow_time = 2s).
- Yellow_Red: Yellow and red lights on, walk signal off (yellow_red_time = 1s).
- Red: Red light on; walk signal on if button pressed (walk_time = 5s),
  else red light only (red_time = 5s).

### Practical Considerations

* Interrupts: Using an interrupt for the button ensures the system responds to pedestrian
  input without constant polling, improving efficiency.
* Timing: The walk signal duration (walk_time) matches the red light duration, ensuring
  safe crossing time.
* Scalability: The state machine could be extended with additional states (e.g., flashing
  walk signal) or inputs (e.g., emergency vehicle override).

### Benefits and Applications

This enhanced state machine demonstrates how to integrate external inputs (button press)
and additional outputs (walk signal) into a finite state machine. It’s a practical example
for embedded systems, showcasing real-time event handling in applications like traffic
control, industrial automation, or IoT devices.

