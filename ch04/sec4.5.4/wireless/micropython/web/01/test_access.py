import network
import socket
import time
from machine import Pin
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

# Access Point Configuration
AP_SSID = "PicoDisplay"
AP_PASSWORD = None  # open network - simplicity

# Initialize display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

# Define colors
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 0, 255)
CYAN = display.create_pen(0, 255, 255)
YELLOW = display.create_pen(255, 255, 0)
MAGENTA = display.create_pen(255, 0, 255)

def clear_display(color=BLACK):
    display.set_pen(color)
    display.clear()
    display.update()

def draw_text(text, x=10, y=10, scale=2, color=WHITE):
    display.set_pen(color)
    display.text(text, x, y, scale=scale)
    display.update()

def display_multiline(lines, start_y=10, line_height=20, scale=2, color=WHITE):
    clear_display()
    display.set_pen(color)
    y = start_y
    for line in lines:
        if y + line_height <= HEIGHT:
            display.text(line[:20], 10, y, scale=scale)
            y += line_height
    display.update()

def create_access_point():
    """Create a simple access point"""
    # Disable any existing connections
    sta = network.WLAN(network.STA_IF)
    sta.active(False)
    
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    time.sleep(1)
    
    print("Setting up access point...")
    clear_display()
    draw_text("Starting AP", 10, 30, 2, CYAN)
    
    # Activate AP
    ap.active(True)
    time.sleep(2)
    
    # Simple configuration - just SSID, no password for reliability
    print(f"Configuring SSID: {AP_SSID}")
    ap.config(essid=AP_SSID)
    
    # Wait for activation
    timeout = 10
    while not ap.active() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        print("Waiting for AP...")
    
    if not ap.active():
        print("AP failed to start")
        clear_display()
        draw_text("AP FAILED", 10, 30, 2, RED)
        return None
    
    config = ap.ifconfig()
    ip = config[0]
    
    print(f"AP Started: {AP_SSID}")
    print(f"IP: {ip}")
    
    # Simple display
    clear_display()
    display.set_pen(GREEN)
    display.text("AP READY", 10, 10, scale=2)
    display.set_pen(WHITE)
    display.text("WiFi:", 10, 40, scale=1)
    display.text(AP_SSID, 10, 55, scale=1)
    display.text("Open Network", 10, 70, scale=1)
    display.set_pen(CYAN)
    display.text(ip, 10, 90, scale=1)
    display.update()
    
    return ip

def simple_web_page(message="Hello"):
    html = f"""<html>
<head><title>Pico Display</title></head>
<body>
<h1>Pico Display Control</h1>

<h2>Current Display: {message}</h2>

<form method="get">
<p>Enter text:</p>
<input type="text" name="text" size="30" maxlength="50">
<input type="submit" value="Update">
</form>

<p><a href="/clear">Clear Display</a></p>

<h3>Direct Commands:</h3>
<ul>
<li><a href="/display?text=Hello">Test Hello</a></li>
<li><a href="/display?text=Testing123">Test Numbers</a></li>
<li><a href="/color?text=RED&color=red">Red Text</a></li>
<li><a href="/color?text=GREEN&color=green">Green Text</a></li>
<li><a href="/color?text=BLUE&color=blue">Blue Text</a></li>
</ul>

<h3>API:</h3>
<p>GET /display?text=YourText</p>
<p>GET /color?text=YourText&color=red</p>
<p>GET /clear</p>

</body>
</html>"""
    return html

def handle_request(request):
    try:
        lines = request.split('\n')
        if lines:
            request_line = lines[0]
            parts = request_line.split(' ')
            if len(parts) >= 2:
                path = parts[1]
                params = {}
                
                if '?' in path:
                    path, query = path.split('?', 1)
                    for param in query.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            value = value.replace('+', ' ').replace('%20', ' ')
                            params[key] = value
                
                return path, params
    except:
        pass
    return '/', {}

def main():
    print("Starting Pico Display Server...")
    
    # Setup display
    clear_display()
    draw_text("Starting...", 10, 30, 2, WHITE)
    
    # Create access point
    ip = create_access_point()
    if not ip:
        print("Failed to create access point")
        return
    
    # Setup web server
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        print(f"Web server ready on {ip}:80")
    except Exception as e:
        print(f"Server setup failed: {e}")
        clear_display()
        draw_text("SERVER FAIL", 10, 30, 2, RED)
        return
    
    current_message = "Hello"
    
    # Main server loop
    while True:
        try:
            print("Waiting for connection...")
            cl, addr = s.accept()
            print(f"Connection from {addr}")
            
            request = cl.recv(1024).decode('utf-8')
            print(f"Request: {request.split()[0:2]}")  # Just show method and path
            
            path, params = handle_request(request)
            
            # Handle requests
            if path == '/clear':
                current_message = ""
                clear_display()
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += "<h1>Display Cleared</h1><a href='/'>Back</a>"
                
            elif path == '/display':
                text = params.get('text', '')
                if text:
                    current_message = text
                    clear_display()
                    if len(text) > 15:
                        lines = [text[i:i+15] for i in range(0, len(text), 15)]
                        display_multiline(lines[:4])
                    else:
                        draw_text(text, 10, 30, 2, WHITE)
                    
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += f"<h1>Updated</h1><p>{text}</p><a href='/'>Back</a>"
                
            elif path == '/color':
                text = params.get('text', 'Color')
                color_name = params.get('color', 'white')
                
                colors = {
                    'red': RED, 'green': GREEN, 'blue': BLUE,
                    'yellow': YELLOW, 'cyan': CYAN, 'magenta': MAGENTA,
                    'white': WHITE
                }
                color = colors.get(color_name, WHITE)
                
                current_message = f"{text} ({color_name})"
                clear_display()
                draw_text(text, 10, 30, 2, color)
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += f"<h1>Updated</h1><p>{text} in {color_name}</p><a href='/'>Back</a>"
                
            elif 'text' in params:
                # Handle form submission
                text = params['text']
                if text:
                    current_message = text
                    clear_display()
                    if len(text) > 15:
                        lines = [text[i:i+15] for i in range(0, len(text), 15)]
                        display_multiline(lines[:4])
                    else:
                        draw_text(text, 10, 30, 2, WHITE)
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += simple_web_page(current_message)
                
            else:
                # Main page
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += simple_web_page(current_message)
            
            cl.send(response.encode('utf-8'))
            cl.close()
            print("Response sent")
            
        except OSError as e:
            print(f"Connection error: {e}")
            try:
                cl.close()
            except:
                pass
        except Exception as e:
            print(f"Server error: {e}")
            try:
                cl.close()
            except:
                pass

if __name__ == "__main__":
    main()

