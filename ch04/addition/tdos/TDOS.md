
## TDOS - Tiny Distributed Operating System

### Implementation Guide

TDOS is a lightweight, fault-tolerant distributed system for Raspberry Pi Pico W boards that provides:

- *Automatic Service Discovery*: Zero-configuration networking
- *Fault Tolerance*: Heartbeat monitoring, circuit breakers, retry logic
- *Resource Virtualization*: Unified API for distributed sensors and displays
- *Protocol Robustness*: Message versioning, error handling, timeouts
- *Extensibility*: Easy to add new sensor types and services



### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Kernel Node    │         │  Sensor Node A  │
│  (Coordinator)  │◄───────►│  (Temperature)  │
│  - Discovery    │         │  - Service      │
│  - Registry     │         │  - Heartbeat    │
│  - Display      │         │  - RPC Handler  │
└─────────────────┘         └─────────────────┘
         │                           │
         │                           │
         │         ┌─────────────────┘
         │         │
         ▼         ▼
┌─────────────────────────────┐
│    WiFi Network (UDP)       │
│    - Port 4000: Discovery   │
│    - Port 5000: Services    │
└─────────────────────────────┘
```



### Network Protocol

#### Message Format

All messages are JSON-encoded UDP packets:

```json
{
  "v": 1,              // Protocol version
  "t": 1,              // Message type (1-8)
  "id": "a3f2c1d9",    // Unique message ID
  "ts": 1704000000,    // Unix timestamp
  "p": {...},          // Payload (varies by type)
  "r": "..."           // Reply-to ID (optional)
}
```

#### Message Types

| Type | Value | Purpose |
|------|-------|---------|
| SERVICE_ANNOUNCE | 1 | Initial service registration |
| SERVICE_QUERY | 2 | Query for specific service |
| RPC_REQUEST | 3 | Remote procedure call |
| RPC_RESPONSE | 4 | RPC result |
| HEARTBEAT | 5 | Service alive notification |
| ERROR | 6 | Error response |
| ACK | 7 | Acknowledgment |
| SERVICE_GOODBYE | 8 | Service shutdown notification |

#### Communication Flow

__1. Service Discovery__

```
Sensor Node                    Kernel Node
     │                              │
     │──── SERVICE_ANNOUNCE ───────>│
     │                              │ (Registers service)
     │                              │
     │◄─────────────────────────────│
     │                              │
     │──── HEARTBEAT (every 5s) ───>│
     │                              │ (Updates last_seen)
```

__2. RPC Call__

```
Kernel Node                    Sensor Node
     │                              │
     │──── RPC_REQUEST ────────────>│
     │    {"op": "read"}            │ (Reads sensor)
     │                              │
     │◄──── RPC_RESPONSE ───────────│
     │    {"value": 22.5, ...}      │
```



### File Structure

```
tdos/
├── protocol.py           ## Core protocol library
├── sensor_node.py        ## Sensor node implementation
├── tinyos.py            ## Kernel node implementation
├── weather_station.py   ## Example: Multi-sensor app
├── data_logger.py       ## Example: Data logging
├── monitor.py           ## Example: System monitoring
└── alert_system.py      ## Example: Alert system
```



### Installation & Setup

#### Prerequisites

- Raspberry Pi Pico W (2+ boards)
- MicroPython v1.20+ installed
- WiFi network or create ad-hoc network
- Optional: Display module (SSD1306 or Pimoroni)

#### WiFi Setup

*Option 1: Use existing WiFi*
```python
## Edit these in each file:
WIFI_SSID = "YourNetworkName"
WIFI_PASSWORD = "YourPassword"
```

*Option 2: Create access point on one Pico*
```python
import network

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="TDOS_Network", password="tdos12345")
print("AP IP:", ap.ifconfig()[0])
```

#### Upload Files

Using Thonny, rshell, or mpremote:

```bash
## Upload to Sensor Node
mpremote connect /dev/ttyACM0 cp protocol.py :
mpremote connect /dev/ttyACM0 cp sensor_node.py :main.py

## Upload to Kernel Node
mpremote connect /dev/ttyACM1 cp protocol.py :
mpremote connect /dev/ttyACM1 cp tinyos.py :
mpremote connect /dev/ttyACM1 cp weather_station.py :main.py
```



### Quick Start

#### 1. Start Sensor Nodes

*Temperature Sensor:*
```python
## main.py on Sensor Node 1
from sensor_node import create_temp_sensor

sensor = create_temp_sensor()
sensor.run(ssid="TDOS_Network", password="tdos12345")
```

*Humidity Sensor:*
```python
## main.py on Sensor Node 2
from sensor_node import create_humidity_sensor

sensor = create_humidity_sensor()
sensor.run(ssid="TDOS_Network", password="tdos12345")
```

*ADC Light Sensor:*
```python
## main.py on Sensor Node 3
from sensor_node import create_light_sensor

sensor = create_light_sensor(pin=26)  ## GPIO26 = ADC0
sensor.run(ssid="TDOS_Network", password="tdos12345")
```

#### 2. Start Kernel Node

*Simple Example:*
```python
## main.py on Kernel Node
import tinyos
import time

tinyos.init()

display = tinyos.open_display()
temp = tinyos.open_temp_sensor()

while True:
    reading = tinyos.read(temp)
    if reading:
        msg = f"Temp: {reading['value']:.1f}{reading['unit']}"
        tinyos.write(display, msg)
    time.sleep(5)
```

*Weather Station:*
```python
## main.py on Kernel Node
from weather_station import main
main()
```



### API Reference

#### Kernel API (`tinyos.py`)

__Initialization__

```python
tinyos.init(ssid="TDOS_Network", password="tdos12345")
```

Initialises TDOS kernel, connects to WiFi, starts service discovery.

__Resource Opening__

```python
## Display
display = tinyos.open_display()  ## Returns "display" or "console"

## Sensors
temp = tinyos.open_temp_sensor()       ## RuntimeError if not found
humidity = tinyos.open_humidity_sensor()
light = tinyos.open_light_sensor()
custom = tinyos.open_sensor("my_sensor")
```

__Reading/Writing__

```python
## Write to display
tinyos.write(display, "Hello World")

## Read from sensor
reading = tinyos.read(temp_sensor)
## Returns: {"value": 22.5, "unit": "°C"} or None on error
```

__Service Management__

```python
## List available services
services = tinyos.list_services()
## Returns: ["temp_sensor", "humidity_sensor", ...]

## Get service details
info = tinyos.get_service_info("temp_sensor")
## Returns: {
##   "name": "temp_sensor",
##   "ip": "192.168.1.100",
##   "port": 5000,
##   "metadata": {...},
##   "last_seen": 1704000000,
##   "failures": 0,
##   "state": "active"
## }

## Get statistics
stats = tinyos.get_stats()
## Returns: {
##   "uptime": 120,
##   "services_discovered": 3,
##   "rpc_calls": 45,
##   "rpc_failures": 2,
##   "active_services": 3,
##   ...
## }

## Shutdown
tinyos.shutdown()
```

#### Sensor Node API (`sensor_node.py`)

__Creating Custom Sensors__

```python
from sensor_node import SensorNode

## Simulated sensor
sensor = SensorNode("my_sensor", {"type": "simulated"})

## ADC sensor
sensor = SensorNode("light_sensor", {
    "type": "adc",
    "pin": 26  ## GPIO pin
})

## DHT22 temperature/humidity
sensor = SensorNode("climate", {
    "type": "dht22",
    "pin": 15
})

## Digital input
sensor = SensorNode("button", {
    "type": "digital",
    "pin": 16
})

## Run the sensor
sensor.run(ssid="TDOS_Network", password="tdos12345")
```

__Sensor Reading Format__

Sensors return dictionaries with reading data:

```python
## Simple value sensor
{"value": 22.5, "unit": "°C"}

## Multi-value sensor (DHT22)
{"temperature": 22.5, "humidity": 65.0, "unit": "°C/%"}

## ADC with raw value
{"value": 45.2, "unit": "%", "raw": 29650}

## Error
{"error": "Sensor timeout"}
```



### Advanced Features

#### Fault Tolerance

TDOS implements multiple fault tolerance mechanisms:

*1. Heartbeat Monitoring*
- Services send heartbeats every 5 seconds
- Services timeout after 15 seconds of no heartbeat
- Automatic removal of dead services

*2. Retry Logic*
- RPC calls retry up to 3 times
- Exponential backoff between retries
- Service marked as failed after max retries

*3. Circuit Breaker*
- Opens after 3 consecutive failures
- Prevents cascading failures
- Auto-recovery after 30-second timeout

*4. Graceful Degradation*
- Applications continue with available services
- Missing sensors handled gracefully
- Clear error messages

#### Adding Custom Sensors

*Step 1: Define sensor reading logic*

```python
def read_sensor(self):
    if self.sensor_config["type"] == "my_custom":
        ## Your custom reading logic
        value = self.custom_read()
        return {"value": value, "unit": "custom"}
```

*Step 2: Initialise hardware*

```python
def _init_sensor(self):
    if self.sensor_config["type"] == "my_custom":
        self.sensor = MyCustomSensor(pin=self.sensor_config["pin"])
```

*Step 3: Create and run*

```python
sensor = SensorNode("my_custom_sensor", {
    "type": "my_custom",
    "pin": 20,
    "params": {"calibration": 1.5}
})
sensor.run()
```

#### Display Support

TDOS supports multiple display types:

*Pimoroni Pico Display Pack:*
```python
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
## Auto-detected if library present
```

*SSD1306 OLED (I2C):*
```python
from machine import I2C, Pin
import ssd1306

i2c = I2C(0, scl=Pin(1), sda=Pin(0))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
## Auto-detected if configured
```

*Console fallback:*
```python
## Automatically used if no display hardware
```



### Example Applications

#### 1. Weather Station

Collects data from multiple sensors and displays:

```python
from weather_station import main
main()
```

*Features:*
- Auto-discovers all sensors
- Updates every 5 seconds
- Shows temp, humidity, light
- Displays service count

#### 2. Data Logger

Logs sensor data to file:

```python
from data_logger import DataLogger

logger = DataLogger(
    log_file="data.txt",
    log_interval=10,
    batch_size=6
)
logger.log_sensors()
```

*Features:*
- Batched file writes
- Timestamped entries
- Handles sensor failures
- Shows statistics

#### 3. System Monitor

Monitors TDOS health:

```python
from monitor import main
main()
```

*Features:*
- Service status table
- RPC success/failure rates
- Uptime tracking
- Live service tests

#### 4. Alert System

Temperature monitoring with thresholds:

```python
from alert_system import AlertSystem

alert = AlertSystem(temp_min=18.0, temp_max=25.0)
alert.run()
```

*Features:*
- Configurable thresholds
- Alert triggering
- Display notifications
- Alert counting



### Troubleshooting

#### Common Issues

*Services not discovered:*
```
- Check WiFi connection on all boards
- Verify same SSID/password
- Check firewall (allow UDP 4000, 5000)
- Verify boards on same subnet
```

*Sensor reads return None:*
```
- Check service is still alive (heartbeat)
- Verify sensor hardware connected
- Check circuit breaker state
- Review error logs
```

*Display not working:*
```
- Verify display library installed
- Check I2C/SPI connections
- Falls back to console automatically
```

*WiFi connection fails:*
```
- Verify SSID and password
- Check signal strength
- Try increasing timeout
- Reset board and retry
```

#### Debug Output

Enable verbose logging:

```python
## In protocol.py, sensor_node.py, or tinyos.py
## All print statements show bracketed categories:
## [WiFi], [Network], [Discovery], [Registry], etc.
```

#### Testing Individual Components

*Test sensor reading:*
```python
from sensor_node import SensorNode

sensor = SensorNode("test", {"type": "simulated"})
print(sensor.read_sensor())
```

*Test network connectivity:*
```python
import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print("MAC:", wlan.config('mac'))
print("Connected:", wlan.isconnected())
print("IP:", wlan.ifconfig()[0] if wlan.isconnected() else "None")
```



### Performance Characteristics

#### Network Bandwidth

- Service announcement: ~200 bytes every 30s
- Heartbeat: ~80 bytes every 5s
- RPC request+response: ~150 bytes per call
- *Total per sensor*: ~1-2 KB/minute

#### Memory Usage

- Protocol library: ~5 KB
- Sensor node: ~8 KB
- Kernel node: ~12 KB
- *Total RAM*: ~25 KB (Pico has 264 KB)

#### Latency

- Service discovery: 0-3 seconds
- RPC call: 20-100 ms (depends on network)
- Timeout handling: 2 seconds default
- Circuit breaker recovery: 30 seconds

#### Scalability

- *Tested*: 10 sensor nodes + 1 kernel
- *Theoretical*: 50+ nodes (limited by broadcast traffic)
- *Recommended*: 20 nodes for best performance



### Future Enhancements

Possible improvements:

1. *Multicast instead of broadcast* - Reduce network traffic
2. *Service priorities* - Prefer certain services
3. *Load balancing* - Multiple instances of same service
4. *Persistent storage* - Save/restore registry
5. *Security* - Message signing/encryption
6. *Time synchronization* - NTP integration
7. *Event streaming* - Pub/sub pattern
8. *Service dependencies* - Declare requirements
9. *Health metrics* - Detailed performance stats
10. *Web interface* - HTTP API and dashboard


### Contributing

To extend TDOS:

1. Add message types to `MessageType` class
2. Implement handlers in sensor/kernel nodes
3. Test with fault injection
4. Document protocol changes
5. Update version numbers

