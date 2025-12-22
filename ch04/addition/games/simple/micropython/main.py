from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
import time
import random

# Init Display Pack 2.0
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)

WIDTH = display.get_bounds()[0]  # 320
HEIGHT = display.get_bounds()[1]  # 240

TILE = 16
VIEW_W, VIEW_H = WIDTH // TILE, HEIGHT // TILE  # 20x15 tiles visible

WORLD_W, WORLD_H = 40, 30

# Button mappings for Display Pack 2.0
BUTTON_A = 12
BUTTON_B = 13
BUTTON_X = 14
BUTTON_Y = 15

# Set up buttons
from machine import Pin
btn_a = Pin(BUTTON_A, Pin.IN, Pin.PULL_UP)
btn_b = Pin(BUTTON_B, Pin.IN, Pin.PULL_UP)
btn_x = Pin(BUTTON_X, Pin.IN, Pin.PULL_UP)
btn_y = Pin(BUTTON_Y, Pin.IN, Pin.PULL_UP)

# Create color pens (RGB565 format for Display Pack 2.0)
class Colors:
    WALL = display.create_pen(60, 60, 80)
    FLOOR = display.create_pen(10, 10, 15)
    PLAYER = display.create_pen(0, 255, 200)
    BOT_PATROL = display.create_pen(255, 80, 80)
    BOT_STALK = display.create_pen(255, 0, 0)
    COIN = display.create_pen(255, 215, 0)
    HEALTH = display.create_pen(0, 255, 0)
    BLACK = display.create_pen(0, 0, 0)
    WHITE = display.create_pen(255, 255, 255)
    RED = display.create_pen(255, 0, 0)
    DARK_RED = display.create_pen(100, 0, 0)

def generate_world():
    world = [[1 for _ in range(WORLD_W)] for _ in range(WORLD_H)]
    
    # Create random rooms
    rooms = []
    for _ in range(8):
        w = random.randint(4, 11)  # 4-11 tiles wide
        h = random.randint(4, 11)
        x = random.randint(1, WORLD_W - w - 2)
        y = random.randint(1, WORLD_H - h - 2)
        
        # Carve room
        for ry in range(y, y + h):
            for rx in range(x, x + w):
                if 0 < rx < WORLD_W - 1 and 0 < ry < WORLD_H - 1:
                    world[ry][rx] = 0
        
        rooms.append((x + w//2, y + h//2))
    
    # Connect rooms with corridors
    for i in range(len(rooms) - 1):
        x1, y1 = rooms[i]
        x2, y2 = rooms[i + 1]
        
        # Horizontal then vertical corridor
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 < x < WORLD_W - 1 and 0 < y1 < WORLD_H - 1:
                world[y1][x] = 0
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 < x2 < WORLD_W - 1 and 0 < y < WORLD_H - 1:
                world[y][x2] = 0
    
    return world, rooms

# HELPER FUNCTIONS (define before use!)
def is_wall(x, y):
    if x < 0 or y < 0 or x >= WORLD_W or y >= WORLD_H:
        return True
    return world[y][x] == 1

def distance(x1, y1, x2, y2):
    return abs(x2 - x1) + abs(y2 - y1)

def can_see(x1, y1, x2, y2, max_dist=10):
    if distance(x1, y1, x2, y2) > max_dist:
        return False
    
    dx = 1 if x2 > x1 else -1 if x2 < x1 else 0
    dy = 1 if y2 > y1 else -1 if y2 < y1 else 0
    
    x, y = x1, y1
    while (x, y) != (x2, y2):
        if is_wall(x, y):
            return False
        if abs(x2 - x) > abs(y2 - y):
            x += dx
        else:
            y += dy
    return True

def move_entity(ent, dx, dy):
    nx, ny = ent["x"] + dx, ent["y"] + dy
    if not is_wall(nx, ny):
        ent["x"], ent["y"] = nx, ny
        return True
    return False

def find_empty_tile():
    for _ in range(100):  # Try 100 times
        x = random.randint(0, WORLD_W - 1)
        y = random.randint(0, WORLD_H - 1)
        if not is_wall(x, y):
            return x, y
    return 5, 5  # Fallback

# Generate world
world, spawn_points = generate_world()

# Game state
game_state = {
    "score": 0,
    "health": 100,
    "time": 0,
    "game_over": False
}

# Initialize player
player = {
    "x": spawn_points[0][0] if spawn_points else 5,
    "y": spawn_points[0][1] if spawn_points else 5,
    "dx": 0,
    "dy": 0,
    "color": Colors.PLAYER
}

# Initialize bots
bots = []
for i in range(6):
    bx, by = find_empty_tile()
    bots.append({
        "x": bx,
        "y": by,
        "state": "patrol",
        "timer": random.randint(0, 15),
        "last_seen_x": 0,
        "last_seen_y": 0,
        "color": Colors.BOT_PATROL
    })

# Init collectibles
coins = []
for _ in range(15):
    cx, cy = find_empty_tile()
    coins.append({"x": cx, "y": cy, "collected": False})

health_packs = []
for _ in range(5):
    hx, hy = find_empty_tile()
    health_packs.append({"x": hx, "y": hy, "collected": False})

def update_bots():
    for b in bots:
        b["timer"] -= 1
        
        # Check if can see player
        can_see_player = can_see(b["x"], b["y"], player["x"], player["y"])
        
        if can_see_player:
            b["state"] = "stalk"
            b["last_seen_x"] = player["x"]
            b["last_seen_y"] = player["y"]
            b["timer"] = 20  # Stay in stalk mode
            b["color"] = Colors.BOT_STALK
        elif b["timer"] <= 0:
            # Return to patrol
            b["state"] = "patrol"
            b["color"] = Colors.BOT_PATROL
            b["timer"] = 15 + random.randint(0, 15)
        
        # Movement based on state
        if b["state"] == "patrol":
            if random.randint(0, 3) == 0:  # Move 1/4 of the time
                dirs = [(1,0), (-1,0), (0,1), (0,-1)]
                dx, dy = dirs[random.randint(0, 3)]
                move_entity(b, dx, dy)
        
        elif b["state"] == "stalk":
            target_x = b["last_seen_x"]
            target_y = b["last_seen_y"]
            
            dx = 1 if target_x > b["x"] else -1 if target_x < b["x"] else 0
            dy = 1 if target_y > b["y"] else -1 if target_y < b["y"] else 0
            
            # Try both axes, prefer one randomly
            if random.randint(0, 1):
                if not move_entity(b, dx, 0):
                    move_entity(b, 0, dy)
            else:
                if not move_entity(b, 0, dy):
                    move_entity(b, dx, 0)
        
        # Check collision with player
        if b["x"] == player["x"] and b["y"] == player["y"]:
            game_state["health"] -= 10
            # Push player back
            move_entity(player, -player["dx"], -player["dy"])

def update_player():
    player["dx"], player["dy"] = 0, 0
    
    # Buttons are active LOW (0 = pressed)
    if btn_a.value() == 0:  # A = Left
        player["dx"] = -1
        move_entity(player, -1, 0)
    if btn_b.value() == 0:  # B = Right
        player["dx"] = 1
        move_entity(player, 1, 0)
    if btn_x.value() == 0:  # X = Up
        player["dy"] = -1
        move_entity(player, 0, -1)
    if btn_y.value() == 0:  # Y = Down
        player["dy"] = 1
        move_entity(player, 0, 1)
    
    # Collect items
    for coin in coins:
        if not coin["collected"] and coin["x"] == player["x"] and coin["y"] == player["y"]:
            coin["collected"] = True
            game_state["score"] += 10
    
    for hp in health_packs:
        if not hp["collected"] and hp["x"] == player["x"] and hp["y"] == player["y"]:
            hp["collected"] = True
            game_state["health"] = min(100, game_state["health"] + 30)

def draw_world(vx, vy):
    for ty in range(VIEW_H + 1):
        for tx in range(VIEW_W + 1):
            wx, wy = vx + tx, vy + ty
            if 0 <= wx < WORLD_W and 0 <= wy < WORLD_H:
                color = Colors.WALL if world[wy][wx] == 1 else Colors.FLOOR
                display.set_pen(color)
                display.rectangle(tx * TILE, ty * TILE, TILE, TILE)

def draw_entity(ent, vx, vy):
    sx = (ent["x"] - vx) * TILE
    sy = (ent["y"] - vy) * TILE
    if -TILE < sx < WIDTH and -TILE < sy < HEIGHT:
        display.set_pen(ent["color"])
        display.rectangle(sx + 2, sy + 2, TILE - 4, TILE - 4)

def draw_collectibles(vx, vy):
    for coin in coins:
        if not coin["collected"]:
            sx = (coin["x"] - vx) * TILE
            sy = (coin["y"] - vy) * TILE
            if -TILE < sx < WIDTH and -TILE < sy < HEIGHT:
                display.set_pen(Colors.COIN)
                display.circle(sx + TILE//2, sy + TILE//2, 3)
    
    for hp in health_packs:
        if not hp["collected"]:
            sx = (hp["x"] - vx) * TILE
            sy = (hp["y"] - vy) * TILE
            if -TILE < sx < WIDTH and -TILE < sy < HEIGHT:
                display.set_pen(Colors.HEALTH)
                display.rectangle(sx + 4, sy + 4, TILE - 8, TILE - 8)

def draw_hud():
    # Score
    display.set_pen(Colors.WHITE)
    display.text("Score:" + str(game_state['score']), 2, 2, scale=1)
    
    # Health bar
    bar_w = 60
    bar_h = 8
    bar_x = WIDTH - bar_w - 2
    bar_y = 2
    
    display.set_pen(Colors.DARK_RED)
    display.rectangle(bar_x, bar_y, bar_w, bar_h)
    
    display.set_pen(Colors.HEALTH)
    health_w = int(bar_w * game_state["health"] / 100)
    display.rectangle(bar_x, bar_y, health_w, bar_h)

# Main game loop
frame = 0
print("Starting game loop...")

while game_state["health"] > 0:
    update_player()
    
    if frame % 2 == 0:  # Update bots every other frame
        update_bots()
    
    # Camera follows player
    vx = player["x"] - VIEW_W // 2
    vy = player["y"] - VIEW_H // 2
    vx = max(0, min(WORLD_W - VIEW_W, vx))
    vy = max(0, min(WORLD_H - VIEW_H, vy))
    
    # Render
    display.set_pen(Colors.BLACK)
    display.clear()
    
    draw_world(vx, vy)
    draw_collectibles(vx, vy)
    draw_entity(player, vx, vy)
    for b in bots:
        draw_entity(b, vx, vy)
    
    draw_hud()
    
    display.update()
    game_state["time"] += 1
    frame += 1
    time.sleep(0.1)

# Game Over
display.set_pen(Colors.BLACK)
display.clear()
display.set_pen(Colors.RED)
display.text("GAME OVER", WIDTH//2 - 45, HEIGHT//2 - 10, scale=2)
display.set_pen(Colors.WHITE)
display.text("Score: " + str(game_state['score']), WIDTH//2 - 35, HEIGHT//2 + 15, scale=1)
display.update()

print("Game Over! Final score:", game_state['score'])
