# auth_server.py - Device B (Authentication Server)
# This device connects to Device A's Access Point

import network
import socket
import time
import machine
import json
import urequests
from pimoroni import RGBLED
import picographics
import select

# Display setup
display = picographics.PicoGraphics(display=picographics.DISPLAY_PICO_DISPLAY_2)
display.set_backlight(0.8)
WIDTH, HEIGHT = display.get_bounds()

# LED setup
led = RGBLED(6, 7, 8)

# Configuration Constants
WIFI_SSID = "2FA_Token_Service"
WIFI_PASSWORD = "SecureToken2024"
TOKEN_SERVICE_IP = "192.168.4.1"
TOKEN_SERVICE_PORT = 8080
AUTH_SERVER_PORT = 9090
SESSION_TIMEOUT = 300  # 5 minutes
SESSION_CLEANUP_INTERVAL = 60  # 1 minute
MAX_SESSIONS = 50
VALIDATION_TIMEOUT = 10
MAX_VALIDATION_RETRIES = 2
SOCKET_READ_TIMEOUT = 2  # Seconds to wait for data (NEW)

# User database (should use hashed passwords in production)
USERS = {
    "alice": "password123",
    "bob": "secret456"
}

# Session storage
active_sessions = {}
session_counter = 0
message_display = "Ready"
auth_success_count = 0

def connect_wifi():
    """Connect to Device A's WiFi AP with retry logic"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"WiFi connection attempt {attempt + 1}/{max_attempts}")
            
            if wlan.isconnected():
                wlan.disconnect()
                time.sleep(1)
            
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            
            display.set_pen(0)
            display.clear()
            display.set_pen(15)
            display.text("Connecting...", 10, 50, scale=2)
            display.text(f"Try {attempt + 1}/{max_attempts}", 10, 75, scale=1)
            display.text(WIFI_SSID, 10, 95, scale=1)
            display.update()
            
            max_wait = 15
            while max_wait > 0:
                status = wlan.status()
                if status < 0 or status >= 3:
                    break
                max_wait -= 1
                led.set_rgb(50, 50, 0)
                time.sleep(0.5)
                led.set_rgb(0, 0, 0)
                time.sleep(0.5)
            
            if wlan.status() == 3:
                led.set_rgb(0, 255, 0)
                time.sleep(1)
                led.set_rgb(0, 0, 0)
                status = wlan.ifconfig()
                print(f'Connected to {WIFI_SSID}')
                print('IP:', status[0])
                return status[0]
                
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    
    # All attempts failed
    led.set_rgb(255, 0, 0)
    display.set_pen(0)
    display.clear()
    display.set_pen(15)
    display.text("WiFi Failed!", 10, 50, scale=2)
    display.text("Check Device A", 10, 80, scale=1)
    display.update()
    raise RuntimeError('WiFi connection failed after retries')

def draw_screen(ip_addr, message="", auth_count=0):
    display.set_pen(0)
    display.clear()
    display.set_pen(15)
    
    display.text("Auth Server", 10, 10, scale=2)
    display.text(ip_addr, 10, 35, scale=1)
    
    # Session stats
    display.text(f"Sessions: {len(active_sessions)}", 10, 70, scale=2)
    
    # Colour code based on activity
    if auth_count > 0:
        display.set_pen(10)  # Green
    display.text(f"Auth OK: {auth_count}", 10, 100, scale=2)
    display.set_pen(15)
    
    # Status message
    if message:
        display.set_pen(11)  # Cyan
        if len(message) <= 25:
            display.text(message, 10, 140, scale=1)
        else:
            display.text(message[:25], 10, 140, scale=1)
            display.text(message[25:50], 10, 155, scale=1)
        display.set_pen(15)
    
    # Server info
    display.set_pen(8)
    display.text(f"Port: {AUTH_SERVER_PORT}", 10, 195, scale=1)
    display.text(f"Token: {TOKEN_SERVICE_IP}", 10, 210, scale=1)
    
    display.update()

def validate_token_with_service(token, retries=MAX_VALIDATION_RETRIES):
    for attempt in range(retries):
        try:
            url = f"http://{TOKEN_SERVICE_IP}:{TOKEN_SERVICE_PORT}/validate?token={token}"
            print(f"Validating token (attempt {attempt + 1}/{retries}): {url}")
            
            response = urequests.get(url, timeout=VALIDATION_TIMEOUT)
            data = response.json()
            response.close()
            
            is_valid = data.get("valid", False)
            print(f"Validation result: {is_valid}")
            return is_valid
            
        except Exception as e:
            print(f"Token validation error (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(1)
            else:
                print("All validation attempts failed")
                return False
    
    return False

def handle_login(data):
    global session_counter, message_display
    
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return {"status": "error", "message": "Username and password required"}
    
    if username not in USERS:
        return {"status": "error", "message": "Invalid credentials"}
    
    if USERS[username] != password:
        return {"status": "error", "message": "Invalid credentials"}
    
    if len(active_sessions) >= MAX_SESSIONS:
        return {"status": "error", "message": "Server busy, try again later"}
    
    session_counter += 1
    session_id = f"sess_{session_counter}_{int(time.time())}"
    
    active_sessions[session_id] = {
        "username": username,
        "authenticated": False,
        "created": time.time(),
        "last_activity": time.time()
    }
    
    led.set_rgb(0, 0, 255)
    time.sleep(0.1)
    led.set_rgb(0, 0, 0)
    
    message_display = f"Login: {username}"
    print(f"Login successful for {username}, session: {session_id}")
    
    return {
        "status": "pending",
        "message": "Password OK. Enter token from Device A",
        "session_id": session_id
    }

def handle_verify(data):
    global message_display, auth_success_count
    
    session_id = data.get("session_id", "").strip()
    token = data.get("token", "").strip()
    
    if not session_id:
        return {"status": "error", "message": "Session ID required"}
    
    if session_id not in active_sessions:
        return {"status": "error", "message": "Invalid or expired session"}
    
    if not token or len(token) != 6 or not token.isdigit():
        return {"status": "error", "message": "Invalid token format"}
    
    active_sessions[session_id]["last_activity"] = time.time()
    
    message_display = f"Verifying token..."
    
    if validate_token_with_service(token):
        active_sessions[session_id]["authenticated"] = True
        auth_success_count += 1
        
        led.set_rgb(0, 255, 0)
        time.sleep(0.3)
        led.set_rgb(0, 0, 0)
        
        username = active_sessions[session_id]["username"]
        message_display = f"Auth OK: {username}"
        print(f"Authentication successful for {username}")
        
        return {
            "status": "success",
            "message": "Authentication successful!",
            "session_id": session_id,
            "username": username
        }
    else:
        led.set_rgb(255, 0, 0)
        time.sleep(0.3)
        led.set_rgb(0, 0, 0)
        
        message_display = "Invalid token"
        print(f"Invalid token attempt for session {session_id}")
        
        return {"status": "error", "message": "Invalid or expired token"}

def handle_status(data):
    session_id = data.get("session_id", "").strip()
    
    if not session_id:
        return {"status": "error", "message": "Session ID required"}
    
    if session_id not in active_sessions:
        return {"status": "error", "message": "Invalid or expired session"}
    
    session = active_sessions[session_id]
    session["last_activity"] = time.time()
    
    return {
        "status": "ok",
        "authenticated": session["authenticated"],
        "username": session["username"],
        "created": session["created"]
    }

def read_request_with_timeout(conn, timeout=SOCKET_READ_TIMEOUT):
    # Set socket to blocking mode temporarily
    conn.setblocking(True)
    conn.settimeout(timeout)
    
    try:
        # Read request in chunks
        request_data = b""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                request_data += chunk
                
                # Check if we have complete HTTP request (ends with \r\n\r\n)
                if b'\r\n\r\n' in request_data:
                    # For POST requests, check if we have the body
                    if b'POST' in request_data:
                        # Try to get Content-Length
                        try:
                            header_end = request_data.find(b'\r\n\r\n')
                            headers = request_data[:header_end].decode()
                            
                            content_length = 0
                            for line in headers.split('\r\n'):
                                if line.lower().startswith('content-length:'):
                                    content_length = int(line.split(':')[1].strip())
                                    break
                            
                            if content_length > 0:
                                body_start = header_end + 4
                                body_received = len(request_data) - body_start
                                
                                # Keep reading until we have the full body
                                while body_received < content_length:
                                    chunk = conn.recv(min(1024, content_length - body_received))
                                    if not chunk:
                                        break
                                    request_data += chunk
                                    body_received = len(request_data) - body_start
                        except:
                            pass  # If we can't parse content-length, return what we have
                    
                    break
                    
            except OSError as e:
                if e.args[0] == 11:  # EAGAIN
                    time.sleep(0.01)  # Small delay before retry
                    continue
                else:
                    raise
        
        return request_data.decode() if request_data else None
        
    except Exception as e:
        print(f"Read error: {e}")
        return None
    finally:
        # Restore non-blocking mode
        conn.setblocking(False)

def handle_request(conn):
    global message_display
    
    try:
        # Read request with proper timeout
        request = read_request_with_timeout(conn)
        
        if not request:
            print("Empty or invalid request")
            conn.close()
            return
        
        lines = request.split('\r\n')
        request_line = lines[0] if lines else ""
        
        print(f"Request: {request_line}")
        
        # Route requests
        if "POST /login" in request_line:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            
            if not body:
                response_data = {"status": "error", "message": "Empty request body"}
            else:
                try:
                    data = json.loads(body)
                    response_data = handle_login(data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    response_data = {"status": "error", "message": "Invalid JSON"}
            
        elif "POST /verify" in request_line:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            
            if not body:
                response_data = {"status": "error", "message": "Empty request body"}
            else:
                try:
                    data = json.loads(body)
                    response_data = handle_verify(data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    response_data = {"status": "error", "message": "Invalid JSON"}
            
        elif "POST /status" in request_line:
            body_start = request.find('\r\n\r\n') + 4
            body = request[body_start:]
            
            if not body:
                response_data = {"status": "error", "message": "Empty request body"}
            else:
                try:
                    data = json.loads(body)
                    response_data = handle_status(data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    response_data = {"status": "error", "message": "Invalid JSON"}
        
        elif "GET /health" in request_line:
            response_data = {
                "status": "ok",
                "sessions": len(active_sessions),
                "authenticated": sum(1 for s in active_sessions.values() if s["authenticated"])
            }
        
        else:
            response_data = {"status": "error", "message": "Unknown endpoint"}
        
        # Send response
        response_json = json.dumps(response_data)
        
        # Send response in blocking mode to ensure it goes through
        conn.setblocking(True)
        conn.send('HTTP/1.1 200 OK\r\n')
        conn.send('Content-Type: application/json\r\n')
        conn.send(f'Content-Length: {len(response_json)}\r\n')
        conn.send('Connection: close\r\n\r\n')
        conn.send(response_json)
        
        print(f"Response sent: {response_data.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"Request error: {e}")
        import sys
        sys.print_exception(e)
        try:
            conn.setblocking(True)
            conn.send('HTTP/1.1 500 Internal Server Error\r\n')
            conn.send('Content-Type: application/json\r\n')
            conn.send('Connection: close\r\n\r\n')
            conn.send('{"status": "error", "message": "Server error"}')
        except:
            pass
    finally:
        try:
            conn.close()
        except:
            pass

def cleanup_old_sessions():
    current_time = time.time()
    to_remove = []
    
    for session_id, session_data in active_sessions.items():
        age = current_time - session_data["created"]
        if age > SESSION_TIMEOUT:
            to_remove.append(session_id)
            print(f"Removing expired session: {session_id} (age: {int(age)}s)")
    
    for session_id in to_remove:
        del active_sessions[session_id]
    
    if to_remove:
        print(f"Cleaned up {len(to_remove)} expired sessions")


def main():
    global message_display, auth_success_count
    message_display = "Starting.."
    
    try:
        ip = connect_wifi()
    except Exception as e:
        print(f"Startup failed: {e}")
        while True:
            led.set_rgb(255, 0, 0)
            time.sleep(1)
            led.set_rgb(0, 0, 0)
            time.sleep(1)
    
    # Start HTTP server
    try:
        addr = socket.getaddrinfo('0.0.0.0', AUTH_SERVER_PORT)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(5)
        s.setblocking(False)  # Non-blocking for accept()
        
        print(f'Auth server listening on {ip}:{AUTH_SERVER_PORT}')
        print(f'Token service at {TOKEN_SERVICE_IP}:{TOKEN_SERVICE_PORT}')
        message_display = "Ready"
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        raise
    
    last_cleanup = time.time()
    loop_count = 0
    
    while True:
        try:
            # Handle connections
            try:
                conn, addr = s.accept()
                print(f'Connection from {addr}')
                handle_request(conn)
            except OSError:
                pass  # No connection
            
            # Periodic cleanup
            if time.time() - last_cleanup > SESSION_CLEANUP_INTERVAL:
                cleanup_old_sessions()
                last_cleanup = time.time()
            
            # Update display
            auth_count = sum(1 for s in active_sessions.values() if s.get("authenticated", False))
            draw_screen(ip, message_display, auth_count)
            
            time.sleep(0.05)
            
            # Periodic status
            loop_count += 1
            if loop_count % 200 == 0:
                print(f"Status: {len(active_sessions)} sessions, {auth_count} authenticated")
            
        except KeyboardInterrupt:
            print("\nShutting down..")
            break
        except Exception as e:
            print(f"Loop error: {e}")
            import sys
            sys.print_exception(e)
            led.set_rgb(255, 165, 0)
            time.sleep(0.2)
            led.set_rgb(0, 0, 0)
            time.sleep(1)

if __name__ == "__main__":
    main()
