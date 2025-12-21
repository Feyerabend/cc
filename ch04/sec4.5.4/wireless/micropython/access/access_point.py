# access_point.py
import network
import socket
import time
from machine import Pin, reset
import gc

# Define the Access Point and TCP server class
class PicoAccessPoint:    
    def __init__(self, ssid="PICO_AP", password=None, port=12345):
        self.ssid = ssid
        self.password = password
        self.port = port
        self.led = Pin(25, Pin.OUT)  # Onboard LED for status
        self.clients = []  # Track connected clients
        
        # Init access point
        self.ap = network.WLAN(network.AP_IF)
        self.setup_access_point()
        
        # Init TCP server
        self.server_socket = None
        self.setup_tcp_server()
    
    def setup_access_point(self):
        self.ap.active(True)
        
        # Config network parameters
        if self.password:
            # Secure network with WPA2
            self.ap.config(essid=self.ssid, password=self.password, authmode=network.AUTH_WPA2_PSK)
            print(f"Secure AP '{self.ssid}' created with password protection")
        else:
            # Open network for testing
            self.ap.config(essid=self.ssid, authmode=network.AUTH_OPEN)
            print(f"Open AP '{self.ssid}' created (no password required)")
        
        # Wait for interface to become active
        max_wait = 10
        while max_wait > 0:
            if self.ap.active():
                break
            time.sleep(1)
            max_wait -= 1
        
        if self.ap.active():
            print(f"Access Point active: {self.ap.ifconfig()}")
            self.led.value(1)  # Turn on LED to indicate AP is active
        else:
            print("Failed to activate Access Point")
            raise RuntimeError("AP activation failed")
    
    def setup_tcp_server(self):
        try:
            # Create and bind socket
            addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(addr)
            self.server_socket.listen(5)  # Allow up to 5 pending connections
            
            print(f"TCP server listening on {addr}")
        except Exception as e:
            print(f"Failed to setup TCP server: {e}")
            raise
    
    def handle_client_connection(self, client_socket, client_addr):
        print(f"Client connected from {client_addr}")
        client_socket.settimeout(30.0)  # 30 second timeout
        
        try:
            # Send welcome message
            welcome_msg = f"Welcome to {self.ssid} server!\nSupported commands: LED ON, LED OFF, STATUS, QUIT\n"
            client_socket.send(welcome_msg.encode('utf-8'))
            
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # Process received command
                command = data.decode('utf-8').strip().upper()
                print(f"Received command: {command}")
                
                response = self.process_command(command)
                client_socket.send(response.encode('utf-8'))
                
                # Handle quit command
                if command == "QUIT":
                    break
                    
        except socket.timeout:
            print(f"Client {client_addr} timed out")
        except Exception as e:
            print(f"Error handling client {client_addr}: {e}")
        finally:
            client_socket.close()
            print(f"Client {client_addr} disconnected")
    
    def process_command(self, command):
        if command == "LED ON":
            self.led.value(1)
            return "LED turned ON\n"
        elif command == "LED OFF":
            self.led.value(0)
            return "LED turned OFF\n"
        elif command == "STATUS":
            led_status = "ON" if self.led.value() else "OFF"
            ap_info = self.ap.ifconfig()
            return f"Status: LED={led_status}, IP={ap_info[0]}, Clients={self.ap.status('stations')}\n"
        elif command == "QUIT":
            return "Goodbye!\n"
        else:
            return f"Unknown command: {command}\nSupported: LED ON, LED OFF, STATUS, QUIT\n"
    
    def run(self):
        print(f"Server running on {self.ssid}")
        print("Waiting for client connections..")
        
        try:
            while True:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    self.handle_client_connection(client_socket, client_addr)
                    gc.collect()  # Clean up memory after each client
                except KeyboardInterrupt:
                    print("Server shutdown requested")
                    break
                except Exception as e:
                    print(f"Server error: {e}")
                    time.sleep(1)
        finally:
            self.cleanup()
    
    def cleanup(self):
        if self.server_socket:
            self.server_socket.close()
        self.ap.active(False)
        self.led.value(0)
        print("Server cleanup completed")


if __name__ == "__main__":
    # Create secure access point (uncomment next line for password protection)
    # server = PicoAccessPoint(ssid="PICO_SECURE_AP", password="pico12345")
    
    # Create open access point for testing
    server = PicoAccessPoint(ssid="PICO_DEMO_AP")
    server.run()
