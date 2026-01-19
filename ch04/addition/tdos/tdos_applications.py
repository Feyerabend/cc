# weather_station.py - Multi-sensor weather monitoring application
"""
Example application that collects data from multiple sensors
and displays it on a screen or console.
"""

import tinyos
import time

def format_reading(reading):
    """Format a sensor reading for display"""
    if not reading:
        return "N/A"
    
    if "error" in reading:
        return f"Error: {reading['error']}"
    
    # Handle different reading formats
    if "temperature" in reading and "humidity" in reading:
        # DHT22-style reading
        temp = reading.get("temperature", "?")
        humidity = reading.get("humidity", "?")
        return f"T:{temp}°C H:{humidity}%"
    elif "value" in reading:
        # Simple value reading
        value = reading["value"]
        unit = reading.get("unit", "")
        return f"{value:.1f}{unit}"
    else:
        return str(reading)

def main():
    """Main weather station application"""
    print("=== Weather Station Application ===")
    
    # Initialize TDOS
    tinyos.init()
    
    # Open display
    display = tinyos.open_display()
    
    # Try to discover and open sensors
    available_sensors = {}
    sensor_names = ["temp_sensor", "humidity_sensor", "light_sensor", "climate_sensor"]
    
    for sensor_name in sensor_names:
        try:
            handle = tinyos.open_sensor(sensor_name)
            available_sensors[sensor_name] = handle
            print(f"✓ Opened {sensor_name}")
        except RuntimeError:
            print(f"✗ {sensor_name} not available")
    
    if not available_sensors:
        print("No sensors available!")
        tinyos.write(display, "No sensors\navailable")
        return
    
    print(f"\nMonitoring {len(available_sensors)} sensors...")
    print("Press Ctrl+C to stop\n")
    
    update_count = 0
    
    try:
        while True:
            update_count += 1
            readings = {}
            
            # Collect all sensor readings
            for name, handle in available_sensors.items():
                reading = tinyos.read(handle)
                if reading:
                    readings[name] = reading
            
            # Format display message
            display_lines = []
            display_lines.append(f"Update #{update_count}")
            display_lines.append("")
            
            # Add sensor readings
            if "temp_sensor" in readings:
                display_lines.append(f"Temp: {format_reading(readings['temp_sensor'])}")
            
            if "humidity_sensor" in readings:
                display_lines.append(f"Humidity: {format_reading(readings['humidity_sensor'])}")
            
            if "light_sensor" in readings:
                display_lines.append(f"Light: {format_reading(readings['light_sensor'])}")
            
            if "climate_sensor" in readings:
                display_lines.append(f"Climate: {format_reading(readings['climate_sensor'])}")
            
            # Show service count
            services = tinyos.list_services()
            display_lines.append("")
            display_lines.append(f"Services: {len(services)}")
            
            # Display and print
            message = "\n".join(display_lines)
            tinyos.write(display, message)
            
            # Console output
            print(f"\n--- Update #{update_count} ---")
            for name, reading in readings.items():
                print(f"{name}: {format_reading(reading)}")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nShutting down weather station...")
        tinyos.shutdown()

if __name__ == "__main__":
    main()


# ==============================================================================


# data_logger.py - Distributed data logging application
"""
Application that logs sensor data to a file with timestamps.
Demonstrates graceful handling of service failures.
"""

import tinyos
import time

class DataLogger:
    """Data logger for TDOS sensors"""
    
    def __init__(self, log_file="sensor_log.txt", log_interval=10, batch_size=10):
        self.log_file = log_file
        self.log_interval = log_interval
        self.batch_size = batch_size
        self.data_buffer = []
        self.total_logged = 0
    
    def log_sensors(self):
        """Main logging loop"""
        print("=== Data Logger Application ===")
        
        # Initialize TDOS
        tinyos.init()
        
        print(f"Logging to: {self.log_file}")
        print(f"Interval: {self.log_interval}s")
        print(f"Batch size: {self.batch_size}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self._collect_data()
                
                # Flush buffer if it's full
                if len(self.data_buffer) >= self.batch_size:
                    self._flush_to_file()
                
                time.sleep(self.log_interval)
                
        except KeyboardInterrupt:
            print("\n\nShutting down logger...")
            # Flush any remaining data
            if self.data_buffer:
                self._flush_to_file()
            print(f"Total records logged: {self.total_logged}")
            tinyos.shutdown()
    
    def _collect_data(self):
        """Collect data from all available sensors"""
        timestamp = time.time()
        data_point = {
            "timestamp": timestamp,
            "readings": {}
        }
        
        # Get all available services
        services = tinyos.list_services()
        
        # Read from each sensor service
        for service_name in services:
            if "_sensor" in service_name:
                try:
                    # Open and read sensor
                    handle = tinyos.open_sensor(service_name)
                    reading = tinyos.read(handle)
                    
                    if reading and "error" not in reading:
                        data_point["readings"][service_name] = reading
                        
                except Exception as e:
                    print(f"Error reading {service_name}: {e}")
        
        # Only log if we got some readings
        if data_point["readings"]:
            self.data_buffer.append(data_point)
            
            # Print to console
            print(f"[{time.localtime(int(timestamp))[3]:02d}:{time.localtime(int(timestamp))[4]:02d}:{time.localtime(int(timestamp))[5]:02d}] ", end="")
            for sensor, reading in data_point["readings"].items():
                if "value" in reading:
                    print(f"{sensor}={reading['value']:.1f}{reading.get('unit', '')} ", end="")
            print()
        else:
            print("No sensor data available")
    
    def _flush_to_file(self):
        """Write buffered data to file"""
        if not self.data_buffer:
            return
        
        try:
            with open(self.log_file, "a") as f:
                for entry in self.data_buffer:
                    # Format: timestamp | sensor1=value1,unit1 | sensor2=value2,unit2 | ...
                    timestamp_str = str(int(entry["timestamp"]))
                    
                    sensor_parts = []
                    for sensor, reading in entry["readings"].items():
                        if "value" in reading:
                            value = reading["value"]
                            unit = reading.get("unit", "")
                            sensor_parts.append(f"{sensor}={value}{unit}")
                    
                    line = f"{timestamp_str} | {' | '.join(sensor_parts)}\n"
                    f.write(line)
            
            count = len(self.data_buffer)
            self.total_logged += count
            self.data_buffer.clear()
            print(f"✓ Flushed {count} records to {self.log_file} (total: {self.total_logged})")
            
        except Exception as e:
            print(f"✗ Error writing to file: {e}")

if __name__ == "__main__":
    logger = DataLogger(log_interval=5, batch_size=6)
    logger.log_sensors()


# ==============================================================================


# monitor.py - System monitoring and diagnostics
"""
Application for monitoring TDOS system health and performance.
"""

import tinyos
import time

def print_service_table(services_info):
    """Print formatted table of services"""
    print("\n" + "="*70)
    print(f"{'Service Name':<20} {'IP Address':<15} {'State':<10} {'Failures':<8}")
    print("="*70)
    
    for name, info in services_info.items():
        print(f"{name:<20} {info['ip']:<15} {info['state']:<10} {info['failures']:<8}")
    
    print("="*70)

def main():
    """Main monitoring application"""
    print("=== TDOS System Monitor ===\n")
    
    # Initialize TDOS
    tinyos.init()
    
    print("\nMonitoring system...")
    print("Press Ctrl+C to stop\n")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            
            # Get system stats
            stats = tinyos.get_stats()
            
            # Get service information
            service_names = tinyos.list_services()
            services_info = {}
            for name in service_names:
                info = tinyos.get_service_info(name)
                if info:
                    services_info[name] = info
            
            # Display stats
            print(f"\n--- Update {iteration} ---")
            print(f"Uptime: {stats['uptime']}s")
            print(f"Active Services: {stats['active_services']}")
            print(f"Total Discovered: {stats['services_discovered']}")
            print(f"RPC Calls: {stats['rpc_calls']} (Failures: {stats['rpc_failures']})")
            
            # Display service table
            if services_info:
                print_service_table(services_info)
            else:
                print("\nNo services available")
            
            # Test reading from each service
            print("\nService Tests:")
            for name in service_names:
                if "_sensor" in name:
                    reading = tinyos.read(name)
                    status = "✓" if reading else "✗"
                    print(f"  {status} {name}: {reading if reading else 'Failed'}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nShutting down monitor...")
        tinyos.shutdown()

if __name__ == "__main__":
    main()


# ==============================================================================


# alert_system.py - Temperature alert system
"""
Application that monitors temperature and triggers alerts
when thresholds are exceeded.
"""

import tinyos
import time

class AlertSystem:
    """Alert system for monitoring sensor thresholds"""
    
    def __init__(self, temp_min=15.0, temp_max=30.0):
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.alert_active = False
        self.alert_count = 0
    
    def run(self):
        """Main alert system loop"""
        print("=== Temperature Alert System ===")
        print(f"Min Temp: {self.temp_min}°C")
        print(f"Max Temp: {self.temp_max}°C")
        print()
        
        # Initialize TDOS
        tinyos.init()
        
        # Open resources
        display = tinyos.open_display()
        
        try:
            temp_sensor = tinyos.open_temp_sensor()
            print("✓ Temperature sensor ready")
        except RuntimeError:
            print("✗ Temperature sensor not available")
            return
        
        print("\nMonitoring temperature...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Read temperature
                reading = tinyos.read(temp_sensor)
                
                if reading and "value" in reading:
                    temp = reading["value"]
                    
                    # Check thresholds
                    if temp < self.temp_min:
                        self._trigger_alert("LOW", temp, display)
                    elif temp > self.temp_max:
                        self._trigger_alert("HIGH", temp, display)
                    else:
                        self._clear_alert(temp, display)
                else:
                    print("Failed to read temperature")
                    tinyos.write(display, "Sensor Error")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print(f"\n\nTotal alerts: {self.alert_count}")
            tinyos.shutdown()
    
    def _trigger_alert(self, alert_type, temp, display):
        """Trigger an alert"""
        if not self.alert_active:
            self.alert_active = True
            self.alert_count += 1
            print(f"\n!!! ALERT: Temperature {alert_type} ({temp:.1f}°C) !!!")
        
        message = f"ALERT!\nTemp {alert_type}\n{temp:.1f}°C"
        tinyos.write(display, message)
    
    def _clear_alert(self, temp, display):
        """Clear alert state"""
        if self.alert_active:
            self.alert_active = False
            print(f"Alert cleared - temperature normal ({temp:.1f}°C)")
        
        message = f"Temp Normal\n{temp:.1f}°C"
        tinyos.write(display, message)

if __name__ == "__main__":
    alert = AlertSystem(temp_min=18.0, temp_max=25.0)
    alert.run()
