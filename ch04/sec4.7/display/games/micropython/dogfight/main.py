"""
Dogfight Game for Raspberry Pi Pico with Pimoroni Display Pack 2.0
Player vs AI opponent - Using PicoGraphics Library
With Classic Atari-style Jet Sprites

Controls:
- A (GP12): Turn left
- B (GP13): Turn right  
- A+B together: Fire
- Y (GP15): Reset game
"""

import time
import random
import math
from pimoroni import Button, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

# Init display using PicoGraphics
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

# Init buttons
button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Init RGB LED
led = RGBLED(6, 7, 8)

# Create color pens
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 0, 255)
YELLOW = display.create_pen(255, 255, 0)
CYAN = display.create_pen(0, 200, 200)
ORANGE = display.create_pen(255, 128, 0)

# Game constants
GAME_WIDTH = 100#80
GAME_HEIGHT = 80#72
PIXEL_SIZE = 2
SCREEN_WIDTH = GAME_WIDTH * PIXEL_SIZE
SCREEN_HEIGHT = GAME_HEIGHT * PIXEL_SIZE

# Directions (0-7) not sure these are the proper representations
DIR_N, DIR_NE, DIR_E, DIR_SE = 0, 1, 2, 3
DIR_S, DIR_SW, DIR_W, DIR_NW = 4, 5, 6, 7

# Direction deltas
DIR_DX = [0, 1, 1, 1, 0, -1, -1, -1]
DIR_DY = [-1, -1, 0, 1, 1, 1, 0, -1]

TURNS = 2

# Atari-style jet shapes (8x8 grid for each of 8 directions)
# Converted from the Atari assembly code - these are beautiful classic shapes!
PLANE0_SHAPES = [
    # 0
    [0,0,0,1,0,0,0,0,
     0,0,0,1,0,0,0,0,
     0,0,0,1,0,0,0,0,
     0,0,1,1,1,0,0,0,
     0,1,1,1,1,1,0,0,
     1,1,1,1,1,1,1,0,
     1,1,1,1,1,1,1,0,
     0,0,0,1,0,0,0,0],
    
    # 1
    [0,0,0,0,0,0,0,0,
     1,1,0,0,0,0,0,1,
     1,1,1,1,1,1,1,0,
     0,1,1,1,1,1,0,0,
     0,1,1,1,1,0,0,0,
     0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0],
    
    # 2
    [0,1,1,0,0,0,0,0,
     0,1,1,1,0,0,0,0,
     0,1,1,1,1,0,0,0,
     1,1,1,1,1,1,1,1,
     0,1,1,1,1,0,0,0,
     0,1,1,1,0,0,0,0,
     0,1,1,0,0,0,0,0,
     0,0,0,0,0,0,0,0],

    # 3
    [0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0,
     0,1,1,1,1,0,0,0,
     0,1,1,1,1,1,0,0,
     1,1,1,1,1,1,1,0,
     1,1,0,0,0,0,0,1,
     0,0,0,0,0,0,0,0],

    # 4
    [0,0,0,1,0,0,0,0,
     1,1,1,1,1,1,1,0,
     1,1,1,1,1,1,1,0,
     0,1,1,1,1,1,0,0,
     0,0,1,1,1,0,0,0,
     0,0,0,1,0,0,0,0,
     0,0,0,1,0,0,0,0,
     0,0,0,0,0,0,0,0],
    
    # 5
    [0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0,
     0,0,0,1,1,1,1,0,
     0,0,1,1,1,1,1,0,
     0,1,1,1,1,1,1,1,
     1,0,0,0,0,0,1,1,
     0,0,0,0,0,0,0,0],

    
    # 6
    [0,0,0,0,0,1,1,0,
     0,0,0,0,1,1,1,0,
     0,0,0,1,1,1,1,0,
     1,1,1,1,1,1,1,1,
     0,0,0,1,1,1,1,0,
     0,0,0,0,1,1,1,0,
     0,0,0,0,0,1,1,0,
     0,0,0,0,0,0,0,0],
    
    # 7
    [0,0,0,0,0,0,0,0,
     1,0,0,0,0,0,1,1,
     0,1,1,1,1,1,1,1,
     0,0,1,1,1,1,1,0,
     0,0,0,1,1,1,1,0,
     0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0],
]

# Second plane type - slightly different design
PLANE1_SHAPES = [
    # 0
    [0,0,0,1,0,0,0,0,
     0,0,1,1,1,0,0,0,
     0,0,0,1,0,0,0,0,
     0,0,1,1,1,0,0,0,
     0,1,1,1,1,1,0,0,
     1,1,1,1,1,1,1,0,
     1,1,1,1,1,1,1,0,
     0,0,0,1,0,0,0,0],
    
    # 1
    [0,0,0,0,0,0,0,0,
     1,1,0,0,0,1,0,1,
     1,1,1,1,1,1,1,0,
     0,1,1,1,1,1,0,1,
     0,1,1,1,1,0,0,0,
     0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0],
    
    # 2
    [0,1,1,0,0,0,0,0,
     0,1,1,1,0,0,0,0,
     0,1,1,1,1,0,1,0,
     1,1,1,1,1,1,1,1,
     0,1,1,1,1,0,1,0,
     0,1,1,1,0,0,0,0,
     0,1,1,0,0,0,0,0,
     0,0,0,0,0,0,0,0],

    # 3
    [0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0,
     0,0,1,1,0,0,0,0,
     0,1,1,1,1,0,0,0,
     0,1,1,1,1,1,0,1,
     1,1,1,1,1,1,1,0,
     1,1,0,0,0,1,0,1,
     0,0,0,0,0,0,0,0],

    # 4
    [0,0,0,1,0,0,0,0,
     1,1,1,1,1,1,1,0,
     1,1,1,1,1,1,1,0,
     0,1,1,1,1,1,0,0,
     0,0,1,1,1,0,0,0,
     0,0,0,1,0,0,0,0,
     0,0,1,1,1,0,0,0,
     0,0,0,1,0,0,0,0],
    
    # 5
    [0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0,
     0,0,0,1,1,1,1,0,
     1,0,1,1,1,1,1,0,
     0,1,1,1,1,1,1,1,
     1,0,1,0,0,0,1,1,
     0,0,0,0,0,0,0,0],

    
    # 6
    [0,0,0,0,0,1,1,0,
     0,0,0,0,1,1,1,0,
     0,1,0,1,1,1,1,0,
     1,1,1,1,1,1,1,1,
     0,1,0,1,1,1,1,0,
     0,0,0,0,1,1,1,0,
     0,0,0,0,0,1,1,0,
     0,0,0,0,0,0,0,0],
    
    # 7
    [0,0,0,0,0,0,0,0,
     1,0,1,0,0,0,1,1,
     0,1,1,1,1,1,1,1,
     1,0,1,1,1,1,1,0,
     0,0,0,1,1,1,1,0,
     0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0,
     0,0,0,0,1,1,0,0],
]

class Shot:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.dir = direction
        self.range = 18
        self.active = True
    
    def update(self):
        if not self.active:
            return
        
        # Move shot (2.5x speed of plane)
        for _ in range(2):
            self.x += DIR_DX[self.dir]
            self.y += DIR_DY[self.dir]
        
        # Wrap around screen
        if self.x < 0: self.x = GAME_WIDTH - 1
        if self.x >= GAME_WIDTH: self.x = 0
        if self.y < 0: self.y = GAME_HEIGHT - 1
        if self.y >= GAME_HEIGHT: self.y = 0
        
        # Decrement range
        self.range -= 1
        if self.range <= 0:
            self.active = False

class Plane:
    def __init__(self, x, y, direction, plane_type, is_ai=False):
        self.x = x
        self.y = y
        self.dir = direction
        self.type = plane_type
        self.is_ai = is_ai
        self.shots = []
        self.fire_cooldown = 0
        self.alive = True
        self.turn_counter = 0  # CHANGED: Added turn counter for smooth turning
        
        # AI state
        self.ai_timer = 0
        self.ai_state = "chase"
        self.ai_turn_delay = 0
    
    def get_shape(self):
        shapes = PLANE1_SHAPES if self.type == 1 else PLANE0_SHAPES
        return shapes[self.dir]
    
    def update(self):
        if not self.alive:
            return
        
        # Move plane
        self.x += DIR_DX[self.dir]
        self.y += DIR_DY[self.dir]
        
        # Wrap around
        if self.x < 4: self.x = GAME_WIDTH - 5
        if self.x >= GAME_WIDTH - 4: self.x = 4
        if self.y < 4: self.y = GAME_HEIGHT - 5
        if self.y >= GAME_HEIGHT - 4: self.y = 4
        
        # Update shots
        for shot in self.shots[:]:
            shot.update()
            if not shot.active:
                self.shots.remove(shot)
        
        # Update cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
    
    def fire(self):
        if self.fire_cooldown == 0 and len(self.shots) < 3:
            # Fire from nose of plane
            nose_x = self.x + DIR_DX[self.dir] * 4
            nose_y = self.y + DIR_DY[self.dir] * 4
            self.shots.append(Shot(nose_x, nose_y, self.dir))
            self.fire_cooldown = 12
    
    def turn_left(self):
        # CHANGED: Only turn after counter reaches threshold
        self.turn_counter += 1
        if self.turn_counter >= TURNS:  # every TURNS frames
            self.dir = (self.dir - 1) % 8
            self.turn_counter = 0
    
    def turn_right(self):
        # CHANGED: Only turn after counter reaches threshold
        self.turn_counter += 1
        if self.turn_counter >= TURNS:  # every TURNS frames
            self.dir = (self.dir + 1) % 8
            self.turn_counter = 0
    
    def check_hit(self, other_plane):
        shape = other_plane.get_shape()
        for shot in self.shots:
            if not shot.active:
                continue
            
            # Check all 8x8 positions of the plane
            for dy in range(8):
                for dx in range(8):
                    if shape[dy * 8 + dx]:
                        px = other_plane.x + dx - 4
                        py = other_plane.y + dy - 4
                        if abs(shot.x - px) <= 1 and abs(shot.y - py) <= 1:
                            shot.active = False
                            return True
        return False
    
    def ai_update(self, player):
        if not self.alive:
            return
        
        self.ai_timer += 1
        
        # Calculate angle to player
        dx = player.x - self.x
        dy = player.y - self.y
        
        # Wrap-around distance (find shortest path)
        if abs(dx) > GAME_WIDTH / 2:
            dx = dx - GAME_WIDTH if dx > 0 else dx + GAME_WIDTH
        if abs(dy) > GAME_HEIGHT / 2:
            dy = dy - GAME_HEIGHT if dy > 0 else dy + GAME_HEIGHT
        
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Determine target direction
        target_angle = math.atan2(dy, dx)
        target_dir = int((target_angle / (2 * math.pi) * 8 + 2) % 8)
        
        # Simple state machine
        if distance < 20:
            # Close range - try to evade and fire
            self.ai_state = "evade"
            if self.ai_timer % 5 == 0:
                if random.random() < 0.3:
                    self.turn_left() if random.random() < 0.5 else self.turn_right()
            
            # Fire if roughly aimed at player
            dir_diff = abs(self.dir - target_dir)
            if dir_diff <= 1 or dir_diff >= 7:
                if random.random() < 0.5:
                    self.fire()
        
        elif distance < 40:
            # Medium range - chase and fire
            self.ai_state = "chase"
            if self.ai_turn_delay <= 0:
                dir_diff = (target_dir - self.dir) % 8
                if dir_diff <= 4 and dir_diff != 0:
                    self.turn_right()
                    self.ai_turn_delay = 2
                elif dir_diff > 4:
                    self.turn_left()
                    self.ai_turn_delay = 2
                else:
                    if random.random() < 0.4:
                        self.fire()
            else:
                self.ai_turn_delay -= 1
        
        else:
            # Far range - just chase
            self.ai_state = "chase"
            if self.ai_turn_delay <= 0:
                dir_diff = (target_dir - self.dir) % 8
                if dir_diff <= 4 and dir_diff != 0:
                    self.turn_right()
                    self.ai_turn_delay = 3
                elif dir_diff > 4:
                    self.turn_left()
                    self.ai_turn_delay = 3
            else:
                self.ai_turn_delay -= 1

class Game:
    def __init__(self):
        self.player = None
        self.ai = None
        self.game_over = False
        self.winner = None
        self.reset()
    
    def reset(self):
        # Player starts bottom right
        self.player = Plane(GAME_WIDTH - 15, GAME_HEIGHT - 15, DIR_W, 0, is_ai=False)
        
        # AI starts top left
        self.ai = Plane(15, 15, DIR_E, 1, is_ai=True)
        
        self.game_over = False
        self.winner = None
    
    def update(self):
        if self.game_over:
            return
        
        # Update both planes
        self.player.update()
        self.ai.ai_update(self.player)
        self.ai.update()
        
        # Check collisions
        if self.player.check_hit(self.ai):
            self.game_over = True
            self.winner = "Player"
            self.ai.alive = False
        
        if self.ai.check_hit(self.player):
            self.game_over = True
            self.winner = "AI"
            self.player.alive = False
    
    def draw_plane(self, plane, color):
        shape = plane.get_shape()
        for dy in range(8):
            for dx in range(8):
                if shape[dy * 8 + dx]:
                    px = (plane.x + dx - 4) * PIXEL_SIZE
                    py = (plane.y + dy - 4) * PIXEL_SIZE
                    if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                        display.set_pen(color)
                        display.rectangle(px, py, PIXEL_SIZE, PIXEL_SIZE)
    
    def render(self):
        # Clear display
        display.set_pen(BLACK)
        display.clear()
        
        # Draw player (white with cyan highlights)
        if self.player.alive:
            self.draw_plane(self.player, WHITE)
        
        # Draw AI (red with orange highlights)
        if self.ai.alive:
            self.draw_plane(self.ai, RED)
        
        # Draw player shots (cyan)
        display.set_pen(CYAN)
        for shot in self.player.shots:
            if shot.active:
                x = shot.x * PIXEL_SIZE
                y = shot.y * PIXEL_SIZE
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    display.rectangle(x, y, PIXEL_SIZE, PIXEL_SIZE)
        
        # Draw AI shots (orange/yellow)
        display.set_pen(ORANGE)
        for shot in self.ai.shots:
            if shot.active:
                x = shot.x * PIXEL_SIZE
                y = shot.y * PIXEL_SIZE
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    display.rectangle(x, y, PIXEL_SIZE, PIXEL_SIZE)
        
        # Draw game over message
        if self.game_over:
            display.set_pen(BLACK)
            display.rectangle(60, 95, 200, 50)
            display.set_pen(GREEN if self.winner == "Player" else RED)
            msg = f"{self.winner} WINS!"
            display.text(msg, 80, 110, scale=3)
        
        display.update()

# Main game loop
def main():
    game = Game()
    
    # Show startup message
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(CYAN)
    display.text("DOGFIGHT", 80, 80, scale=4)
    display.set_pen(WHITE)
    display.text("Classic Atari Style", 75, 130, scale=2)
    display.text("A/B: Turn  A+B: Fire  Y: Reset", 110, 160, scale=1)
    display.update()
    time.sleep(3)
    
    prev_fire = False
    
    while True:
        # Read buttons
        btn_a = button_a.read()
        btn_b = button_b.read()
        btn_x = button_x.read()
        btn_y = button_y.read()
        
        # Reset game
        if btn_y:
            game.reset()
            led.set_rgb(0, 0, 0)
            time.sleep(0.2)
            continue
        
        # Player controls
        if btn_a and btn_b:
            # Both pressed = fire
            if not prev_fire:
                game.player.fire()
            prev_fire = True
        else:
            # Only one pressed = turn
            if btn_a:
                game.player.turn_left()
            elif btn_b:
                game.player.turn_right()
            prev_fire = False
        
        # Update LED based on game state
        if game.game_over:
            if game.winner == "Player":
                led.set_rgb(0, 255, 0)  # Green
            else:
                led.set_rgb(255, 0, 0)  # Red
        else:
            # Pulse LED based on activity
            intensity = 100 if game.player.fire_cooldown > 0 else 20
            led.set_rgb(0, intensity, intensity)
        
        # Update game logic
        game.update()
        
        # Render
        game.render()
        
        # Frame delay (~10 FPS)
        time.sleep(0.1)

# Run game
if __name__ == "__main__":
    main()