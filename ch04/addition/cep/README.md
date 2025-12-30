
## Complex Event Processing (CEP)

Complex Event Processing (CEP) is a field of computer science focused
on identifying meaningful patterns in real-time event streams. It's
typically used in scenarios where multiple data points (events) are
processed and analyzed to detect complex patterns that are beyond
simple event matching.

In simpler terms, CEP allows systems to continuously monitor and analyze
events as they occur, and when specific patterns of events are detected,
the system can trigger actions or generate outputs. It's commonly used
in financial systems, traffic management, monitoring systems, and IoT
applications.


Concepts in CEP:
- Event: A single piece of data or information, such as a sensor reading,
  a stock price change, or a button press.
- Stream: A continuous flow of events over time.
- Pattern Matching: The process of identifying specific sequences or
  combinations of events.
- Event Correlation: Detecting relationships between events (e.g., event
  A happens, then event B within a certain time window).
- Time Windows: Defining the scope of time in which events are considered,
  to detect temporal patterns.
- Actions: When a pattern or condition is met, some action is triggered,
  such as sending an alert or adjusting a device.


#### Illustrating CEP with Raspberry Pi Pico

To illustrate how we could write a program for Raspberry Pi Pico to perform
basic Complex Event Processing, let's break it down into manageable steps.
We'll implement a basic event stream processing system that detects simple
patterns in sensor data (e.g., temperature readings from a sensor).


__Example Scenario__

Consider a temperature sensor connected to the Raspberry Pi Pico. Our goal
is to process the event stream of temperature readings and trigger a warning
if the temperature has risen above a certain threshold within a specified
time window (e.g., if the temperature exceeds 30°C for 5 consecutive readings).


1. Setup the Raspberry Pi Pico with a Temperature Sensor (e.g., DHT11/DHT22)

We'll need a sensor connected to the Raspberry Pi Pico to simulate an event
stream. The DHT11 or DHT22 is commonly used for this.

Required Components:
- Raspberry Pi Pico
- DHT11 or DHT22 sensor
- Wires for connections

Wiring:
- DHT11 or DHT22 sensor VCC -> 3.3V (Pin 36 or 38 on Pico)
- DHT11 or DHT22 sensor GND -> GND (Pin 38 on Pico)
- DHT11 or DHT22 sensor Data Pin -> GPIO Pin (e.g., GPIO 15)


__Libraries__

You'll need the dht library to interface with the DHT sensor on the Raspberry Pi Pico.

2. Basic Python Code to Read from the Temperature Sensor

Let's start by reading data from the temperature sensor. We'll use the MicroPython environment for the Raspberry Pi Pico.

```python
import time
import dht
from machine import Pin

# Init the sensor (connected to GPIO 15)
sensor = dht.DHT22(Pin(15))

def read_temperature():
    try:
        sensor.measure()
        temp = sensor.temperature()
        humidity = sensor.humidity()
        return temp, humidity
    except OSError as e:
        print("Failed to read sensor.")
        return None, None
```

This code sets up the DHT22 sensor and defines a function to read the temperature and humidity.

3. Implementing Complex Event Processing (CEP)

Now, let's implement a basic CEP system that detects a rising temperature trend. We'll process the event stream of temperature readings and trigger an action when the temperature exceeds 30°C for five consecutive readings (in this example, a basic time window).

Here's a breakdown of how this could work:
- Event Stream: Continuous temperature readings.
- Pattern: Detect when temperature readings exceed 30°C for 5 consecutive readings.
- Action: Trigger a warning (e.g., print an alert or turn on a fan).

Key Elements:

- Event Stream: In our case, temperature readings are events.
- Sliding Window: We need to keep track of the last 5 readings to detect a pattern.
- Condition: If all 5 readings exceed 30°C, trigger an action.

Code Example:

```python
# List to store the last N temperature readings (window size = 5)
temperature_window = []
window_size = 5
threshold_temp = 30  # Threshold for triggering action

def process_temperature_event(temp):
    # Append the new temperature reading
    temperature_window.append(temp)

    # If we have more than the window size, remove the oldest reading
    if len(temperature_window) > window_size:
        temperature_window.pop(0)

    # Check if all readings in the window exceed the threshold
    if len(temperature_window) == window_size and all(t > threshold_temp for t in temperature_window):
        print("Warning: Temperature exceeded threshold for 5 consecutive readings!")
        # Trigger action (e.g., turning on a fan, or sending an alert)
        trigger_action()

def trigger_action():
    # Placeholder for the action triggered when the condition is met
    print("Action triggered: Taking action based on high temperature")

def main():
    while True:
        # Read the temperature from the sensor
        temp, _ = read_temperature()
        if temp is not None:
            print(f"Temperature: {temp}°C")
            process_temperature_event(temp)

        # Sleep for a second before reading again
        time.sleep(1)
```

How This Works:

1. Event Stream: The main() function continuously reads the temperature sensor every second.
2. Pattern Detection: The process_temperature_event() function checks the last 5 temperature
   readings stored in the temperature_window. If all readings exceed 30°C, it triggers an action.
3. Action: The trigger_action() function is called when the pattern is detected. You could
   extend this to control a relay, activate a cooling fan, or send a message.
4. Scaling and Advanced CEP Concepts

For a real-world CEP system, more advanced techniques can be used to handle multiple event streams,
correlate events from different sources, and apply more complex patterns. These may include:
- Temporal Patterns: Detecting patterns that span across specific time windows.
- Event Prioritization: Processing events based on priority or urgency.
- Complex Patterns: Using logical conditions, such as "Event A occurs within 5 minutes of Event B."

To scale this to handle more complex patterns, you could use a proper event processing framework
or even implement your own lightweight query system using state machines or rule-based engines.

5. Optimising for Raspberry Pi Pico

The Raspberry Pi Pico is limited in terms of computational resources, so keeping your event
processing lightweight is important:
- Efficient Data Storage: Avoid storing too much data in memory at once. In this case,
  using a small window of 5 events is sufficient.
- Low Power Operation: Consider the power consumption of sensors and keep the system
  in a low-power state when not processing events.
- Asynchronous Processing: Use non-blocking or interrupt-driven approaches to avoid
  wasting processing time on waiting for sensor data.


### Conclusion

Complex Event Processing (CEP) on a Raspberry Pi Pico can be implemented with a simple
event-driven approach to detect patterns in sensor data and trigger actions. By leveraging
lightweight data storage (a sliding window) and basic pattern matching, you can create a
program that reacts to real-time events. As the complexity of the patterns increases, you
can scale the system by incorporating more sophisticated event correlation techniques, but
even simple CEP can provide valuable functionality in IoT and real-time monitoring scenarios.


### Reference

As a journalist I was once invited to a company in the Netherlands to learn about their
RFID implementation in both hardware and software. However, the technician I spoke with
was more interested in Complex Event Processing and what it could offer.
He even gave me a book about it:

It introduces core concepts such as events, causal relationships, event patterns, hierarchies,
time windows, and event correlation in a way that closely matches the opening sections of your document.
If you continue developing your work on these concepts, I highly recommend reading this book.

