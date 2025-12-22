from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import Button
import time
import random
import math

# Setup display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0, pen_type=PEN_RGB565)

WIDTH, HEIGHT = display.get_bounds()

# Colors
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 100, 255)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GRAY = display.create_pen(128, 128, 128)
BROWN = display.create_pen(139, 69, 19)
YELLOW = display.create_pen(255, 255, 0)

# Button pins
button_a = 12  # Move left/up
button_b = 13  # Move right/down
button_x = 14  # Shoot
button_y = 15  # Change angle

def read_button(pin):
    import machine
    return machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP).value() == 0

class Missile:
    def __init__(self, x, y, dx, dy, owner):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.owner = owner
        self.active = True

    def update(self, dt):
        if not self.active:
            return
        
        self.x += self.dx * dt * 60
        self.y += self.dy * dt * 60
        self.dy += 0.12  # Medium gravity for balanced difficulty
        
        # Check boundaries
        if self.x < 0 or self.x > WIDTH or self.y > HEIGHT:
            self.active = False

    def draw(self):
        if self.active:
            display.set_pen(YELLOW)
            display.circle(int(self.x), int(self.y), 2)

class Tank:
    def __init__(self, x, y, color, is_player=False, facing_right=True):
        self.x = x
        self.y = y
        self.color = color
        self.health = 5
        self.max_health = 5
        self.is_player = is_player
        self.facing_right = facing_right
        self.speed = 1.5
        self.shoot_timer = 0
        self.angle = 45 if facing_right else 135  # Shooting angle in degrees
        self.missiles = []
        
        # AI behavior
        self.ai_timer = 0
        self.move_direction = 0

    def update(self, dt):
        if self.is_player:
            # Player controls
            if read_button(button_a):
                if self.facing_right:
                    self.y = max(40, self.y - self.speed)  # Move up
                else:
                    self.y = min(HEIGHT - 40, self.y + self.speed)  # Move down
            
            if read_button(button_b):
                if self.facing_right:
                    self.y = min(HEIGHT - 40, self.y + self.speed)  # Move down
                else:
                    self.y = max(40, self.y - self.speed)  # Move up
            
            if read_button(button_y):
                # Adjust angle with Y + A/B
                if read_button(button_a):
                    # Y + A: Raise angle
                    if self.facing_right:
                        self.angle = min(80, self.angle + 1.5)
                    else:
                        self.angle = max(100, self.angle - 1.5)
                elif read_button(button_b):
                    # Y + B: Lower angle
                    if self.facing_right:
                        self.angle = max(10, self.angle - 1.5)
                    else:
                        self.angle = min(170, self.angle + 1.5)
            
            if read_button(button_x) and self.shoot_timer <= 0:
                self.shoot()
        else:
            # Enemy AI
            self.ai_timer += 1
            
            # Random movement every 2 seconds
            if self.ai_timer % 120 == 0:
                self.move_direction = random.choice([-1, 0, 1])
            
            # Move based on direction
            if self.move_direction != 0:
                new_y = self.y + self.move_direction * self.speed
                self.y = max(40, min(HEIGHT - 40, new_y))
            
            # Randomly adjust angle
            if random.random() < 0.02:
                if self.facing_right:
                    self.angle += random.choice([-2, 2])
                    self.angle = max(10, min(80, self.angle))
                else:
                    self.angle += random.choice([-2, 2])
                    self.angle = max(100, min(170, self.angle))
            
            # More active enemy shooting
            if random.random() < 0.03 and self.shoot_timer <= 0:
                self.shoot()

        self.shoot_timer = max(0, self.shoot_timer - 1)
        
        # Update missiles
        for missile in self.missiles[:]:
            missile.update(dt)
            if not missile.active:
                self.missiles.remove(missile)

    def shoot(self):
        power = 5.0  # Balanced power
        angle_rad = math.radians(self.angle)
        
        # Calculate missile starting position (from turret tip)
        turret_length = 15
        start_x = self.x + math.cos(angle_rad) * turret_length
        start_y = self.y - math.sin(angle_rad) * turret_length
        
        # Calculate velocity
        dx = math.cos(angle_rad) * power
        dy = -math.sin(angle_rad) * power
        
        self.missiles.append(Missile(start_x, start_y, dx, dy, self))
        self.shoot_timer = 40  # Balanced cooldown

    def check_collisions(self, other_missiles):
        for missile in other_missiles[:]:
            if missile.active and missile.owner != self:
                # Check collision with tank
                if abs(missile.x - self.x) < 15 and abs(missile.y - self.y) < 12:
                    self.health -= 1
                    missile.active = False
                    other_missiles.remove(missile)
                    return True
        return False

    def draw(self):
        # Tank body
        display.set_pen(self.color)
        display.rectangle(int(self.x) - 12, int(self.y) - 8, 24, 16)
        
        # Tank tracks
        display.set_pen(GRAY)
        display.rectangle(int(self.x) - 14, int(self.y) + 6, 28, 4)
        
        # Turret
        display.set_pen(self.color)
        display.circle(int(self.x), int(self.y) - 2, 8)
        
        # Gun barrel
        angle_rad = math.radians(self.angle)
        end_x = self.x + math.cos(angle_rad) * 20
        end_y = self.y - math.sin(angle_rad) * 20
        
        display.set_pen(BLACK)
        # Draw line for gun barrel (approximate with small rectangles)
        steps = 10
        for i in range(steps):
            t = i / steps
            x = int(self.x + (end_x - self.x) * t)
            y = int(self.y + (end_y - self.y) * t)
            display.rectangle(x - 1, y - 1, 2, 2)
        
        # Health bar
        bar_width = 24
        bar_height = 4
        health_ratio = self.health / self.max_health
        
        display.set_pen(RED)
        display.rectangle(int(self.x) - bar_width//2, int(self.y) - 20, bar_width, bar_height)
        display.set_pen(GREEN)
        display.rectangle(int(self.x) - bar_width//2, int(self.y) - 20, int(bar_width * health_ratio), bar_height)
        
        # Draw missiles
        for missile in self.missiles:
            missile.draw()

# Initialize game
player = Tank(50, HEIGHT//2, BLUE, True, True)
enemy = Tank(WIDTH - 50, HEIGHT//2, RED, False, False)
game_over = False
winner = None
clock = 0

# Game loop
while not game_over:
    dt = 1/60
    clock += 1
    
    # Update tanks
    player.update(dt)
    enemy.update(dt)
    
    # Check collisions
    all_missiles = player.missiles + enemy.missiles
    player.check_collisions(enemy.missiles)
    enemy.check_collisions(player.missiles)
    
    # Check win conditions
    if player.health <= 0:
        winner = "ENEMY WINS!"
        game_over = True
    elif enemy.health <= 0:
        winner = "PLAYER WINS!"
        game_over = True
    
    # Clear screen
    display.set_pen(BLUE)
    display.rectangle(0, 0, WIDTH, HEIGHT//3)  # Sky
    display.set_pen(GREEN)
    display.rectangle(0, HEIGHT//3, WIDTH, HEIGHT//3)  # Hills
    display.set_pen(BROWN)
    display.rectangle(0, 2*HEIGHT//3, WIDTH, HEIGHT//3)  # Ground
    
    # Draw tanks
    player.draw()
    enemy.draw()
    
    # Draw UI
    display.set_pen(WHITE)
    display.text(f"Health: {player.health}", 10, 10, scale=1)
    display.text(f"Enemy: {enemy.health}", WIDTH - 80, 10, scale=1)
    display.text(f"Angle: {int(player.angle)}", 10, 25, scale=1)
    
    # Controls hint
    display.text("A/B:Move X:Shoot Y+A:Up Y+B:Down", 10, HEIGHT - 15, scale=1)
    
    display.update()
    time.sleep(dt)

# Game over screen
if winner:
    display.set_pen(BLACK)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(WHITE)
    display.text(winner, WIDTH//2 - 40, HEIGHT//2, scale=2)
    display.update()
    time.sleep(3)

print("Game over!")

