# sensor_node.py - TDOS Sensor Node Implementation
"""
Fully functional sensor node with WiFi connectivity, service announcement,
heartbeat monitoring, and RPC handling.
"""

import network
import socket
import time
import machine
import _thread
from protocol import (TDOSMessage, MessageType, HEARTBEAT_INTERVAL, 
                     MAX_MESSAGE_SIZE, CircuitBreaker)

class SensorNode:
    """Sensor node that registers with TDOS network"""
    
    def __init__(self, service_name, sensor_config=None):
        """
        Initialize sensor node
        
        Args:
            service_name: Unique name for this service
            sensor_config: Dict with sensor configuration:
                - type: "adc", "dht22", "bme280", "simulated"
                - pin: GPIO pin number (if applicable)
                - params: Additional sensor-specific parameters
        """
        self.service_name = service_name
        self.sensor_config = sensor_config or {"type": "simulated"}
        self.running = True
        self.socket = None
        self.broadcast_socket = None
        self.wlan = None
        self.my_ip = None
        self.circuit_breaker = CircuitBreaker()
        
        # Initialize sensor based on config
        self._init_sensor()
        
        # Statistics
        self.stats = {
            "requests_handled": 0,
            "errors": 0,
            "uptime_start": time.time()
        }
    
    def _init_sensor(self):
        """Initialize sensor hardware"""
        sensor_type = self.sensor_config.get("type", "simulated")
        
        if sensor_type == "adc":
            pin_num = self.sensor_config.get("pin", 26)
            self.sensor = machine.ADC(pin_num)
            print(f"[Sensor] Initialized ADC on pin {pin_num}")
            
        elif sensor_type == "dht22":
            try:
                import dht
                pin_num = self.sensor_config.get("pin", 15)
                self.sensor = dht.DHT22(machine.Pin(pin_num))
                print(f"[Sensor] Initialized DHT22 on pin {pin_num}")
            except ImportError:
                print("[Sensor] DHT library not available, using simulated")
                self.sensor_config["type"] = "simulated"
                self.sensor = None
                
        elif sensor_type == "digital":
            pin_num = self.sensor_config.get("pin", 16)
            self.sensor = machine.Pin(pin_num, machine.Pin.IN)
            print(f"[Sensor] Initialized digital input on pin {pin_num}")
            
        else:
            self.sensor = None
            print("[Sensor] Using simulated sensor")
    
    def connect_wifi(self, ssid, password, timeout=20):
        """Connect to WiFi network"""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        if self.wlan.isconnected():
            self.my_ip = self.wlan.ifconfig()[0]
            print(f"[WiFi] Already connected to {ssid}, IP: {self.my_ip}")
            return self.my_ip
        
        print(f"[WiFi] Connecting to {ssid}...")
        self.wlan.connect(ssid, password)
        
        start_time = time.time()
        while not self.wlan.isconnected() and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        if self.wlan.isconnected():
            self.my_ip = self.wlan.ifconfig()[0]
            print(f"[WiFi] Connected! IP: {self.my_ip}")
            return self.my_ip
        else:
            raise RuntimeError("Failed to connect to WiFi")
    
    def setup_sockets(self, service_port=5000, discovery_port=4000):
        """Setup UDP sockets for communication"""
        try:
            # Service socket for receiving RPC requests
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('', service_port))
            self.socket.settimeout(1.0)
            print(f"[Network] Service socket bound to port {service_port}")
            
            # Broadcast socket for announcements
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            print(f"[Network] Broadcast socket ready")
            
            self.service_port = service_port
            self.discovery_port = discovery_port
            
        except Exception as e:
            print(f"[Network] Error setting up sockets: {e}")
            raise
    
    def read_sensor(self):
        """Read sensor value based on sensor type"""
        sensor_type = self.sensor_config.get("type", "simulated")
        
        try:
            if sensor_type == "adc":
                # ADC reading (0-65535)
                raw = self.sensor.read_u16()
                # Convert to percentage
                value = (raw / 65535) * 100
                return {"value": round(value, 2), "unit": "%", "raw": raw}
                
            elif sensor_type == "dht22":
                self.sensor.measure()
                temp = self.sensor.temperature()
                humidity = self.sensor.humidity()
                return {
                    "temperature": round(temp, 1),
                    "humidity": round(humidity, 1),
                    "unit": "°C/%"
                }
                
            elif sensor_type == "digital":
                value = self.sensor.value()
                return {"value": value, "unit": "digital"}
                
            else:  # simulated
                # Generate simulated data based on service name
                if "temp" in self.service_name.lower():
                    base = 20.0
                    variation = (time.time() % 20) - 10
                    value = base + variation
                    return {"value": round(value, 1), "unit": "°C"}
                    
                elif "humidity" in self.service_name.lower():
                    base = 50.0
                    variation = (time.time() % 30) - 15
                    value = base + variation
                    return {"value": round(value, 1), "unit": "%"}
                    
                elif "light" in self.service_name.lower():
                    base = 50.0
                    variation = (time.time() % 40) - 20
                    value = max(0, min(100, base + variation))
                    return {"value": round(value, 1), "unit": "%"}
                    
                else:
                    return {"value": time.time() % 100, "unit": "units"}
                    
        except Exception as e:
            print(f"[Sensor] Error reading sensor: {e}")
            return {"error": str(e)}
    
    def announce_service(self):
        """Broadcast service announcement"""
        msg = TDOSMessage(
            MessageType.SERVICE_ANNOUNCE,
            {
                "service": self.service_name,
                "port": self.service_port,
                "capabilities": ["read", "status"],
                "sensor_type": self.sensor_config.get("type", "unknown"),
                "metadata": {
                    "uptime": int(time.time() - self.stats["uptime_start"]),
                    "requests": self.stats["requests_handled"]
                }
            }
        )
        
        try:
            data = msg.serialize()
            if len(data) <= MAX_MESSAGE_SIZE:
                self.broadcast_socket.sendto(data, ('<broadcast>', self.discovery_port))
            else:
                print(f"[Network] Announcement too large: {len(data)} bytes")
        except Exception as e:
            print(f"[Network] Failed to announce service: {e}")
    
    def send_heartbeat(self):
        """Send heartbeat to indicate service is alive"""
        msg = TDOSMessage(
            MessageType.HEARTBEAT,
            {
                "service": self.service_name,
                "status": "healthy",
                "uptime": int(time.time() - self.stats["uptime_start"])
            }
        )
        
        try:
            data = msg.serialize()
            self.broadcast_socket.sendto(data, ('<broadcast>', self.discovery_port))
        except Exception as e:
            print(f"[Network] Failed to send heartbeat: {e}")
    
    def handle_request(self, request_msg, client_addr):
        """Handle incoming RPC request"""
        try:
            operation = request_msg.payload.get("op", "unknown")
            
            if operation == "read":
                # Read sensor value
                reading = self.read_sensor()
                response = TDOSMessage(
                    MessageType.RPC_RESPONSE,
                    reading,
                    reply_to=request_msg.msg_id
                )
                self.stats["requests_handled"] += 1
                
            elif operation == "status":
                # Return node status
                response = TDOSMessage(
                    MessageType.RPC_RESPONSE,
                    {
                        "service": self.service_name,
                        "uptime": int(time.time() - self.stats["uptime_start"]),
                        "requests": self.stats["requests_handled"],
                        "errors": self.stats["errors"],
                        "ip": self.my_ip
                    },
                    reply_to=request_msg.msg_id
                )
                
            else:
                # Unknown operation
                response = TDOSMessage(
                    MessageType.ERROR,
                    {"error": f"Unknown operation: {operation}"},
                    reply_to=request_msg.msg_id
                )
                self.stats["errors"] += 1
            
            # Send response
            self.socket.sendto(response.serialize(), client_addr)
            
        except Exception as e:
            print(f"[Handler] Error handling request: {e}")
            self.stats["errors"] += 1
            
            # Send error response
            try:
                error_response = TDOSMessage(
                    MessageType.ERROR,
                    {"error": str(e)},
                    reply_to=request_msg.msg_id
                )
                self.socket.sendto(error_response.serialize(), client_addr)
            except:
                pass  # Best effort
    
    def heartbeat_worker(self):
        """Background thread for sending heartbeats"""
        print("[Heartbeat] Worker started")
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                print(f"[Heartbeat] Error: {e}")
                time.sleep(HEARTBEAT_INTERVAL)
    
    def run(self, ssid="TDOS_Network", password="tdos12345"):
        """Main run loop"""
        print(f"[{self.service_name}] Starting...")
        
        # Connect to WiFi
        self.connect_wifi(ssid, password)
        
        # Setup networking
        self.setup_sockets()
        
        # Initial service announcement
        self.announce_service()
        
        # Start heartbeat thread
        _thread.start_new_thread(self.heartbeat_worker, ())
        
        print(f"[{self.service_name}] Running on {self.my_ip}:{self.service_port}")
        
        last_announce = time.time()
        announce_interval = 30  # Re-announce every 30 seconds
        
        while self.running:
            try:
                # Periodic re-announcement
                if time.time() - last_announce > announce_interval:
                    self.announce_service()
                    last_announce = time.time()
                
                # Handle incoming requests
                try:
                    data, addr = self.socket.recvfrom(MAX_MESSAGE_SIZE)
                    msg = TDOSMessage.deserialize(data)
                    
                    if msg.msg_type == MessageType.RPC_REQUEST:
                        self.handle_request(msg, addr)
                        
                except socket.timeout:
                    continue
                except ValueError as e:
                    print(f"[Network] Invalid message: {e}")
                    
            except KeyboardInterrupt:
                print("\n[Main] Shutting down...")
                break
            except Exception as e:
                print(f"[Main] Error in main loop: {e}")
                time.sleep(1)
        
        self.cleanup()
    
    def cleanup(self):
        """Clean shutdown"""
        print(f"[{self.service_name}] Cleaning up...")
        self.running = False
        
        # Send goodbye message
        try:
            msg = TDOSMessage(
                MessageType.SERVICE_GOODBYE,
                {"service": self.service_name}
            )
            self.broadcast_socket.sendto(msg.serialize(), ('<broadcast>', self.discovery_port))
        except:
            pass
        
        # Close sockets
        if self.socket:
            self.socket.close()
        if self.broadcast_socket:
            self.broadcast_socket.close()
        
        print(f"[{self.service_name}] Shutdown complete")


# Example configurations
def create_temp_sensor():
    """Create temperature sensor node"""
    return SensorNode("temp_sensor", {"type": "simulated"})

def create_humidity_sensor():
    """Create humidity sensor node"""
    return SensorNode("humidity_sensor", {"type": "simulated"})

def create_light_sensor(pin=26):
    """Create light sensor node with ADC"""
    return SensorNode("light_sensor", {"type": "adc", "pin": pin})

def create_dht22_sensor(pin=15):
    """Create DHT22 temperature/humidity sensor"""
    return SensorNode("climate_sensor", {"type": "dht22", "pin": pin})


# Main entry point
if __name__ == "__main__":
    # Configuration - change these for your setup
    WIFI_SSID = "TDOS_Network"
    WIFI_PASSWORD = "tdos12345"
    
    # Choose sensor type:
    # Option 1: Simulated temperature sensor
    sensor = create_temp_sensor()
    
    # Option 2: Real ADC light sensor
    # sensor = create_light_sensor(pin=26)
    
    # Option 3: DHT22 sensor
    # sensor = create_dht22_sensor(pin=15)
    
    # Run the sensor node
    sensor.run(WIFI_SSID, WIFI_PASSWORD)
