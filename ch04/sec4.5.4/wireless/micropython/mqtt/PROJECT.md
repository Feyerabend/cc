
## Raspberry Pi Pico W MQTT Client

A simple yet powerful MQTT client implementation for the Raspberry Pi Pico W that
enables remote control and monitoring of your device over the internet.

- *MQTT Connection*: Connect to any MQTT broker (defaults to test.mosquitto.org)
- *LED Control*: Remotely control the onboard LED via MQTT commands
- *Telemetry*: Automatic publishing of device status and metrics every 30 seconds
- *Command Processing*: Support for both JSON and plain text command formats
- *Real-time Updates*: Status messages published for all actions
- *Error Handling*: Robust error handling throughout


### Hardware Requirements

- Raspberry Pi Pico W
- USB cable for power and programming
- WiFi network


### Software Requirements

- MicroPython firmware for Pico W
- `umqtt.simple` library (included in most MicroPython distributions)


### Installation

1. *Flash MicroPython to your Pico W* if you haven't already:
   - Download the latest MicroPython firmware from
     [micropython.org](https://micropython.org/download/rp2-pico-w/)
   - Hold the BOOTSEL button while connecting your Pico W to your computer
   - Copy the `.uf2` file to the mounted drive

2. *Upload the script*:
   - Use Thonny IDE, ampy, or rshell to upload `mqtt.py` to your Pico W
   - Save it as `main.py` to run automatically on boot, or run it manually

3. *Configure WiFi* (add to the beginning of the script):
   ```python
   import network
   wlan = network.WLAN(network.STA_IF)
   wlan.active(True)
   wlan.connect('YOUR_SSID', 'YOUR_PASSWORD')
   
   while not wlan.isconnected():
       pass
   print('Connected to WiFi:', wlan.ifconfig())
   ```

### Usage

#### Basic Setup

```python
import gc
from mqtt import PicoMQTTClient

## Create MQTT client with default settings
mqtt_client = PicoMQTTClient()

## Or customize the configuration
mqtt_client = PicoMQTTClient(
    client_id="my_pico_device",
    broker="test.mosquitto.org",
    port=1883
)

## Start the client
mqtt_client.run()
```

#### MQTT Topics

The client uses three main topics:

- *Command Topic*: `devices/{client_id}/commands` - Send commands to the device
- *Status Topic*: `devices/{client_id}/status` - Receive status updates
- *Telemetry Topic*: `devices/{client_id}/telemetry` - Receive periodic telemetry data

#### Sending Commands

You can send commands in two formats:

*JSON Format:*
```json
{"command": "led_on"}
{"command": "led_off"}
{"command": "status"}
```

*Plain Text Format:*
```
led_on
led_off
status
```

#### Example: Testing with Mosquitto

If you have `mosquitto_pub` and `mosquitto_sub` installed:

*Subscribe to status messages:*
```bash
mosquitto_sub -h test.mosquitto.org -t "devices/pico_w_001/status"
```

*Send a command to turn on the LED:*
```bash
mosquitto_pub -h test.mosquitto.org -t "devices/pico_w_001/commands" -m "led_on"
```

*Request telemetry:*
```bash
mosquitto_pub -h test.mosquitto.org -t "devices/pico_w_001/commands" -m '{"command": "status"}'
```

### Telemetry Data

The device automatically publishes telemetry every 30 seconds, including:

- Device uptime
- LED status
- Free memory
- Temperature (placeholder)
- Signal strength (placeholder)

Example telemetry payload:
```json
{
  "timestamp": 1704672000,
  "device": "pico_w_001",
  "uptime": 150000,
  "led_status": true,
  "free_memory": 120000,
  "temperature": 25.0,
  "signal_strength": -45
}
```

### Customisation

#### Change Telemetry Interval

Modify the `telemetry_interval` variable in the `run()` method:

```python
telemetry_interval = 60.0  ## Publish every 60 seconds
```

#### Add Custom Commands

Extend the `process_command()` method to add your own commands:

```python
elif command_type == 'my_custom_command':
    ## Your custom logic here
    self.publish_status("Custom command executed")
```

#### Use a Different MQTT Broker

```python
mqtt_client = PicoMQTTClient(
    broker="broker.hivemq.com",  ## or your own broker
    port=1883
)
```

### Troubleshooting

*Connection Issues:*
- Verify your WiFi credentials are correct
- Check that your broker address is accessible
- Ensure port 1883 is not blocked by your firewall

*Memory Issues:*
- The script includes garbage collection to manage memory
- Reduce telemetry_interval if you're running out of memory
- Consider removing unused telemetry fields

*LED Not Responding:*
- Verify the LED is connected to GPIO 25 (onboard LED on Pico W)
- Check the command format matches expected patterns
- Monitor the status topic for error messages
