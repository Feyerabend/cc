# wifi_ap.py - WiFi Access Point for TDOS
"""
Create a WiFi access point on a Pico W to allow other nodes to connect.
This can be run on a dedicated Pico W or combined with a kernel/sensor node.
"""

import network
import time

class TDOSAccessPoint:
    """WiFi Access Point for TDOS network"""
    
    def __init__(self, ssid="TDOS_Network", password="tdos12345", channel=6):
        """
        Initialize access point
        
        Args:
            ssid: Network name
            password: Network password (min 8 chars)
            channel: WiFi channel (1-13)
        """
        self.ssid = ssid
        self.password = password
        self.channel = channel
        self.ap = None
    
    def start(self):
        """Start the access point"""
        print("=== TDOS WiFi Access Point ===\n")
        
        # Deactivate station mode
        sta = network.WLAN(network.STA_IF)
        sta.active(False)
        
        # Create access point
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(True)
        
        # Configure AP
        self.ap.config(
            essid=self.ssid,
            password=self.password,
            channel=self.channel,
            # Security: WPA2
            authmode=network.AUTH_WPA_WPA2_PSK
        )
        
        # Wait for AP to be active
        max_wait = 10
        while not self.ap.active() and max_wait > 0:
            time.sleep(1)
            max_wait -= 1
        
        if self.ap.active():
            ip, subnet, gateway, dns = self.ap.ifconfig()
            
            print("✓ Access Point Started")
            print(f"  SSID: {self.ssid}")
            print(f"  Password: {self.password}")
            print(f"  Channel: {self.channel}")
            print(f"  IP Address: {ip}")
            print(f"  Subnet Mask: {subnet}")
            print(f"  Gateway: {gateway}")
            print()
            print("Clients can connect using:")
            print(f"  SSID: {self.ssid}")
            print(f"  Password: {self.password}")
            print()
            
            return True
        else:
            print("✗ Failed to start access point")
            return False
    
    def get_clients(self):
        """Get list of connected clients (if supported)"""
        try:
            # Note: Not all MicroPython versions support this
            if hasattr(self.ap, 'status'):
                status = self.ap.status('stations')
                return status
        except:
            pass
        return None
    
    def stop(self):
        """Stop the access point"""
        if self.ap:
            self.ap.active(False)
            print("Access point stopped")
    
    def run_with_monitoring(self):
        """Run AP with client monitoring"""
        if not self.start():
            return
        
        print("Monitoring connected clients...")
        print("Press Ctrl+C to stop\n")
        
        last_client_count = 0
        
        try:
            while True:
                clients = self.get_clients()
                
                if clients is not None:
                    client_count = len(clients)
                    
                    if client_count != last_client_count:
                        print(f"[{time.localtime()[3]:02d}:{time.localtime()[4]:02d}:{time.localtime()[5]:02d}] ", end="")
                        print(f"Connected clients: {client_count}")
                        
                        for i, client in enumerate(clients):
                            # Client is typically a MAC address tuple
                            mac = ':'.join(f'{b:02x}' for b in client)
                            print(f"  {i+1}. {mac}")
                        
                        last_client_count = client_count
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\nStopping access point...")
            self.stop()


def setup_ap_only():
    """Setup AP in standalone mode"""
    ap = TDOSAccessPoint(
        ssid="TDOS_Network",
        password="tdos12345",
        channel=6
    )
    ap.run_with_monitoring()


def setup_ap_with_kernel():
    """Setup AP and run kernel node"""
    # Start access point
    ap = TDOSAccessPoint()
    if not ap.start():
        return
    
    # Small delay to let AP stabilize
    time.sleep(2)
    
    # Import and run kernel
    import tinyos
    tinyos.init(ssid="TDOS_Network", password="tdos12345")
    
    display = tinyos.open_display()
    
    print("\nKernel running with AP...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            services = tinyos.list_services()
            message = f"AP Running\n{len(services)} services"
            tinyos.write(display, message)
            
            print(f"Services: {len(services)}")
            for name in services:
                print(f"  - {name}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        tinyos.shutdown()
        ap.stop()


def setup_ap_with_sensor():
    """Setup AP and run sensor node"""
    # Start access point
    ap = TDOSAccessPoint()
    if not ap.start():
        return
    
    # Small delay to let AP stabilize
    time.sleep(2)
    
    # Import and run sensor
    from sensor_node import create_temp_sensor
    
    sensor = create_temp_sensor()
    
    print("\nSensor running with AP...")
    print("Other nodes should connect to this AP\n")
    
    try:
        sensor.run(ssid="TDOS_Network", password="tdos12345")
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        sensor.cleanup()
        ap.stop()


# Configuration helper
def print_config_instructions():
    """Print configuration instructions for other nodes"""
    print("\n" + "="*60)
    print("CONFIGURATION FOR OTHER NODES")
    print("="*60)
    print()
    print("Add this to your sensor_node.py or application:")
    print()
    print("  WIFI_SSID = 'TDOS_Network'")
    print("  WIFI_PASSWORD = 'tdos12345'")
    print()
    print("Or when running:")
    print()
    print("  sensor.run(ssid='TDOS_Network', password='tdos12345')")
    print()
    print("="*60)
    print()


if __name__ == "__main__":
    # Choose your mode:
    
    # Mode 1: Access Point only (no other services)
    setup_ap_only()
    
    # Mode 2: Access Point + Kernel Node
    # setup_ap_with_kernel()
    
    # Mode 3: Access Point + Sensor Node
    # setup_ap_with_sensor()
    
    # Helper: Print config instructions
    # print_config_instructions()
