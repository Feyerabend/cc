# tinyos.py - TDOS Kernel Node Implementation
"""
Kernel node that discovers services, manages registry, and provides
unified API for accessing distributed resources.
"""

import network
import socket
import time
import _thread
from protocol import (TDOSMessage, MessageType, ServiceRegistry, 
                     MAX_MESSAGE_SIZE, CircuitBreaker)

# Try to import display libraries
HAS_DISPLAY = False
try:
    # Pimoroni Pico Display Pack
    from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
    display_driver = PicoGraphics(display=DISPLAY_PICO_DISPLAY)
    HAS_DISPLAY = True
    print("[Display] Pimoroni display available")
except ImportError:
    try:
        # SSD1306 OLED
        from machine import I2C, Pin
        import ssd1306
        i2c = I2C(0, scl=Pin(1), sda=Pin(0))
        display_driver = ssd1306.SSD1306_I2C(128, 64, i2c)
        HAS_DISPLAY = True
        print("[Display] SSD1306 display available")
    except:
        display_driver = None
        print("[Display] No display hardware, using console")


class TinyOS:
    """Main TDOS kernel for service discovery and coordination"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self.display_driver = display_driver
        self.discovery_socket = None
        self.client_socket = None
        self.running = True
        self.wlan = None
        self.my_ip = None
        self.circuit_breakers = {}  # service_name -> CircuitBreaker
        
        # Statistics
        self.stats = {
            "services_discovered": 0,
            "rpc_calls": 0,
            "rpc_failures": 0,
            "uptime_start": time.time()
        }
    
    def connect_wifi(self, ssid="TDOS_Network", password="tdos12345", timeout=20):
        """Connect to WiFi network"""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        if self.wlan.isconnected():
            self.my_ip = self.wlan.ifconfig()[0]
            print(f"[WiFi] Already connected, IP: {self.my_ip}")
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
    
    def init(self, ssid="TDOS_Network", password="tdos12345"):
        """Initialize TDOS kernel"""
        print("[TDOS] Initializing...")
        
        # Connect to network
        self.connect_wifi(ssid, password)
        
        # Setup sockets
        self._setup_sockets()
        
        # Start background workers
        _thread.start_new_thread(self._discovery_worker, ())
        _thread.start_new_thread(self._cleanup_worker, ())
        
        # Wait for initial service discovery
        print("[TDOS] Discovering services...")
        time.sleep(3)
        
        # Display discovered services
        services = self.registry.list_services()
        print(f"[TDOS] Discovered {len(services)} services:")
        for name in services:
            service = self.registry.get_service(name)
            print(f"  - {name} at {service.ip}:{service.port}")
        
        print("[TDOS] Initialization complete")
    
    def _setup_sockets(self):
        """Setup network sockets"""
        try:
            # Discovery socket (listens for service announcements)
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.bind(('', 4000))
            self.discovery_socket.settimeout(0.5)
            print("[Network] Discovery socket bound to port 4000")
            
            # Client socket (for RPC calls)
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.settimeout(2.0)
            print("[Network] Client socket ready")
            
        except Exception as e:
            print(f"[Network] Error setting up sockets: {e}")
            raise
    
    def _discovery_worker(self):
        """Background thread for service discovery"""
        print("[Discovery] Worker started")
        
        while self.running:
            try:
                data, addr = self.discovery_socket.recvfrom(MAX_MESSAGE_SIZE)
                msg = TDOSMessage.deserialize(data)
                
                if msg.msg_type == MessageType.SERVICE_ANNOUNCE:
                    # New service announcement
                    service_name = msg.payload.get("service")
                    port = msg.payload.get("port", 5000)
                    metadata = {
                        "capabilities": msg.payload.get("capabilities", []),
                        "sensor_type": msg.payload.get("sensor_type", "unknown"),
                        "extra": msg.payload.get("metadata", {})
                    }
                    
                    was_new = service_name not in self.registry.services
                    self.registry.register_service(service_name, addr[0], port, metadata)
                    
                    if was_new:
                        self.stats["services_discovered"] += 1
                        # Create circuit breaker for new service
                        self.circuit_breakers[service_name] = CircuitBreaker()
                
                elif msg.msg_type == MessageType.HEARTBEAT:
                    # Heartbeat update
                    service_name = msg.payload.get("service")
                    self.registry.update_heartbeat(service_name, addr[0])
                
                elif msg.msg_type == MessageType.SERVICE_GOODBYE:
                    # Service shutting down
                    service_name = msg.payload.get("service")
                    self.registry.remove_service(service_name)
                    
            except socket.timeout:
                continue
            except ValueError as e:
                print(f"[Discovery] Invalid message: {e}")
            except Exception as e:
                print(f"[Discovery] Error: {e}")
    
    def _cleanup_worker(self):
        """Background thread for cleanup tasks"""
        print("[Cleanup] Worker started")
        
        while self.running:
            time.sleep(10)
            
            # Cleanup stale services
            removed = self.registry.cleanup_stale_services()
            if removed > 0:
                print(f"[Cleanup] Removed {removed} stale services")
            
            # Cleanup pending requests
            expired = self.registry.cleanup_pending_requests()
            if expired > 0:
                print(f"[Cleanup] Cleaned {expired} expired requests")
    
    def open_display(self):
        """Open display resource"""
        if HAS_DISPLAY:
            print("[TDOS] Display opened")
            return "display"
        else:
            print("[TDOS] Console display opened")
            return "console"
    
    def open_sensor(self, sensor_name):
        """
        Open sensor resource
        
        Args:
            sensor_name: Name of sensor service
            
        Returns:
            Sensor handle (service name)
            
        Raises:
            RuntimeError: If sensor not available
        """
        service = self.registry.get_service(sensor_name)
        if service:
            print(f"[TDOS] Opened sensor: {sensor_name}")
            return sensor_name
        else:
            available = self.registry.list_services()
            raise RuntimeError(
                f"Sensor '{sensor_name}' not available. "
                f"Available services: {', '.join(available) if available else 'none'}"
            )
    
    # Convenience methods for common sensors
    def open_temp_sensor(self):
        """Open temperature sensor"""
        return self.open_sensor("temp_sensor")
    
    def open_humidity_sensor(self):
        """Open humidity sensor"""
        return self.open_sensor("humidity_sensor")
    
    def open_light_sensor(self):
        """Open light sensor"""
        return self.open_sensor("light_sensor")
    
    def write(self, handle, message):
        """
        Write to a resource
        
        Args:
            handle: Resource handle (e.g., "display", "console")
            message: Message to write
        """
        if handle == "display" and HAS_DISPLAY:
            try:
                # Check if it's Pimoroni or SSD1306
                if hasattr(self.display_driver, 'set_pen'):
                    # Pimoroni display
                    self.display_driver.set_pen(0)
                    self.display_driver.clear()
                    self.display_driver.set_pen(1)
                    self.display_driver.text(str(message), 10, 10, scale=2)
                    self.display_driver.update()
                else:
                    # SSD1306 display
                    self.display_driver.fill(0)
                    lines = str(message).split('\n')
                    for i, line in enumerate(lines[:8]):  # Max 8 lines
                        self.display_driver.text(line[:16], 0, i * 8)  # Max 16 chars
                    self.display_driver.show()
            except Exception as e:
                print(f"[Display] Error: {e}")
                print(f"DISPLAY: {message}")
        else:
            # Console output
            print(f"DISPLAY: {message}")
    
    def read(self, handle, timeout=2.0):
        """
        Read from a sensor
        
        Args:
            handle: Sensor handle (service name)
            timeout: Read timeout in seconds
            
        Returns:
            Sensor reading or None on failure
        """
        service = self.registry.get_service(handle)
        if not service:
            print(f"[TDOS] Service {handle} not available")
            return None
        
        # Check circuit breaker
        if handle not in self.circuit_breakers:
            self.circuit_breakers[handle] = CircuitBreaker()
        
        breaker = self.circuit_breakers[handle]
        if not breaker.can_attempt():
            print(f"[TDOS] Circuit breaker open for {handle}")
            return None
        
        # Try to read with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Create RPC request
                request = TDOSMessage(
                    MessageType.RPC_REQUEST,
                    {"op": "read"}
                )
                
                # Send request
                addr = (service.ip, service.port)
                self.client_socket.sendto(request.serialize(), addr)
                self.stats["rpc_calls"] += 1
                
                # Wait for response
                start_time = time.time()
                while (time.time() - start_time) < timeout:
                    try:
                        data, _ = self.client_socket.recvfrom(MAX_MESSAGE_SIZE)
                        response = TDOSMessage.deserialize(data)
                        
                        # Check if this is our response
                        if response.reply_to == request.msg_id:
                            if response.msg_type == MessageType.RPC_RESPONSE:
                                # Success
                                breaker.record_success()
                                return response.payload
                            elif response.msg_type == MessageType.ERROR:
                                print(f"[TDOS] Service error from {handle}: {response.payload.get('error')}")
                                breaker.record_failure()
                                self.stats["rpc_failures"] += 1
                                return None
                    except socket.timeout:
                        continue
                
                # Timeout
                print(f"[TDOS] Timeout reading {handle} (attempt {attempt + 1}/{max_retries})")
                self.registry.mark_service_failure(handle)
                breaker.record_failure()
                self.stats["rpc_failures"] += 1
                
            except Exception as e:
                print(f"[TDOS] Error reading {handle}: {e}")
                self.registry.mark_service_failure(handle)
                breaker.record_failure()
                self.stats["rpc_failures"] += 1
        
        return None  # All retries failed
    
    def list_services(self):
        """Get list of available services"""
        return self.registry.list_services()
    
    def get_service_info(self, service_name):
        """Get detailed service information"""
        service = self.registry.get_service(service_name)
        return service.to_dict() if service else None
    
    def get_stats(self):
        """Get kernel statistics"""
        return {
            **self.stats,
            "uptime": int(time.time() - self.stats["uptime_start"]),
            "active_services": len(self.registry.list_services()),
            "total_services": len(self.registry.services)
        }
    
    def shutdown(self):
        """Shutdown TDOS kernel"""
        print("[TDOS] Shutting down...")
        self.running = False
        
        if self.discovery_socket:
            self.discovery_socket.close()
        if self.client_socket:
            self.client_socket.close()
        
        print("[TDOS] Shutdown complete")


# Global instance for convenient API
_tinyos = None

def init(ssid="TDOS_Network", password="tdos12345"):
    """Initialize TDOS"""
    global _tinyos
    _tinyos = TinyOS()
    _tinyos.init(ssid, password)

def open_display():
    """Open display resource"""
    return _tinyos.open_display()

def open_temp_sensor():
    """Open temperature sensor"""
    return _tinyos.open_temp_sensor()

def open_humidity_sensor():
    """Open humidity sensor"""
    return _tinyos.open_humidity_sensor()

def open_light_sensor():
    """Open light sensor"""
    return _tinyos.open_light_sensor()

def open_sensor(name):
    """Open named sensor"""
    return _tinyos.open_sensor(name)

def write(handle, message):
    """Write to resource"""
    _tinyos.write(handle, message)

def read(handle):
    """Read from sensor"""
    return _tinyos.read(handle)

def list_services():
    """List available services"""
    return _tinyos.list_services()

def get_service_info(name):
    """Get service information"""
    return _tinyos.get_service_info(name)

def get_stats():
    """Get statistics"""
    return _tinyos.get_stats()

def shutdown():
    """Shutdown TDOS"""
    _tinyos.shutdown()


# Example usage
if __name__ == "__main__":
    # Initialize TDOS
    init()
    
    # Open display
    display = open_display()
    
    # Try to open sensors
    try:
        temp = open_temp_sensor()
        print("Temperature sensor available")
    except RuntimeError as e:
        print(f"Temperature sensor not available: {e}")
        temp = None
    
    # Main loop
    try:
        while True:
            message_lines = []
            
            # Read temperature
            if temp:
                reading = read(temp)
                if reading:
                    value = reading.get("value")
                    unit = reading.get("unit", "")
                    message_lines.append(f"Temp: {value}{unit}")
            
            # List services
            services = list_services()
            message_lines.append(f"Services: {len(services)}")
            
            # Display
            message = "\n".join(message_lines) if message_lines else "No data"
            write(display, message)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        shutdown()
