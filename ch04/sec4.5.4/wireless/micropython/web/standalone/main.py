# main.py - Main application with integrated web server
import network
import socket
import time
from machine import Pin
import gc

class PicoWebServer:
    def __init__(self):
        self.led = Pin(25, Pin.OUT)
        self.ap = None
        self.server_socket = None
        
        # Setup access point and web server
        self.setup_access_point()
        self.setup_web_server()
    
    def setup_access_point(self):
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(True)
        self.ap.config(essid='PicoWeb', authmode=network.AUTH_OPEN)
        
        print(f"Web server access point active: {self.ap.ifconfig()}")
        
    def setup_web_server(self):
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(addr)
        self.server_socket.listen(1)
        
        print(f"HTTP server listening on {addr}")
    
    def generate_html_page(self):
        led_status = "ON" if self.led.value() else "OFF"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pico W Controller</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .button {{ 
                    background-color: #4CAF50; 
                    color: white; 
                    padding: 15px 32px; 
                    text-decoration: none; 
                    display: inline-block; 
                    font-size: 16px; 
                    margin: 4px 2px; 
                    cursor: pointer; 
                    border-radius: 4px;
                }}
                .status {{ 
                    padding: 20px; 
                    margin: 20px 0; 
                    border: 1px solid #ddd; 
                    border-radius: 4px; 
                }}
            </style>
        </head>
        <body>
            <h1>Raspberry Pi Pico W Controller</h1>
            
            <div class="status">
                <h2>Current Status</h2>
                <p><strong>LED Status:</strong> {led_status}</p>
                <p><strong>IP Address:</strong> {self.ap.ifconfig()[0]}</p>
                <p><strong>Uptime:</strong> {time.ticks_ms() // 1000} seconds</p>
            </div>
            
            <h2>Controls</h2>
            <a href="/led/on" class="button">Turn LED ON</a>
            <a href="/led/off" class="button" style="background-color: #f44336;">Turn LED OFF</a>
            
            <br><br>
            <a href="/" class="button" style="background-color: #008CBA;">Refresh</a>
            
            <hr>
            <p><em>Powered by Raspberry Pi Pico W</em></p>
        </body>
        </html>
        """
        return html
    
    def handle_request(self, client_socket):
        try:
            # Read HTTP request
            request = client_socket.recv(1024).decode('utf-8')
            
            # Parse request line
            request_line = request.split('\r\n')[0]
            method, path, _ = request_line.split(' ')
            
            print(f"HTTP {method} {path}")
            
            # Process different paths
            if path == '/':
                response_body = self.generate_html_page()
                status = "200 OK"
            elif path == '/led/on':
                self.led.value(1)
                response_body = self.generate_html_page()
                status = "200 OK"
            elif path == '/led/off':
                self.led.value(0)
                response_body = self.generate_html_page()
                status = "200 OK"
            else:
                response_body = "<h1>404 Not Found</h1><p>The requested page does not exist.</p>"
                status = "404 Not Found"
            
            # Send HTTP response
            response = f"""HTTP/1.1 {status}\r
Content-Type: text/html\r
Content-Length: {len(response_body)}\r
Connection: close\r
\r
{response_body}"""
            
            client_socket.send(response.encode('utf-8'))
            
        except Exception as e:
            print(f"Request handling error: {e}")
            # Send error response
            error_response = """HTTP/1.1 500 Internal Server Error\r
Content-Type: text/html\r
Connection: close\r
\r
<h1>500 Internal Server Error</h1>"""
            try:
                client_socket.send(error_response.encode('utf-8'))
            except:
                pass
    
    def run(self):
        self.led.value(1)  # Indicate server is running
        print("Web server is running...")
        print(f"Connect to WiFi network 'PicoWeb' and visit http://{self.ap.ifconfig()[0]}")
        
        while True:
            try:
                client_socket, client_addr = self.server_socket.accept()
                print(f"Client connected: {client_addr}")
                
                self.handle_request(client_socket)
                client_socket.close()
                
                gc.collect()  # Clean up memory
                
            except Exception as e:
                print(f"Server error: {e}")
                time.sleep(1)

# Start the web server
if __name__ == "__main__":
    server = PicoWebServer()
    server.run()
