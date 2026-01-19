# token_service.py - Device A (Token Generator with Access Point)
# This device creates a WiFi Access Point and generates TOTP tokens

import network
import socket
import time
import machine
from pimoroni import RGBLED
import picographics

# Display setup
display = picographics.PicoGraphics(display=picographics.DISPLAY_PICO_DISPLAY_2)
display.set_backlight(0.8)
WIDTH, HEIGHT = display.get_bounds()

# Button setup
button_a = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
button_b = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
button_x = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
button_y = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

# LED setup
led = RGBLED(6, 7, 8)

# Configuration Constants
TOTP_SECRET = b"JBSWY3DPEHPK3PXP"
TOTP_INTERVAL = 30
CORRECT_PIN = "1234"  # A=1, B=2, X=3, Y=4
DEBOUNCE_MS = 300
PIN_TIMEOUT_SECONDS = 120  # Auto-lock after 2 minutes
AP_SSID = "2FA_Token_Service"
AP_PASSWORD = "SecureToken2024"
HTTP_PORT = 8080

# State variables
current_pin = ""
pin_locked = False
pin_unlock_time = 0
last_button_time = 0

def start_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    
    try:
        ap.config(essid=AP_SSID, password=AP_PASSWORD)
    except Exception as e:
        print(f"AP config error: {e}")
        raise
    
    display.set_pen(0)
    display.clear()
    display.set_pen(15)
    display.text("Starting AP..", 10, 50, scale=2)
    display.update()
    
    max_wait = 10
    while max_wait > 0:
        if ap.active():
            break
        max_wait -= 1
        led.set_rgb(50, 50, 0)
        time.sleep(0.5)
        led.set_rgb(0, 0, 0)
        time.sleep(0.5)
    
    if not ap.active():
        led.set_rgb(255, 0, 0)
        display.set_pen(0)
        display.clear()
        display.set_pen(15)
        display.text("AP Failed!", 10, 50, scale=2)
        display.text("Check config", 10, 80, scale=1)
        display.update()
        raise RuntimeError('Access Point failed to start')
    else:
        led.set_rgb(0, 255, 0)
        time.sleep(1)
        led.set_rgb(0, 0, 0)
        status = ap.ifconfig()
        print('AP Started Successfully')
        print('SSID:', AP_SSID)
        print('Password:', AP_PASSWORD)
        print('IP:', status[0])
        return status[0]

def base32_decode(s):
    """Base32 decoder for TOTP secret"""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    result = []
    bits = 0
    value = 0
    
    for char in s.decode('ascii'):
        if char not in alphabet:
            continue
        value = (value << 5) | alphabet.index(char)
        bits += 5
        
        if bits >= 8:
            result.append((value >> (bits - 8)) & 0xFF)
            bits -= 8
    
    return bytes(result)

def hmac_sha1(key, msg):
    import uhashlib
    
    blocksize = 64
    if len(key) > blocksize:
        key = uhashlib.sha1(key).digest()
    if len(key) < blocksize:
        key = key + bytes(blocksize - len(key))
    
    o_key_pad = bytes((x ^ 0x5C) for x in key)
    i_key_pad = bytes((x ^ 0x36) for x in key)
    
    return uhashlib.sha1(o_key_pad + uhashlib.sha1(i_key_pad + msg).digest()).digest()

def generate_totp(secret, time_step=30):
    try:
        key = base32_decode(secret)
        timestamp = int(time.time()) // time_step
        msg = timestamp.to_bytes(8, 'big')
        
        hmac = hmac_sha1(key, msg)
        offset = hmac[-1] & 0x0F
        code = int.from_bytes(hmac[offset:offset+4], 'big') & 0x7FFFFFFF
        
        return str(code % 1000000).zfill(6)
    except Exception as e:
        print(f"TOTP generation error: {e}")
        return "ERROR!"

def check_pin_timeout():
    global pin_locked, current_pin, pin_unlock_time
    
    if pin_locked and pin_unlock_time > 0:
        elapsed = time.time() - pin_unlock_time
        if elapsed > PIN_TIMEOUT_SECONDS:
            print("PIN timeout - auto-locking")
            pin_locked = False
            current_pin = ""
            pin_unlock_time = 0
            led.set_rgb(255, 165, 0)  # Orange
            time.sleep(0.3)
            led.set_rgb(0, 0, 0)

def draw_screen(ip_addr, token=None, pin_display="", message=""):
    display.set_pen(0)
    display.clear()
    display.set_pen(15)
    
    display.text("Token Service", 10, 10, scale=2)
    display.text(f"AP: {AP_SSID[:15]}", 10, 30, scale=1)
    
    if not pin_locked:
        display.text("Enter PIN:", 10, 60, scale=2)
        display.text("*" * len(pin_display), 10, 85, scale=3)
    else:
        if token and token != "ERROR!":
            display.text("TOKEN:", 10, 60, scale=2)
            display.text(token, 30, 95, scale=4)
            
            # Token validity timer
            remaining = TOTP_INTERVAL - (int(time.time()) % TOTP_INTERVAL)
            display.text(f"Valid: {remaining}s", 10, 140, scale=2)
            
            # PIN timeout indicator (NEW)
            if pin_unlock_time > 0:
                time_unlocked = int(time.time() - pin_unlock_time)
                time_remaining = PIN_TIMEOUT_SECONDS - time_unlocked
                display.set_pen(8)
                display.text(f"Lock in: {time_remaining}s", 10, 165, scale=1)
                display.set_pen(15)
        else:
            display.set_pen(12)  # Red
            display.text("TOKEN ERROR", 10, 100, scale=2)
            display.set_pen(15)
    
    if message:
        display.set_pen(10)
        display.text(message[:30], 10, 195, scale=1)
    
    display.set_pen(8)
    display.text("A=1 B=2 X=3 Y=4", 10, 210, scale=1)
    
    display.update()

def check_buttons():
    global current_pin, pin_locked, last_button_time, pin_unlock_time
    
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_button_time) < DEBOUNCE_MS:
        return
    
    button_pressed = False
    new_digit = None
    
    # Non-blocking button check
    if not button_a.value():
        new_digit = "1"
        button_pressed = True
    elif not button_b.value():
        new_digit = "2"
        button_pressed = True
    elif not button_x.value():
        new_digit = "3"
        button_pressed = True
    elif not button_y.value():
        new_digit = "4"
        button_pressed = True
    
    if button_pressed and new_digit:
        current_pin += new_digit
        last_button_time = current_time
        
        # Brief LED feedback (non-blocking)
        led.set_rgb(0, 0, 255)
        time.sleep(0.05)  # Reduced blocking time
        led.set_rgb(0, 0, 0)
    
    # Check PIN when complete
    if len(current_pin) >= len(CORRECT_PIN):
        if current_pin == CORRECT_PIN:
            pin_locked = True
            pin_unlock_time = time.time()  # Record unlock time (NEW)
            led.set_rgb(0, 255, 0)
            time.sleep(0.3)
            led.set_rgb(0, 0, 0)
            print(f"PIN unlocked at {pin_unlock_time}")
        else:
            # Wrong PIN
            led.set_rgb(255, 0, 0)
            time.sleep(0.3)
            led.set_rgb(0, 0, 0)
            current_pin = ""
            print("Incorrect PIN attempt")

def handle_request(conn):
    try:
        request = conn.recv(1024).decode()
        
        if "GET /validate" in request:
            try:
                # Extract token parameter
                token_start = request.find("token=") + 6
                token_end = request.find(" ", token_start)
                if token_end == -1:
                    token_end = request.find("&", token_start)
                if token_end == -1:
                    token_end = request.find("\r", token_start)
                if token_end == -1:
                    token_end = len(request)
                
                provided_token = request[token_start:token_end].strip()
                
                # Validate token format
                if len(provided_token) != 6 or not provided_token.isdigit():
                    response = '{"valid": false, "error": "Invalid token format"}'
                else:
                    current_token = generate_totp(TOTP_SECRET)
                    valid = (provided_token == current_token)
                    response = f'{{"valid": {str(valid).lower()}}}'
                    print(f"Token validation: {provided_token} == {current_token} -> {valid}")
                
                conn.send('HTTP/1.1 200 OK\r\n')
                conn.send('Content-Type: application/json\r\n')
                conn.send('Connection: close\r\n\r\n')
                conn.send(response)
                
            except Exception as e:
                print(f"Validation error: {e}")
                conn.send('HTTP/1.1 400 Bad Request\r\n')
                conn.send('Content-Type: application/json\r\n')
                conn.send('Connection: close\r\n\r\n')
                conn.send('{"valid": false, "error": "Processing error"}')
        
        elif "GET /health" in request:
            # Health check endpoint (NEW)
            response = '{"status": "ok", "locked": ' + str(pin_locked).lower() + '}'
            conn.send('HTTP/1.1 200 OK\r\n')
            conn.send('Content-Type: application/json\r\n')
            conn.send('Connection: close\r\n\r\n')
            conn.send(response)
        
        else:
            conn.send('HTTP/1.1 404 Not Found\r\n\r\n')
            
    except Exception as e:
        print(f"Request handling error: {e}")
        try:
            conn.send('HTTP/1.1 500 Internal Server Error\r\n\r\n')
        except:
            pass
    finally:
        try:
            conn.close()
        except:
            pass


def main():

    global current_pin, pin_locked
    
    try:
        ip = start_access_point()
    except Exception as e:
        print(f"Failed to start AP: {e}")
        while True:
            led.set_rgb(255, 0, 0)
            time.sleep(1)
            led.set_rgb(0, 0, 0)
            time.sleep(1)
    
    # Start HTTP server
    try:
        addr = socket.getaddrinfo('0.0.0.0', HTTP_PORT)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        s.setblocking(False)
        print(f'HTTP server listening on {ip}:{HTTP_PORT}')
    except Exception as e:
        print(f"Failed to start server: {e}")
        raise
    
    last_token = ""
    loop_count = 0
    
    while True:
        try:
            # Handle incoming requests
            try:
                conn, addr = s.accept()
                print('Connection from', addr)
                handle_request(conn)
            except OSError:
                pass  # No connection available
            
            # Check for button presses
            check_buttons()
            
            # Check PIN timeout (NEW)
            check_pin_timeout()
            
            # Update display
            if pin_locked:
                token = generate_totp(TOTP_SECRET)
                if token != last_token:
                    last_token = token
                    print(f"New token: {token}")
                draw_screen(ip, token=token)
            else:
                draw_screen(ip, pin_display=current_pin, message="Enter PIN to unlock")
            
            # Small delay to prevent CPU hogging
            time.sleep(0.05)
            
            # Periodic status (every 200 loops = ~10 seconds)
            loop_count += 1
            if loop_count % 200 == 0:
                print(f"Status: Locked={pin_locked}, Clients can connect to {AP_SSID}")
            
        except KeyboardInterrupt:
            print("\nShutting down..")
            break
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(1)  # Prevent rapid error loops

if __name__ == "__main__":
    main()

