import network
import socket
import time
import json
from machine import Pin
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

# Access Point Configuration
AP_SSID = "PicoDisplay"
AP_PASSWORD = None  # Open network for simplicity

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
ORANGE = display.create_pen(255, 165, 0)

# Global state
current_display_text = "Ready"
current_color = "white"
log_buffer = []
max_log_lines = 8
connection_count = 0
last_request_time = 0

def log(message, level="INFO"):
    global log_buffer, max_log_lines
    timestamp = time.ticks_ms() // 1000  # Simple timestamp in seconds
    log_entry = f"{timestamp:>6} {level[:4]} {message[:25]}"
    print(f"[{level}] {message}")
    
    log_buffer.append(log_entry)
    if len(log_buffer) > max_log_lines:
        log_buffer.pop(0)
    
    update_display_with_logs()

def get_color_pen(color_name):
    colors = {
        'black': BLACK, 'white': WHITE, 'red': RED, 'green': GREEN,
        'blue': BLUE, 'cyan': CYAN, 'yellow': YELLOW, 'magenta': MAGENTA,
        'orange': ORANGE
    }
    return colors.get(color_name.lower(), WHITE)

def clear_display(color=BLACK):
    display.set_pen(color)
    display.clear()
    display.update()

def update_display_with_logs():
    clear_display()
    
    # Show current display content at top
    if current_display_text:
        color_pen = get_color_pen(current_color)
        display.set_pen(color_pen)
        if len(current_display_text) > 15:
            # Multi-line for long text
            lines = [current_display_text[i:i+15] for i in range(0, len(current_display_text), 15)]
            for i, line in enumerate(lines[:2]):  # Max 2 lines for content
                display.text(line, 5, 5 + i * 15, scale=1)
        else:
            display.text(current_display_text, 5, 5, scale=2)
    
    # Show logs in bottom half
    display.set_pen(CYAN)
    display.text("--- LOGS ---", 5, HEIGHT//2, scale=1)
    
    display.set_pen(WHITE)
    start_y = HEIGHT//2 + 15
    line_height = 12
    
    for i, log_line in enumerate(log_buffer[-6:]):  # Show last 6 log lines
        y_pos = start_y + i * line_height
        if y_pos < HEIGHT - 10:
            display.text(log_line[:30], 5, y_pos, scale=1)
    
    display.update()

def create_access_point():
    log("Disabling existing connections")
    
    # Disable existing connections
    sta = network.WLAN(network.STA_IF)
    sta.active(False)
    
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    time.sleep(1)
    
    log("Activating AP interface")
    ap.active(True)
    time.sleep(2)
    
    log(f"Configuring SSID: {AP_SSID}")
    ap.config(essid=AP_SSID)
    
    # Wait for activation with timeout
    timeout = 10
    while not ap.active() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        log(f"AP starting... {timeout}s")
    
    if not ap.active():
        log("AP activation FAILED", "ERROR")
        return None
    
    config = ap.ifconfig()
    ip = config[0]
    
    log(f"AP Ready: {ip}", "SUCCESS")
    return ip

def parse_json_body(request_data):
    try:
        # Find the JSON body after headers
        if '\r\n\r\n' in request_data:
            body = request_data.split('\r\n\r\n', 1)[1]
            if body.strip():
                return json.loads(body)
    except Exception as e:
        log(f"JSON parse error: {e}", "ERROR")
    return {}

def create_response(status_code, data=None, message=None):
    response_data = {
        "status": status_code,
        "timestamp": time.ticks_ms(),
        "connection_count": connection_count
    }
    
    if data is not None:
        response_data["data"] = data
    if message:
        response_data["message"] = message
    
    json_response = json.dumps(response_data)
    
    status_text = {
        200: "OK", 201: "Created", 400: "Bad Request", 
        404: "Not Found", 405: "Method Not Allowed", 500: "Internal Server Error"
    }.get(status_code, "Unknown")
    
    headers = f"HTTP/1.1 {status_code} {status_text}\r\n"
    headers += "Content-Type: application/json\r\n"
    headers += "Access-Control-Allow-Origin: *\r\n"
    headers += f"Content-Length: {len(json_response)}\r\n"
    headers += "Connection: close\r\n\r\n"
    
    return headers + json_response

def handle_rest_request(method, path, params, json_body):
    global current_display_text, current_color
    
    # GET /api/display - Get current display state
    if method == "GET" and path == "/api/display":
        return create_response(200, {
            "text": current_display_text,
            "color": current_color,
            "logs": log_buffer[-5:]  # Last 5 log entries
        })
    
    # POST /api/display - Set display text
    elif method == "POST" and path == "/api/display":
        text = json_body.get("text", params.get("text", ""))
        color = json_body.get("color", params.get("color", current_color))
        
        if not text:
            return create_response(400, message="Text parameter required")
        
        current_display_text = text[:50]  # Limit length
        current_color = color
        
        log(f"Display set: '{text[:15]}'")
        update_display_with_logs()
        
        return create_response(200, {
            "text": current_display_text,
            "color": current_color
        }, "Display updated")
    
    # PUT /api/display/color - Update only color
    elif method == "PUT" and path == "/api/display/color":
        color = json_body.get("color", params.get("color"))
        
        if not color:
            return create_response(400, message="Color parameter required")
        
        current_color = color
        log(f"Color changed: {color}")
        update_display_with_logs()
        
        return create_response(200, {
            "text": current_display_text,
            "color": current_color
        }, "Color updated")
    
    # DELETE /api/display - Clear display
    elif method == "DELETE" and path == "/api/display":
        current_display_text = ""
        current_color = "white"
        
        log("Display cleared")
        update_display_with_logs()
        
        return create_response(200, message="Display cleared")
    
    # GET /api/status - System status
    elif method == "GET" and path == "/api/status":
        return create_response(200, {
            "uptime": time.ticks_ms(),
            "memory": "N/A",  # Could add gc.mem_free() if gc available
            "connections": connection_count,
            "ap_ssid": AP_SSID
        })
    
    # GET /api/logs - Get recent logs
    elif method == "GET" and path == "/api/logs":
        return create_response(200, {
            "logs": log_buffer,
            "count": len(log_buffer)
        })
    
    # Simple web interface for testing
    elif method == "GET" and path == "/":
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pico Display REST API</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .api-section {{ margin: 20px 0; padding: 10px; border: 1px solid #ccc; }}
        button {{ padding: 8px 15px; margin: 5px; }}
        input {{ padding: 5px; margin: 5px; }}
        pre {{ background: #f0f0f0; padding: 10px; }}
    </style>
</head>
<body>
    <h1>Pico Display REST API</h1>
    
    <div class="api-section">
        <h3>Quick Test</h3>
        <input type="text" id="testText" value="Hello REST!" placeholder="Enter text">
        <select id="testColor">
            <option value="white">White</option>
            <option value="red">Red</option>
            <option value="green">Green</option>
            <option value="blue">Blue</option>
            <option value="yellow">Yellow</option>
        </select>
        <button onclick="updateDisplay()">Update Display</button>
        <button onclick="clearDisplay()">Clear Display</button>
    </div>
    
    <div class="api-section">
        <h3>REST Endpoints</h3>
        <pre>
GET    /api/display      - Get current display state
POST   /api/display      - Set display text and color
PUT    /api/display/color- Update color only  
DELETE /api/display      - Clear display
GET    /api/status       - Get system status
GET    /api/logs         - Get recent logs
        </pre>
    </div>
    
    <script>
        function updateDisplay() {{
            const text = document.getElementById('testText').value;
            const color = document.getElementById('testColor').value;
            
            fetch('/api/display', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{text: text, color: color}})
            }})
            .then(r => r.json())
            .then(data => alert('Updated: ' + JSON.stringify(data)))
            .catch(e => alert('Error: ' + e));
        }}
        
        function clearDisplay() {{
            fetch('/api/display', {{method: 'DELETE'}})
            .then(r => r.json())
            .then(data => alert('Cleared: ' + JSON.stringify(data)))
            .catch(e => alert('Error: ' + e));
        }}
    </script>
</body>
</html>"""
        
        headers = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
        headers += f"Content-Length: {len(html)}\r\n\r\n"
        return headers + html
    
    # Unknown endpoint
    else:
        return create_response(404, message=f"Endpoint not found: {method} {path}")

def parse_request(request_data):
    lines = request_data.split('\n')
    if not lines:
        return None, None, {}, {}
    
    # Parse request line
    request_line = lines[0].strip()
    parts = request_line.split(' ')
    
    if len(parts) < 2:
        return None, None, {}, {}
    
    method = parts[0]
    full_path = parts[1]
    
    # Parse path and query parameters
    if '?' in full_path:
        path, query_string = full_path.split('?', 1)
        params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value.replace('%20', ' ').replace('+', ' ')
    else:
        path = full_path
        params = {}
    
    # Parse JSON body for POST/PUT requests
    json_body = {}
    if method in ['POST', 'PUT']:
        json_body = parse_json_body(request_data)
    
    return method, path, params, json_body

def main():
    global connection_count, last_request_time
    
    log("Starting Pico Display REST Server")
    
    # Setup display
    current_display_text = "Starting..."
    update_display_with_logs()
    
    # Create access point
    ip = create_access_point()
    if not ip:
        log("Failed to create AP - ABORT", "ERROR")
        return
    
    # Setup web server
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(3)  # Allow up to 3 pending connections
        log(f"Server listening on {ip}:80")
    except Exception as e:
        log(f"Server setup failed: {e}", "ERROR")
        return
    
    current_display_text = "REST API Ready"
    update_display_with_logs()
    
    # Main server loop
    while True:
        client_socket = None
        try:
            log("Waiting for connection...")
            client_socket, client_addr = s.accept()
            connection_count += 1
            last_request_time = time.ticks_ms()
            
            log(f"Connection #{connection_count} from {client_addr[0]}")
            
            # Set socket timeout
            client_socket.settimeout(10.0)
            
            # Receive request
            request_data = client_socket.recv(2048).decode('utf-8')
            
            if not request_data:
                log("Empty request received", "WARN")
                continue
            
            # Parse request
            method, path, params, json_body = parse_request(request_data)
            
            if method and path:
                log(f"{method} {path[:20]}")
                
                # Handle the request
                response = handle_rest_request(method, path, params, json_body)
                
                # Send response
                client_socket.send(response.encode('utf-8'))
                log("Response sent OK")
                
            else:
                log("Invalid request format", "WARN")
                error_response = create_response(400, message="Invalid request")
                client_socket.send(error_response.encode('utf-8'))
            
        except OSError as e:
            error_code = e.args[0] if e.args else 0
            if error_code == 104:  # Connection reset by peer
                log("Client disconnected", "WARN")
            elif error_code == 110:  # Connection timeout
                log("Connection timeout", "WARN")
            else:
                log(f"Connection error: {error_code}", "ERROR")
                
        except Exception as e:
            log(f"Server error: {str(e)[:20]}", "ERROR")
            
        finally:
            # Always close the client socket
            if client_socket:
                try:
                    client_socket.close()
                    log("Connection closed")
                except:
                    pass

if __name__ == "__main__":
    main()
