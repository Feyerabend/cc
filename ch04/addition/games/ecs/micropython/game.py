"""
Game for Pimoroni Display Pack 2.0 + Raspberry Pi Pico 2
Gameplay with varied enemies, power-ups, obstacles, and scoring

Hardware: 320x240 IPS LCD, 4 buttons (A, B, X, Y)
Libraries: picographics, pimoroni
"""

from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from pimoroni import Button
import time
import math
import random

# Init display and buttons
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

btn_a = Button(12)  # Left
btn_b = Button(13)  # Right
btn_x = Button(14)  # Up
btn_y = Button(15)  # Down

# Colors
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 100, 255)
YELLOW = display.create_pen(255, 255, 0)
ORANGE = display.create_pen(255, 165, 0)
PURPLE = display.create_pen(180, 0, 255)
CYAN = display.create_pen(0, 255, 255)
GRAY = display.create_pen(100, 100, 100)


# INPUT HANDLER
class InputHandler:
    def __init__(self):
        self.left = False
        self.right = False
        self.up = False
        self.down = False
    
    def poll(self):
        self.left = btn_a.is_pressed
        self.right = btn_b.is_pressed
        self.up = btn_x.is_pressed
        self.down = btn_y.is_pressed
        return self


# ENTITY BASE CLASS
class Entity:
    _next_id = 0
    
    def __init__(self, x, y):
        self.id = Entity._next_id
        Entity._next_id += 1
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.active = True
    
    def update(self, dt, input_handler):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x = max(5, min(WIDTH - 5, self.x))
        self.y = max(5, min(HEIGHT - 5, self.y))
    
    def render(self, display):
        pass


# PLAYER
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 120
        self.size = 8
        self.score = 0
        self.health = 3
        self.invincible_time = 0
        self.power_up_time = 0
        self.combo = 0
        self.combo_timer = 0
    
    def update(self, dt, input_handler):
        # Power-up speed boost
        speed = self.speed * 1.5 if self.power_up_time > 0 else self.speed
        
        # 8-directional movement
        self.vx = 0
        self.vy = 0
        if input_handler.left:
            self.vx = -speed
        if input_handler.right:
            self.vx = speed
        if input_handler.up:
            self.vy = -speed
        if input_handler.down:
            self.vy = speed
        
        # Normalize diagonal movement
        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.707
            self.vy *= 0.707
        
        super().update(dt, input_handler)
        
        # Update timers
        self.invincible_time = max(0, self.invincible_time - dt)
        self.power_up_time = max(0, self.power_up_time - dt)
        self.combo_timer = max(0, self.combo_timer - dt)
        
        if self.combo_timer <= 0:
            self.combo = 0
    
    def take_damage(self):
        if self.invincible_time <= 0:
            self.health -= 1
            self.invincible_time = 2.0  # 2 seconds invincibility
            self.combo = 0
            return True
        return False
    
    def collect_coin(self, value):
        self.combo += 1
        self.combo_timer = 2.0
        multiplier = min(self.combo, 5)
        self.score += value * multiplier
    
    def render(self, display):
        # Flash when invincible
        if self.invincible_time > 0 and int(self.invincible_time * 10) % 2 == 0:
            return
        
        # Glow when powered up
        if self.power_up_time > 0:
            display.set_pen(CYAN)
            display.circle(int(self.x), int(self.y), self.size + 3)
        
        display.set_pen(GREEN)
        display.rectangle(int(self.x - self.size), int(self.y - self.size), 
                         self.size * 2, self.size * 2)


# ENEMY TYPES
class PatrolEnemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 50
        self.size = 7
        self.patrol_points = [
            (random.randint(30, WIDTH-30), random.randint(30, HEIGHT-30))
            for _ in range(4)
        ]
        self.current_target = 0
    
    def update(self, dt, input_handler):
        target = self.patrol_points[self.current_target]
        dx = target[0] - self.x
        dy = target[1] - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 5:
            self.current_target = (self.current_target + 1) % len(self.patrol_points)
        else:
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
        
        super().update(dt, input_handler)
    
    def render(self, display):
        display.set_pen(RED)
        display.circle(int(self.x), int(self.y), self.size)


class ChaserEnemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 40
        self.size = 6
    
    def update(self, dt, input_handler):
        # Get player position from game manager (passed through)
        super().update(dt, input_handler)
    
    def chase(self, target_x, target_y, dt):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
    
    def render(self, display):
        display.set_pen(ORANGE)
        display.circle(int(self.x), int(self.y), self.size)
        # Draw direction indicator
        display.line(int(self.x), int(self.y), 
                    int(self.x + self.vx*0.3), int(self.y + self.vy*0.3))


class WaveEnemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 70
        self.size = 6
        self.time = random.random() * 6.28
        self.direction = random.choice([-1, 1])
    
    def update(self, dt, input_handler):
        self.time += dt * 2
        self.vx = self.speed * self.direction
        self.vy = math.sin(self.time) * 60
        
        # Wrap around
        if self.x < -10:
            self.x = WIDTH + 10
        elif self.x > WIDTH + 10:
            self.x = -10
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.y = max(20, min(HEIGHT - 20, self.y))
    
    def render(self, display):
        display.set_pen(PURPLE)
        display.circle(int(self.x), int(self.y), self.size)


# COLLECTIBLES
class Coin(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.size = 5
        self.time = random.random() * 6.28
        self.value = 10
    
    def update(self, dt, input_handler):
        self.time += dt * 3
        self.y += math.sin(self.time) * 0.3
        super().update(dt, input_handler)
    
    def render(self, display):
        display.set_pen(YELLOW)
        display.circle(int(self.x), int(self.y), self.size)


class PowerUp(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.size = 6
        self.time = 0
    
    def update(self, dt, input_handler):
        self.time += dt * 4
        super().update(dt, input_handler)
    
    def render(self, display):
        display.set_pen(CYAN)
        # Rotating square effect
        s = self.size + math.sin(self.time) * 2
        display.rectangle(int(self.x - s), int(self.y - s), int(s*2), int(s*2))


# OBSTACLES
class Obstacle(Entity):
    def __init__(self, x, y, w, h):
        super().__init__(x, y)
        self.width = w
        self.height = h
        self.size = max(w, h) // 2  # For collision
    
    def render(self, display):
        display.set_pen(GRAY)
        display.rectangle(int(self.x - self.width//2), 
                         int(self.y - self.height//2),
                         self.width, self.height)


# ENTITY MANAGER
class EntityManager:
    def __init__(self):
        self.entities = []
    
    def create_entity(self, entity_type, *args):
        entity = entity_type(*args)
        self.entities.append(entity)
        return entity
    
    def update(self, dt, input_handler):
        for entity in self.entities:
            if entity.active:
                entity.update(dt, input_handler)
    
    def render(self, display):
        for entity in self.entities:
            if entity.active:
                entity.render(display)
    
    def get_by_type(self, entity_type):
        return [e for e in self.entities if isinstance(e, entity_type) and e.active]
    
    def remove_inactive(self):
        self.entities = [e for e in self.entities if e.active]


# COLLISION SYSTEM
def check_collision(e1, e2):
    dx = e1.x - e2.x
    dy = e1.y - e2.y
    dist = math.sqrt(dx*dx + dy*dy)
    return dist < (getattr(e1, 'size', 5) + getattr(e2, 'size', 5))


# PARTICLE EFFECT
class Particle(Entity):
    def __init__(self, x, y, color):
        super().__init__(x, y)
        angle = random.random() * 6.28
        speed = random.randint(30, 80)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = 0.5
        self.color = color
        self.size = 2
    
    def update(self, dt, input_handler):
        super().update(dt, input_handler)
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
    
    def render(self, display):
        display.set_pen(self.color)
        display.circle(int(self.x), int(self.y), self.size)


# GAME
class Game:
    def __init__(self):
        self.entity_manager = EntityManager()
        self.input_handler = InputHandler()
        self.player = None
        self.running = True
        self.game_over = False
        self.last_time = time.ticks_ms()
        self.spawn_timer = 0
        self.wave = 1
        
    def setup(self):
        self.game_over = False
        self.wave = 1
        self.entity_manager = EntityManager()
        
        # Create player
        self.player = self.entity_manager.create_entity(Player, WIDTH // 2, HEIGHT // 2)
        
        # Create obstacles for strategic gameplay
        obstacles = [
            (80, 60, 40, 20),
            (240, 60, 40, 20),
            (160, 120, 20, 60),
            (80, 180, 40, 20),
            (240, 180, 40, 20),
        ]
        for ox, oy, ow, oh in obstacles:
            self.entity_manager.create_entity(Obstacle, ox, oy, ow, oh)
        
        # Create initial enemies
        self.spawn_enemies(3)
        
        # Create initial coins
        for i in range(6):
            self.spawn_coin()
    
    def spawn_enemies(self, count):
        enemy_types = [PatrolEnemy, ChaserEnemy, WaveEnemy]
        for i in range(count):
            enemy_type = random.choice(enemy_types)
            x = random.randint(30, WIDTH - 30)
            y = random.randint(30, HEIGHT - 30)
            # Don't spawn too close to player
            while abs(x - self.player.x) < 50 and abs(y - self.player.y) < 50:
                x = random.randint(30, WIDTH - 30)
                y = random.randint(30, HEIGHT - 30)
            self.entity_manager.create_entity(enemy_type, x, y)
    
    def spawn_coin(self):
        x = random.randint(30, WIDTH - 30)
        y = random.randint(30, HEIGHT - 30)
        self.entity_manager.create_entity(Coin, x, y)
    
    def spawn_power_up(self):
        x = random.randint(40, WIDTH - 40)
        y = random.randint(40, HEIGHT - 40)
        self.entity_manager.create_entity(PowerUp, x, y)
    
    def spawn_particles(self, x, y, color, count=5):
        for _ in range(count):
            self.entity_manager.create_entity(Particle, x, y, color)
    
    def loop(self):
        if self.game_over:
            self.render_game_over()
            # Check for restart
            if self.input_handler.poll().up:
                self.setup()
            return
        
        # Calculate delta time
        current_time = time.ticks_ms()
        dt = time.ticks_diff(current_time, self.last_time) / 1000.0
        self.last_time = current_time
        dt = min(dt, 0.1)
        
        # Get input
        input_state = self.input_handler.poll()
        
        # Update all entities
        self.entity_manager.update(dt, input_state)
        
        # Update chasers to follow player
        for chaser in self.entity_manager.get_by_type(ChaserEnemy):
            chaser.chase(self.player.x, self.player.y, dt)
        
        # Check collisions
        enemies = (self.entity_manager.get_by_type(PatrolEnemy) + 
                  self.entity_manager.get_by_type(ChaserEnemy) +
                  self.entity_manager.get_by_type(WaveEnemy))
        
        coins = self.entity_manager.get_by_type(Coin)
        power_ups = self.entity_manager.get_by_type(PowerUp)
        obstacles = self.entity_manager.get_by_type(Obstacle)
        
        # Player-Enemy collision
        for enemy in enemies:
            if check_collision(self.player, enemy):
                if self.player.take_damage():
                    self.spawn_particles(self.player.x, self.player.y, RED, 8)
                    if self.player.health <= 0:
                        self.game_over = True
        
        # Player-Coin collision
        for coin in coins:
            if check_collision(self.player, coin):
                coin.active = False
                self.player.collect_coin(coin.value)
                self.spawn_particles(coin.x, coin.y, YELLOW, 4)
        
        # Player-PowerUp collision
        for power_up in power_ups:
            if check_collision(self.player, power_up):
                power_up.active = False
                self.player.power_up_time = 5.0
                self.spawn_particles(power_up.x, power_up.y, CYAN, 6)
        
        # Player-Obstacle collision (simple push back)
        for obstacle in obstacles:
            if check_collision(self.player, obstacle):
                dx = self.player.x - obstacle.x
                dy = self.player.y - obstacle.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    push = (obstacle.size + self.player.size - dist)
                    self.player.x += (dx / dist) * push
                    self.player.y += (dy / dist) * push
        
        self.entity_manager.remove_inactive()
        
        # Spawn management
        self.spawn_timer += dt
        
        # Spawn coins
        if len(coins) < 4 and random.random() < 0.02:
            self.spawn_coin()
        
        # Spawn power-ups rarely
        if len(power_ups) == 0 and random.random() < 0.005:
            self.spawn_power_up()
        
        # Wave system - spawn more enemies as score increases
        if self.spawn_timer > 10:
            self.spawn_timer = 0
            if len(enemies) < 6:
                self.spawn_enemies(1)
        
        # Render
        display.set_pen(BLACK)
        display.clear()
        
        self.entity_manager.render(display)
        
        # Draw UI
        display.set_pen(WHITE)
        display.text(f"Score:{self.player.score}", 5, 5, scale=2)
        
        # Health
        for i in range(self.player.health):
            display.set_pen(RED)
            display.rectangle(5 + i * 15, 25, 12, 8)
        
        # Combo
        if self.player.combo > 1:
            display.set_pen(YELLOW)
            display.text(f"x{self.player.combo}", 5, 40, scale=2)
        
        # Power-up indicator
        if self.player.power_up_time > 0:
            display.set_pen(CYAN)
            w = int((self.player.power_up_time / 5.0) * 60)
            display.rectangle(WIDTH - 65, 5, w, 6)
        
        display.set_pen(WHITE)
        display.text("ABXY:Move", 5, HEIGHT - 15, scale=1)
        
        display.update()
    
    def render_game_over(self):
        display.set_pen(BLACK)
        display.clear()
        
        display.set_pen(RED)
        display.text("GAME OVER", WIDTH//2 - 65, HEIGHT//2 - 30, scale=3)
        
        display.set_pen(WHITE)
        display.text(f"Final Score: {self.player.score}", WIDTH//2 - 60, HEIGHT//2 + 10, scale=2)
        display.text("Press X to Restart", WIDTH//2 - 70, HEIGHT//2 + 40, scale=2)
        
        display.update()
    
    def run(self):
        self.setup()
        while self.running:
            self.loop()
            time.sleep(0.016)


if __name__ == "__main__":
    game = Game()
    game.run()
