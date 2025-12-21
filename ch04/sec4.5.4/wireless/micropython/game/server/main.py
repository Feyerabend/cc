"""
Dogfight Game Server for Raspberry Pi Pico W
- Robust connection handling with timeouts
- Proper player ID assignment
- Connection monitoring and cleanup
- Enhanced debugging
"""

import network
import socket
import time
from machine import Pin
from pimoroni import Button, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
import protocol

# WiFi AP Configuration
SSID = "DOGFIGHT_SERVER"
PASSWORD = "dogfight123"
SERVER_IP = "192.168.4.1"
UDP_PORT = 8888

# Timeouts
CLIENT_TIMEOUT = 5000  # 5 seconds without input = disconnect
HEARTBEAT_INTERVAL = 1000  # Send heartbeat every 1 second

# Display setup
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 100, 255)
CYAN = display.create_pen(0, 200, 200)
ORANGE = display.create_pen(255, 128, 0)
YELLOW = display.create_pen(255, 255, 0)

# Buttons
button_y = Button(15)

# LED
led = RGBLED(6, 7, 8)

class Shot:
    def __init__(self, x, y, direction, owner):
        self.x = x
        self.y = y
        self.dir = direction
        self.range = 18
        self.active = True
        self.owner = owner
    
    def update(self):
        if not self.active:
            return
        
        for _ in range(2):
            self.x += protocol.DIR_DX[self.dir]
            self.y += protocol.DIR_DY[self.dir]
        
        if self.x < 0: self.x = protocol.GAME_WIDTH - 1
        if self.x >= protocol.GAME_WIDTH: self.x = 0
        if self.y < 0: self.y = protocol.GAME_HEIGHT - 1
        if self.y >= protocol.GAME_HEIGHT: self.y = 0
        
        self.range -= 1
        if self.range <= 0:
            self.active = False
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'dir': self.dir,
            'range': self.range,
            'owner': self.owner
        }

class Player:
    def __init__(self, player_id, start_x, start_y, start_dir):
        self.id = player_id
        self.x = start_x
        self.y = start_y
        self.dir = start_dir
        self.alive = True
        self.shots = []
        self.fire_cooldown = 0
        self.turn_counter = 0
        
        self.btn_a = False
        self.btn_b = False
        self.btn_x = False
        self.btn_y = False
        self.prev_fire = False
    
    def update_input(self, btn_a, btn_b, btn_x, btn_y):
        self.btn_a = btn_a
        self.btn_b = btn_b
        self.btn_x = btn_x
        self.btn_y = btn_y
    
    def update(self):
        if not self.alive:
            return False
        
        old_x, old_y, old_dir = self.x, self.y, self.dir
        
        # X button = fire (btn_x in protocol)
        if self.btn_x:
            if not self.prev_fire:
                self.fire()
            self.prev_fire = True
        else:
            self.prev_fire = False
        
        # A = turn left, B = turn right
        if self.btn_a:
            self.turn_left()
        elif self.btn_b:
            self.turn_right()
        
        self.x += protocol.DIR_DX[self.dir]
        self.y += protocol.DIR_DY[self.dir]
        
        if self.x < 4: self.x = protocol.GAME_WIDTH - 5
        if self.x >= protocol.GAME_WIDTH - 4: self.x = 4
        if self.y < 4: self.y = protocol.GAME_HEIGHT - 5
        if self.y >= protocol.GAME_HEIGHT - 4: self.y = 4
        
        for shot in self.shots[:]:
            shot.update()
            if not shot.active:
                self.shots.remove(shot)
        
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        
        return (old_x != self.x or old_y != self.y or old_dir != self.dir)
    
    def fire(self):
        if self.fire_cooldown == 0 and len(self.shots) < 3:
            nose_x = self.x + protocol.DIR_DX[self.dir] * 4
            nose_y = self.y + protocol.DIR_DY[self.dir] * 4
            self.shots.append(Shot(nose_x, nose_y, self.dir, self.id))
            self.fire_cooldown = 12
            print(f"Player {self.id} fired! Shots: {len(self.shots)}")
            return True
        return False
    
    def turn_left(self):
        self.turn_counter += 1
        if self.turn_counter >= 2:
            self.dir = (self.dir - 1) % 8
            self.turn_counter = 0
    
    def turn_right(self):
        self.turn_counter += 1
        if self.turn_counter >= 2:
            self.dir = (self.dir + 1) % 8
            self.turn_counter = 0
    
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'dir': self.dir,
            'alive': self.alive
        }

class ClientConnection:
    """Track individual client connection state"""
    def __init__(self, addr, player_id):
        self.addr = addr
        self.player_id = player_id
        self.last_seen = time.ticks_ms()
        self.connected = True
    
    def update_activity(self):
        self.last_seen = time.ticks_ms()
    
    def is_timeout(self):
        return time.ticks_diff(time.ticks_ms(), self.last_seen) > CLIENT_TIMEOUT

class GameServer:
    def __init__(self):
        self.players = {}
        self.player1 = Player(1, protocol.GAME_WIDTH - 15, protocol.GAME_HEIGHT - 15, protocol.DIR_W)
        self.player2 = Player(2, 15, 15, protocol.DIR_E)
        self.players[1] = self.player1
        self.players[2] = self.player2
        
        self.clients = {}  # addr -> ClientConnection
        self.player_assignments = {}  # player_id -> addr
        self.next_player_id = 1
        
        self.game_over = False
        self.winner = 0
        self.seq = 0
        
        self.last_full_sync = 0
        self.full_sync_interval = 30
        self.last_heartbeat = 0
        
        self.prev_state = {}
        self.prev_shots = {}
    
    def reset(self):
        print("Resetting game state...")
        self.player1 = Player(1, protocol.GAME_WIDTH - 15, protocol.GAME_HEIGHT - 15, protocol.DIR_W)
        self.player2 = Player(2, 15, 15, protocol.DIR_E)
        self.players[1] = self.player1
        self.players[2] = self.player2
        self.game_over = False
        self.winner = 0
        self.seq = 0
        self.prev_state = {}
        self.prev_shots = {}
        # Force full sync on next update
        self.last_full_sync = -1000
    
    def assign_player_id(self, addr):
        """Assign a player ID, ensuring uniqueness"""
        # Check if this address already has an ID
        for client in self.clients.values():
            if client.addr == addr:
                return client.player_id
        
        # Find available player ID (1 or 2)
        used_ids = set(self.player_assignments.keys())
        available_ids = {1, 2} - used_ids
        
        if not available_ids:
            # Both slots taken - check for timeouts
            self.cleanup_disconnected_clients()
            used_ids = set(self.player_assignments.keys())
            available_ids = {1, 2} - used_ids
            
            if not available_ids:
                return None  # No slots available
        
        return min(available_ids)  # Prefer player 1, then 2
    
    def cleanup_disconnected_clients(self):
        """Remove clients that have timed out"""
        disconnected = []
        for addr, client in self.clients.items():
            if client.is_timeout():
                disconnected.append(addr)
        
        for addr in disconnected:
            client = self.clients[addr]
            player_id = client.player_id
            print(f"Client timeout: {addr} (Player {player_id})")
            del self.clients[addr]
            if player_id in self.player_assignments:
                del self.player_assignments[player_id]

    def handle_input(self, data, addr):
        if len(data) < 1:
            return None
        
        pkt_type = data[0]
        
        if pkt_type == protocol.PKT_CLIENT_CONNECT:
            print(f"Connect request from {addr}")
            # Client requesting connection
            player_id = self.assign_player_id(addr)
            
            if player_id is None:
                print(f"Connection rejected (full): {addr}")
                return None
            
            # Create or update client connection
            if addr not in self.clients:
                self.clients[addr] = ClientConnection(addr, player_id)
                self.player_assignments[player_id] = addr
                print(f"Client connected: {addr} -> Player {player_id}")
            else:
                self.clients[addr].update_activity()
            
            ack_packet = protocol.ConnectPacket.pack_ack(player_id)
            print(f"Sending ACK to {addr} with player_id={player_id}")
            return ack_packet
        
        elif pkt_type == protocol.PKT_CLIENT_INPUT:
            if addr in self.clients:
                client = self.clients[addr]
                client.update_activity()
                
                input_data = protocol.ClientInputPacket.unpack(data)
                player_id = client.player_id
                player = self.players.get(player_id)
                
                if player:
                    player.update_input(
                        input_data['btn_a'],
                        input_data['btn_b'],
                        input_data['btn_x'],
                        input_data['btn_y']
                    )
            else:
                # Unknown client - send reconnect hint
                print(f"Input from unknown client: {addr}")
        
        elif pkt_type == protocol.PKT_PING:
            # Respond to ping
            if addr in self.clients:
                self.clients[addr].update_activity()
                ping_data = protocol.PingPacket.unpack(data)
                return protocol.PingPacket.pack_pong(ping_data['seq'], ping_data['timestamp'])
        
        return None

    def update(self):
        if self.game_over:
            return
        
        # Cleanup disconnected clients
        self.cleanup_disconnected_clients()
        
        p1_changed = self.player1.update()
        p2_changed = self.player2.update()
        
        if not self.game_over:
            for shot in self.player1.shots:
                if self.check_shot_hit(shot, self.player2):
                    self.game_over = True
                    self.winner = 1
                    self.player2.alive = False
                    break
            
            if not self.game_over:
                for shot in self.player2.shots:
                    if self.check_shot_hit(shot, self.player1):
                        self.game_over = True
                        self.winner = 2
                        self.player1.alive = False
                        break
    
    def check_shot_hit(self, shot, target):
        if not shot.active or not target.alive:
            return False
        
        dx = abs(shot.x - target.x)
        dy = abs(shot.y - target.y)
        
        if dx < 4 and dy < 4:
            shot.active = False
            return True
        return False
    
    def get_state_packet(self, force_full=False):
        self.seq += 1
        
        if force_full or self.seq - self.last_full_sync >= self.full_sync_interval or self.game_over:
            self.last_full_sync = self.seq
            return self.get_full_state_packet()
        else:
            return self.get_delta_packet()
    
    def get_full_state_packet(self):
        p1_shots = [s.to_dict() for s in self.player1.shots if s.active]
        p2_shots = [s.to_dict() for s in self.player2.shots if s.active]
        
        self.prev_state = {
            1: (self.player1.x, self.player1.y, self.player1.dir),
            2: (self.player2.x, self.player2.y, self.player2.dir)
        }
        self.prev_shots = {
            1: set((s.x, s.y) for s in self.player1.shots if s.active),
            2: set((s.x, s.y) for s in self.player2.shots if s.active)
        }
        
        return protocol.FullStatePacket.pack(
            self.seq,
            self.player1.to_dict(),
            self.player2.to_dict(),
            p1_shots,
            p2_shots,
            self.game_over,
            self.winner
        )

    def get_delta_packet(self):
        p1_pos = None
        p2_pos = None
        shots_added = []
        shots_removed = []
        
        if 1 in self.prev_state:
            px, py, pd = self.prev_state[1]
            if px != self.player1.x or py != self.player1.y or pd != self.player1.dir:
                p1_pos = {'x': self.player1.x, 'y': self.player1.y}
                if pd != self.player1.dir:
                    p1_pos['dir'] = self.player1.dir
        
        if 2 in self.prev_state:
            px, py, pd = self.prev_state[2]
            if px != self.player2.x or py != self.player2.y or pd != self.player2.dir:
                p2_pos = {'x': self.player2.x, 'y': self.player2.y}
                if pd != self.player2.dir:
                    p2_pos['dir'] = self.player2.dir
        
        current_p1_shots = set((s.x, s.y) for s in self.player1.shots if s.active)
        current_p2_shots = set((s.x, s.y) for s in self.player2.shots if s.active)
        
        if 1 in self.prev_shots:
            new_shots = current_p1_shots - self.prev_shots[1]
            for sx, sy in new_shots:
                for shot in self.player1.shots:
                    if shot.active and shot.x == sx and shot.y == sy:
                        shots_added.append(shot.to_dict())
                        break
        
        if 2 in self.prev_shots:
            new_shots = current_p2_shots - self.prev_shots[2]
            for sx, sy in new_shots:
                for shot in self.player2.shots:
                    if shot.active and shot.x == sx and shot.y == sy:
                        shots_added.append(shot.to_dict())
                        break
        
        if 1 in self.prev_shots:
            removed = self.prev_shots[1] - current_p1_shots
            shots_removed.extend(list(removed))
        
        if 2 in self.prev_shots:
            removed = self.prev_shots[2] - current_p2_shots
            shots_removed.extend(list(removed))
        
        self.prev_state = {
            1: (self.player1.x, self.player1.y, self.player1.dir),
            2: (self.player2.x, self.player2.y, self.player2.dir)
        }
        self.prev_shots = {
            1: current_p1_shots,
            2: current_p2_shots
        }
        
        return protocol.DeltaStatePacket.pack(
            self.seq,
            p1_pos,
            p2_pos,
            shots_added,
            shots_removed,
            self.game_over,
            self.winner
        )

def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=SSID, password=PASSWORD)
    ap.active(True)
    
    while not ap.active():
        time.sleep(0.1)
    
    print(f"AP Active: {SSID}")
    print(f"IP: {ap.ifconfig()[0]}")
    return ap

def display_status(game, client_count):
    display.set_pen(BLACK)
    display.clear()
    
    display.set_pen(CYAN)
    display.text("DOGFIGHT SERVER", 10, 10, scale=2)
    
    display.set_pen(WHITE)
    display.text(f"Clients: {client_count}/2", 10, 40, scale=2)
    
    display.set_pen(BLUE)
    p1_status = "ALIVE" if game.player1.alive else "DEAD"
    p1_conn = "CONN" if 1 in game.player_assignments else "----"
    display.text(f"P1:{p1_conn} {p1_status}", 10, 70, scale=2)
    
    display.set_pen(RED)
    p2_status = "ALIVE" if game.player2.alive else "DEAD"
    p2_conn = "CONN" if 2 in game.player_assignments else "----"
    display.text(f"P2:{p2_conn} {p2_status}", 10, 95, scale=2)
    
    if game.game_over:
        display.set_pen(GREEN)
        winner_color = "BLUE" if game.winner == 1 else "RED"
        display.text(f"{winner_color} WINS!", 10, 130, scale=3)
    else:
        display.set_pen(ORANGE)
        display.text(f"Frame: {game.seq}", 10, 130, scale=2)
    
    display.set_pen(WHITE)
    display.text(f"P1 Shots: {len(game.player1.shots)}", 10, 160, scale=1)
    display.text(f"P2 Shots: {len(game.player2.shots)}", 10, 175, scale=1)
    display.text("Y=Reset", 10, 220, scale=1)
    
    display.update()

def main():
    print("Starting Dogfight Server..")
    
    ap = setup_ap()
    led.set_rgb(0, 255, 0)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, UDP_PORT))
    sock.setblocking(False)
    
    # Give socket time to be ready
    time.sleep(0.5)
    
    print(f"Listening on {SERVER_IP}:{UDP_PORT}")
    print("Server ready for connections")
    
    game = GameServer()
    
    frame_count = 0
    last_display_update = 0
    
    while True:
        frame_start = time.ticks_ms()
        
        if button_y.read():
            print("Reset game")
            game.reset()
            led.set_rgb(255, 255, 0)
            time.sleep(0.2)
            led.set_rgb(0, 255, 0)
        
        # Receive multiple packets per frame
        packets_received = 0
        for _ in range(10):
            try:
                data, addr = sock.recvfrom(256)
                packets_received += 1
                response = game.handle_input(data, addr)
                if response:
                    sock.sendto(response, addr)
            except OSError:
                break
        
        game.update()
        
        state_packet = game.get_state_packet()
        
        for addr in list(game.clients.keys()):
            try:
                sock.sendto(state_packet, addr)
            except Exception as e:
                print(f"Send error to {addr}: {e}")
        
        if frame_count - last_display_update >= 5:
            display_status(game, len(game.clients))
            last_display_update = frame_count
        
        if game.game_over:
            if game.winner == 1:
                led.set_rgb(0, 0, 255)
            else:
                led.set_rgb(255, 0, 0)
        else:
            intensity = 50 if len(game.clients) == 2 else 10
            led.set_rgb(0, intensity, intensity)
        
        frame_count += 1
        
        elapsed = time.ticks_diff(time.ticks_ms(), frame_start)
        sleep_time = max(0, 50 - elapsed)  # 20fps target
        time.sleep_ms(sleep_time)

if __name__ == "__main__":
    main()
