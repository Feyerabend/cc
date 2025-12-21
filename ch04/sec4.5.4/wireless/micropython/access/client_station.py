# client_station.py
import network
import socket
import time
from machine import Pin

# Raspberry Pi Pico W WiFi Client Station
class PicoWiFiClient:    
    def __init__(self, ssid, password=None, server_ip="192.168.4.1", server_port=12345):
        self.ssid = ssid
        self.password = password
        self.server_ip = server_ip
        self.server_port = server_port
        self.led = Pin(25, Pin.OUT)
        
        # Init WiFi interface
        self.wlan = network.WLAN(network.STA_IF)
        self.socket = None
        
        # Connect to network
        self.connect_to_network()
    
    def connect_to_network(self):
        self.wlan.active(True)
        
        print(f"Connecting to '{self.ssid}'..")
        
        if self.password:
            self.wlan.connect(self.ssid, self.password)
        else:
            self.wlan.connect(self.ssid)
        
        # Wait for connection with timeout
        max_wait = 20
        while max_wait > 0:
            if self.wlan.isconnected():
                break
            print(".", end="")
            time.sleep(1)
            max_wait -= 1
        
        if self.wlan.isconnected():
            print(f"\nConnected successfully!")
            print(f"Network configuration: {self.wlan.ifconfig()}")
            self.led.value(1)  # Indicate successful connection
        else:
            print(f"\nFailed to connect to '{self.ssid}'")
            raise RuntimeError("WiFi connection failed")
    
    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            
            print(f"Connecting to server at {self.server_ip}:{self.server_port}")
            self.socket.connect((self.server_ip, self.server_port))
            
            # Receive welcome message
            welcome = self.socket.recv(1024).decode('utf-8')
            print(f"Server says: {welcome}")
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def send_command(self, command):
        if not self.socket:
            print("No server connection available")
            return None
        
        try:
            # Send command
            self.socket.send(f"{command}\n".encode('utf-8'))
            print(f"Sent: {command}")
            
            # Receive response
            response = self.socket.recv(1024).decode('utf-8')
            print(f"Server response: {response.strip()}")
            
            return response
            
        except Exception as e:
            print(f"Communication error: {e}")
            return None
    
    def interactive_mode(self):
        if not self.connect_to_server():
            return
        
        print("\nInteractive mode - enter commands (type 'help' for options)")
        
        try:
            while True:
                command = input("\nCommand: ").strip()
                
                if command.lower() == 'help':
                    print("Available commands:")
                    print("  LED ON    - Turn on server LED")
                    print("  LED OFF   - Turn off server LED") 
                    print("  STATUS    - Get server status")
                    print("  QUIT      - Disconnect from server")
                    print("  EXIT      - Exit client program")
                    continue
                
                if command.lower() == 'exit':
                    break
                
                if command == '':
                    continue
                
                response = self.send_command(command)
                
                if command.upper() == "QUIT":
                    break
                    
        except KeyboardInterrupt:
            print("\nInteractive mode interrupted")
        finally:
            self.cleanup()
    
    def automated_demo(self):
        if not self.connect_to_server():
            return
        
        print("\nStarting automated demo..")
        
        demo_commands = [
            ("STATUS", 2),
            ("LED ON", 3),
            ("LED OFF", 3),
            ("LED ON", 2),
            ("STATUS", 2),
            ("LED OFF", 1),
            ("QUIT", 1)
        ]
        
        try:
            for command, delay in demo_commands:
                self.send_command(command)
                time.sleep(delay)
                
                if command == "QUIT":
                    break
                    
        except Exception as e:
            print(f"Demo error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.led.value(0)
        print("Client cleanup completed")


if __name__ == "__main__":

    # Connect to open network
    client = PicoWiFiClient(ssid="PICO_DEMO_AP")
    
    # Choose operation mode
    mode = input("Select mode (1=Interactive, 2=Automated demo): ").strip()
    
    if mode == "1":
        client.interactive_mode()
    else:
        client.automated_demo()
