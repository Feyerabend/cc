"""
Dogfight Game Client for Raspberry Pi Pico 2 W
- Robust connection with retry mechanism
- Manual reconnect button (X button)
- Better state synchronization
- Connection timeout handling
- Enhanced debugging
"""

import network
import socket
import time
import _thread
from machine import Pin
from pimoroni import Button, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
import protocol

# WiFi Configuration
SSID = "DOGFIGHT_SERVER"
PASSWORD = "dogfight123"
SERVER_IP = "192.168.4.1"
UDP_PORT = 8888

# Connection parameters
CONNECT_TIMEOUT = 3000  # 3 seconds to get player ID
CONNECT_RETRIES = 5
STATE_TIMEOUT = 2000  # 2 seconds without state = reconnect

# Display setup
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

# Colors
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 100, 255)
CYAN = display.create_pen(0, 200, 200)
ORANGE = display.create_pen(255, 128, 0)
YELLOW = display.create_pen(255, 255, 0)

# Buttons
button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# LED
led = RGBLED(6, 7, 8)

# Display constants
PIXEL_SIZE = 2
SCREEN_WIDTH = protocol.GAME_WIDTH * PIXEL_SIZE
SCREEN_HEIGHT = protocol.GAME_HEIGHT * PIXEL_SIZE

# Plane sprite data
PLANE0_SHAPES = [
    [0,0,0,1,0,0,0,0, 0,0,0,1,0,0,0,0, 0,0,0,1,0,0,0,0, 0,0,1,1,1,0,0,0,
     0,1,1,1,1,1,0,0, 1,1,1,1,1,1,1,0, 1,1,1,1,1,1,1,0, 0,0,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0, 1,1,0,0,0,0,0,1, 1,1,1,1,1,1,1,0, 0,1,1,1,1,1,0,0,
     0,1,1,1,1,0,0,0, 0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0],
    [0,1,1,0,0,0,0,0, 0,1,1,1,0,0,0,0, 0,1,1,1,1,0,0,0, 1,1,1,1,1,1,1,1,
     0,1,1,1,1,0,0,0, 0,1,1,1,0,0,0,0, 0,1,1,0,0,0,0,0, 0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0, 0,1,1,1,1,0,0,0,
     0,1,1,1,1,1,0,0, 1,1,1,1,1,1,1,0, 1,1,0,0,0,0,0,1, 0,0,0,0,0,0,0,0],
    [0,0,0,1,0,0,0,0, 1,1,1,1,1,1,1,0, 1,1,1,1,1,1,1,0, 0,1,1,1,1,1,0,0,
     0,0,1,1,1,0,0,0, 0,0,0,1,0,0,0,0, 0,0,0,1,0,0,0,0, 0,0,0,0,0,0,0,0],
    [0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0, 0,0,0,1,1,1,1,0,
     0,0,1,1,1,1,1,0, 0,1,1,1,1,1,1,1, 1,0,0,0,0,0,1,1, 0,0,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,0, 0,0,0,0,1,1,1,0, 0,0,0,1,1,1,1,0, 1,1,1,1,1,1,1,1,
     0,0,0,1,1,1,1,0, 0,0,0,0,1,1,1,0, 0,0,0,0,0,1,1,0, 0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0, 1,0,0,0,0,0,1,1, 0,1,1,1,1,1,1,1, 0,0,1,1,1,1,1,0,
     0,0,0,1,1,1,1,0, 0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0],
]

PLANE1_SHAPES = [
    [0,0,0,1,0,0,0,0, 0,0,1,1,1,0,0,0, 0,0,0,1,0,0,0,0, 0,0,1,1,1,0,0,0,
     0,1,1,1,1,1,0,0, 1,1,1,1,1,1,1,0, 1,1,1,1,1,1,1,0, 0,0,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0, 1,1,0,0,0,1,0,1, 1,1,1,1,1,1,1,0, 0,1,1,1,1,1,0,1,
     0,1,1,1,1,0,0,0, 0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0],
    [0,1,1,0,0,0,0,0, 0,1,1,1,0,0,0,0, 0,1,1,1,1,0,1,0, 1,1,1,1,1,1,1,1,
     0,1,1,1,1,0,1,0, 0,1,1,1,0,0,0,0, 0,1,1,0,0,0,0,0, 0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0, 0,0,1,1,0,0,0,0, 0,1,1,1,1,0,0,0,
     0,1,1,1,1,1,0,1, 1,1,1,1,1,1,1,0, 1,1,0,0,0,1,0,1, 0,0,0,0,0,0,0,0],
    [0,0,0,1,0,0,0,0, 1,1,1,1,1,1,1,0, 1,1,1,1,1,1,1,0, 0,1,1,1,1,1,0,0,
     0,0,1,1,1,0,0,0, 0,0,0,1,0,0,0,0, 0,0,1,1,1,0,0,0, 0,0,0,1,0,0,0,0],
    [0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0, 0,0,0,1,1,1,1,0,
     1,0,1,1,1,1,1,0, 0,1,1,1,1,1,1,1, 1,0,1,0,0,0,1,1, 0,0,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,0, 0,0,0,0,1,1,1,0, 0,1,0,1,1,1,1,0, 1,1,1,1,1,1,1,1,
     0,1,0,1,1,1,1,0, 0,0,0,0,1,1,1,0, 0,0,0,0,0,1,1,0, 0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0, 1,0,1,0,0,0,1,1, 0,1,1,1,1,1,1,1, 1,0,1,1,1,1,1,0,
     0,0,0,1,1,1,1,0, 0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0, 0,0,0,0,1,1,0,0],
]

# Shared state between cores
class SharedState:
    def __init__(self):
        self.lock = _thread.allocate_lock()
        
        # Network state
        self.connected = False
        self.player_id = 0
        self.reconnect_request = False
        
        # Game state
        self.p1_x = 0
        self.p1_y = 0
        self.p1_dir = 0
        self.p1_alive = True
        
        self.p2_x = 0
        self.p2_y = 0
        self.p2_dir = 0
        self.p2_alive = True
        
        self.shots = []
        self.prev_shot_count = 0  # Track shot count for LED flash
        
        self.game_over = False
        self.winner = 0
        self.last_seq = 0
        self.last_state_time = 0
        
        # Input state
        self.btn_a = False
        self.btn_b = False
        self.btn_x = False
        self.btn_y = False
    
    def update_game_state(self, state):
        with self.lock:
            self.last_state_time = time.ticks_ms()
            
            if 'seq' in state:
                self.last_seq = state['seq']
            
            # Detect game reset (game_over goes from True to False)
            was_game_over = self.game_over
            if 'game_over' in state:
                self.game_over = state['game_over']
                if 'winner' in state:
                    self.winner = state['winner']
                
                # If game was over and now it's not, clear everything
                if was_game_over and not self.game_over:
                    print("Game reset detected - clearing state")
                    self.shots = []
            
            if 'p1' in state:
                if 'x' in state['p1']:
                    self.p1_x = state['p1']['x']
                if 'y' in state['p1']:
                    self.p1_y = state['p1']['y']
                if 'dir' in state['p1']:
                    self.p1_dir = state['p1']['dir']
                if 'alive' in state['p1']:
                    self.p1_alive = state['p1']['alive']
            
            if 'p2' in state:
                if 'x' in state['p2']:
                    self.p2_x = state['p2']['x']
                if 'y' in state['p2']:
                    self.p2_y = state['p2']['y']
                if 'dir' in state['p2']:
                    self.p2_dir = state['p2']['dir']
                if 'alive' in state['p2']:
                    self.p2_alive = state['p2']['alive']
            
            if 'shots' in state:
                self.shots = state['shots']
            
            if 'shots_added' in state:
                self.shots.extend(state['shots_added'])
            
            # Track my own shot count for LED feedback
            my_shots = [s for s in self.shots if s.get('owner') == self.player_id]
            self.prev_shot_count = len(my_shots)
            
            if 'shots_removed' in state:
                for rem_x, rem_y in state['shots_removed']:
                    self.shots = [s for s in self.shots 
                                 if not (abs(s['x'] - rem_x) < 3 and abs(s['y'] - rem_y) < 3)]
            
            # Moved game_over handling to top of function

    def get_display_state(self):
        with self.lock:
            return {
                'p1': {'x': self.p1_x, 'y': self.p1_y, 'dir': self.p1_dir, 'alive': self.p1_alive},
                'p2': {'x': self.p2_x, 'y': self.p2_y, 'dir': self.p2_dir, 'alive': self.p2_alive},
                'shots': list(self.shots),
                'game_over': self.game_over,
                'winner': self.winner,
                'player_id': self.player_id,
                'connected': self.connected,
                'last_state_time': self.last_state_time,
                'my_shot_count': len([s for s in self.shots if s.get('owner') == self.player_id])
            }
    
    def set_input(self, a, b, x, y):
        with self.lock:
            self.btn_a = a
            self.btn_b = b
            self.btn_x = x
            self.btn_y = y
    
    def get_input(self):
        with self.lock:
            return (self.btn_a, self.btn_b, self.btn_x, self.btn_y)
    
    def set_connected(self, connected, player_id=0):
        with self.lock:
            self.connected = connected
            if connected:
                self.player_id = player_id
                self.last_state_time = time.ticks_ms()
    
    def request_reconnect(self):
        with self.lock:
            self.reconnect_request = True
    
    def check_reconnect_request(self):
        with self.lock:
            req = self.reconnect_request
            self.reconnect_request = False
            return req
    
    def is_state_stale(self):
        with self.lock:
            if not self.connected:
                return False
            return time.ticks_diff(time.ticks_ms(), self.last_state_time) > STATE_TIMEOUT

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        print("Already connected")
        return wlan
    
    print(f"Connecting to {SSID}...")
    wlan.connect(SSID, PASSWORD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print(f"Waiting for WiFi.. {max_wait}")
        time.sleep(1)
    
    if wlan.status() != 3:
        raise RuntimeError("WiFi connection failed")
    
    print(f"WiFi Connected: {wlan.ifconfig()}")
    return wlan

def request_player_id(sock, server_addr):
    """Request player ID from server with retries"""
    connect_packet = protocol.ConnectPacket.pack_request()
    
    for attempt in range(CONNECT_RETRIES):
        print(f"Requesting player ID (attempt {attempt + 1}/{CONNECT_RETRIES})")
        
        try:
            sock.sendto(connect_packet, server_addr)
            print(f"Sent connect request to {server_addr}")
        except Exception as e:
            print(f"Send error: {e}")
            continue
        
        deadline = time.ticks_add(time.ticks_ms(), CONNECT_TIMEOUT)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            try:
                sock.settimeout(0.1)
                data, addr = sock.recvfrom(256)
                print(f"Received {len(data)} bytes from {addr}, type={data[0] if len(data) > 0 else 'empty'}")
                
                if len(data) > 0 and data[0] == protocol.PKT_CLIENT_ACK:
                    ack = protocol.ConnectPacket.unpack(data)
                    player_id = ack['player_id']
                    if player_id in [1, 2]:
                        print(f"Assigned Player {player_id}")
                        return player_id
                    else:
                        print(f"Invalid player_id received: {player_id}")
            except OSError as e:
                # Timeout - this is normal
                pass
            except Exception as e:
                print(f"Receive error: {e}")
            
            time.sleep_ms(100)
        
        print(f"Attempt {attempt + 1} timed out")
        time.sleep(0.5)
    
    print("Failed to get player ID after all retries")
    return None

def network_thread(shared_state):
    print("Network thread starting...")
    
    server_addr = (SERVER_IP, UDP_PORT)
    sock = None
    wlan = None
    
    while True:
        try:
            if shared_state.check_reconnect_request():
                print("Reconnect requested")
                shared_state.set_connected(False)
                if sock:
                    sock.close()
                    sock = None
            
            if not wlan or not wlan.isconnected():
                print("Connecting to WiFi...")
                wlan = connect_wifi()
            
            if not sock:
                print("Creating UDP socket...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(False)
                print("Socket created")
            
            if not shared_state.connected:
                player_id = request_player_id(sock, server_addr)
                if player_id:
                    shared_state.set_connected(True, player_id)
                else:
                    print("Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
            
            while shared_state.connected:
                if shared_state.is_state_stale():
                    print("State timeout - reconnecting")
                    shared_state.set_connected(False)
                    break
                
                if shared_state.check_reconnect_request():
                    print("Manual reconnect")
                    shared_state.set_connected(False)
                    break
                
                btn_a, btn_b, btn_x, btn_y = shared_state.get_input()
                input_packet = protocol.ClientInputPacket.pack(
                    shared_state.player_id, btn_a, btn_b, btn_x, btn_y
                )
                sock.sendto(input_packet, server_addr)
                
                for _ in range(5):
                    try:
                        sock.settimeout(0.01)
                        data, addr = sock.recvfrom(512)
                        if len(data) > 0:
                            pkt_type = data[0]
                            
                            if pkt_type == protocol.PKT_FULL_STATE:
                                state = protocol.FullStatePacket.unpack(data)
                                if state:
                                    shared_state.update_game_state(state)
                            
                            elif pkt_type == protocol.PKT_DELTA_STATE:
                                delta = protocol.DeltaStatePacket.unpack(data)
                                if delta:
                                    shared_state.update_game_state(delta)
                    
                    except OSError:
                        break
                    except Exception as e:
                        print(f"Receive error: {e}")
                
                time.sleep_ms(20)  # Send inputs at 50Hz
        
        except Exception as e:
            print(f"Network error: {e}")
            shared_state.set_connected(False)
            if sock:
                sock.close()
                sock = None
            time.sleep(2)

def draw_plane(x, y, dir, plane_type, color):
    shapes = PLANE1_SHAPES if plane_type == 1 else PLANE0_SHAPES
    shape = shapes[dir]
    
    for dy in range(8):
        for dx in range(8):
            if shape[dy * 8 + dx]:
                px = (x + dx - 4) * PIXEL_SIZE
                py = (y + dy - 4) * PIXEL_SIZE
                if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                    display.set_pen(color)
                    display.rectangle(px, py, PIXEL_SIZE, PIXEL_SIZE)

def render_game(state):
    display.set_pen(BLACK)
    display.clear()
    
    if state['p1']['alive']:
        draw_plane(state['p1']['x'], state['p1']['y'], state['p1']['dir'], 0, BLUE)
    
    if state['p2']['alive']:
        draw_plane(state['p2']['x'], state['p2']['y'], state['p2']['dir'], 1, RED)
    
    for shot in state['shots']:
        if shot['owner'] == 1:
            display.set_pen(CYAN)
        else:
            display.set_pen(ORANGE)
        
        x = shot['x'] * PIXEL_SIZE
        y = shot['y'] * PIXEL_SIZE
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            # Draw larger bullets (3x3 pixels)
            display.rectangle(x - 1, y - 1, 4, 4)
    
    if state['game_over']:
        display.set_pen(BLACK)
        display.rectangle(60, 95, 200, 50)
        winner_color = BLUE if state['winner'] == 1 else RED
        display.set_pen(winner_color)
        winner_text = "BLUE WINS!" if state['winner'] == 1 else "RED WINS!"
        display.text(winner_text, 70, 110, scale=3)
    
    if not state['connected']:
        display.set_pen(YELLOW)
        display.text("CONNECTING..", 80, 5, scale=2)
        display.set_pen(WHITE)
        display.text("Press X to retry", 60, 220, scale=1)
    else:
        display.set_pen(BLUE if state['player_id'] == 1 else RED)
        display.text(f"P{state['player_id']}", 5, 5, scale=2)
        
        state_age = time.ticks_diff(time.ticks_ms(), state['last_state_time'])
        if state_age > 1000:
            display.set_pen(YELLOW)
            display.text("WEAK", WIDTH - 50, 5, scale=1)
    
    display.update()

def main():
    print("Starting Dogfight Client...")
    
    shared_state = SharedState()
    
    _thread.start_new_thread(network_thread, (shared_state,))
    
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(CYAN)
    display.text("DOGFIGHT", 80, 80, scale=4)
    display.set_pen(WHITE)
    display.text("Connecting...", 90, 130, scale=2)
    display.update()
    time.sleep(2)
    
    led.set_rgb(0, 0, 255)
    
    prev_x_button = False
    prev_shot_count = 0
    flash_timer = 0
    
    while True:
        btn_a = button_a.read()
        btn_b = button_b.read()
        btn_x = button_x.read()
        btn_y = button_y.read()
        
        if btn_x and not prev_x_button:
            print("Reconnect button pressed")
            shared_state.request_reconnect()
        prev_x_button = btn_x
        
        # X is reconnect, Y is fire
        shared_state.set_input(btn_a, btn_b, btn_y, False)
        
        state = shared_state.get_display_state()
        
        # LED flash when firing
        if flash_timer > 0:
            flash_timer -= 1
        
        my_shot_count = state.get('my_shot_count', 0)
        if my_shot_count > prev_shot_count:
            # New shot fired! Flash bright white
            flash_timer = 3  # Flash for 3 frames
            print(f"FIRE! Shots: {my_shot_count}")
        prev_shot_count = my_shot_count
        
        # Set LED color
        if flash_timer > 0:
            # Bright white flash when firing
            led.set_rgb(255, 255, 255)
        elif state['connected']:
            if state['game_over']:
                if state['winner'] == state['player_id']:
                    led.set_rgb(0, 255, 0)
                else:
                    led.set_rgb(255, 0, 0)
            else:
                led.set_rgb(0, 100, 100)
        else:
            led.set_rgb(255, 255, 0)
        
        render_game(state)
        
        time.sleep(0.03)  # ~30fps

if __name__ == "__main__":
    main()
