
## Projects

### 1: Motion Detection for Security Monitoring

Use a PIR (Passive Infrared) motion sensor connected to a GPIO pin on
the Raspberry Pi Pico 2. The CEP pattern could detect multiple motion
events within a short time window (e.g., 3 motions in 30 seconds),
which might indicate suspicious activity rather than a single false
trigger. This is simple to implement as it builds on the temperature
example by swapping the sensor and adjusting the window logic.

- *Why simple?* PIR sensors are cheap and easy to wire (VCC to 3.3V,
  GND to GND, OUT to a GPIO like 16). No complex libraries needed
  beyond `machine.Pin` for input.

- *Display integration:* Use the Pimoroni Display Pack 2.0 to show
  real-time status (e.g., "No Motion" in green) and flash an alert
  like "Motion Detected!" in red when the pattern is met, using the
  RGB LED for extra visual cue. The screen's 320x240 resolution is
  perfect for displaying a counter or timestamped log of events.


```python
import time
from machine import Pin

# PIR sensor on GPIO 16
pir = Pin(16, Pin.IN)

# Window for 3 motions in 30 seconds (track timestamps)
motion_window = []
window_duration = 30  # seconds
motion_threshold = 3

def process_motion_event():
    current_time = time.time()
    motion_window.append(current_time)
    # Remove old events outside window
    motion_window[:] = [t for t in motion_window if current_time - t < window_duration]
    if len(motion_window) >= motion_threshold:
        print("Alert: Multiple motions detected!")
        # Display alert on screen (add display code here)
        trigger_display_alert()

def main():
    while True:
        if pir.value() == 1:  # Motion detected
            process_motion_event()
        time.sleep(0.1)  # Quick poll
```


### 2: Button Sequence Lock

Leverage the 4 tactile buttons on the Pimoroni Display Pack 2.0 itself as event sources.
The CEP could detect a specific sequence of button presses within a time window (e.g.,
buttons A-B-X-Y in under 10 seconds), acting like a simple combination lock. This is
event correlation across multiple inputs.

- *Why simple?* No extra hardware needed—the display pack provides the buttons. Use
  interrupts or polling on the button pins (typically GPIO 12-15 or similar, check
  Pimoroni docs). The pattern matching is just checking a list of events against a
  predefined sequence.
- *Display integration:* Show a prompt like "Enter Code" on the screen, update with
  asterisks for each press, and display "Access Granted" or "Wrong Code" with the RGB
  LED flashing green/red accordingly. The buttons make it interactive without external
  sensors.


```python
import time
from machine import Pin
# Assume buttons on GPIO (adjust per Pimoroni mapping, e.g., A=Pin(12), B=Pin(13), etc.)
buttons = {'A': Pin(12, Pin.IN), 'B': Pin(13, Pin.IN), 'X': Pin(14, Pin.IN), 'Y': Pin(15, Pin.IN)}

sequence_window = []
correct_sequence = ['A', 'B', 'X', 'Y']
window_duration = 10  # seconds

def process_button_event(button_id):
    current_time = time.time()
    sequence_window.append((button_id, current_time))
    # Expire old presses
    sequence_window[:] = [(b, t) for b, t in sequence_window if current_time - t < window_duration]
    # Check if last len(correct) presses match
    if len(sequence_window) >= len(correct_sequence) and [b for b, _ in sequence_window[-len(correct_sequence):]] == correct_sequence:
        print("Access Granted!")
        # Update display to show success
        display_success()

def main():
    last_states = {k: 0 for k in buttons}
    while True:
        for btn_id, pin in buttons.items():
            if pin.value() == 1 and last_states[btn_id] == 0:  # Button pressed
                process_button_event(btn_id)
            last_states[btn_id] = pin.value()
        time.sleep(0.05)
```


### 3: Light Level Anomaly Detection

Connect a simple LDR (Light Dependent Resistor) to an ADC pin (e.g., GPIO 26)
for analog readings. The CEP pattern could detect prolonged low light levels
(e.g., below a threshold for 10 consecutive readings over 2 minutes), indicating
something like a room light failure or sunset.

- *Why simple?* LDR wiring is basic (one leg to 3.3V via resistor, other to GND
  and ADC). Use machine.ADC for reads—similar to sensor polling in the document.
  The window logic is almost identical to the temperature example.

- *Display integration:* Render current light level as a bar graph or text on the
  2.0" screen (e.g., "Light: Normal" or "Low Light Alert!"), making it visually
  intuitive. Use the RGB LED to change color based on intensity.


```python
import time
from machine import ADC, Pin

# LDR on ADC0 (GPIO 26)
adc = ADC(26)
threshold_light = 20000  # Adjust based on calibration (higher ADC = brighter)
light_window = []
window_size = 10

def read_light():
    return adc.read_u16()  # 0-65535

def process_light_event(light):
    light_window.append(light)
    if len(light_window) > window_size:
        light_window.pop(0)
    if len(light_window) == window_size and all(l < threshold_light for l in light_window):
        print("Alert: Prolonged low light!")
        # Display warning on screen
        display_low_light()

def main():
    while True:
        light = read_light()
        print(f"Light level: {light}")
        process_light_event(light)
        time.sleep(12)  # ~2 min for 10 reads
```
