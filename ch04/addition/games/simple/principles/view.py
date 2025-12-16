import picodisplay as display
import utime
import urandom

# --- setup display ---
buf = bytearray(display.get_width() * display.get_height() * 2)
display.init(buf)

WIDTH, HEIGHT = display.get_width(), display.get_height()
TILE = 16
VIEW_W, VIEW_H = WIDTH // TILE, HEIGHT // TILE   # viewport size in tiles

WORLD_W, WORLD_H = 40, 30   # bigger world!

# --- simple map generation ---
world = []
for y in range(WORLD_H):
    row = []
    for x in range(WORLD_W):
        if x == 0 or y == 0 or x == WORLD_W - 1 or y == WORLD_H - 1:
            row.append(1)  # wall border
        elif urandom.getrandbits(4) == 0:  # random walls
            row.append(1)
        else:
            row.append(0)
    world.append(row)

# --- entities ---
player = {
    "x": 5,
    "y": 5,
    "color": display.create_pen(0, 255, 255)
}

bots = []
for i in range(5):
    bots.append({"x": 10 + i * 3, "y": 8, "state": "patrol",
                 "timer": 0, "color": display.create_pen(255, 0, 0)})

# --- helpers ---
def is_wall(x, y):
    if x < 0 or y < 0 or x >= WORLD_W or y >= WORLD_H:
        return True
    return world[y][x] == 1

def move_entity(ent, dx, dy):
    nx, ny = ent["x"] + dx, ent["y"] + dy
    if not is_wall(nx, ny):
        ent["x"], ent["y"] = nx, ny

# --- drawing ---
def draw_world(vx, vy):
    for ty in range(VIEW_H):
        for tx in range(VIEW_W):
            wx, wy = vx + tx, vy + ty
            if 0 <= wx < WORLD_W and 0 <= wy < WORLD_H:
                if world[wy][wx] == 1:
                    display.set_pen(display.create_pen(80, 80, 80))  # wall
                else:
                    display.set_pen(display.create_pen(0, 0, 0))  # floor
                display.rectangle(tx * TILE, ty * TILE, TILE, TILE)

def draw_entity(ent, vx, vy):
    sx, sy = (ent["x"] - vx) * TILE, (ent["y"] - vy) * TILE
    if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
        display.set_pen(ent["color"])
        display.rectangle(sx + 3, sy + 3, TILE - 6, TILE - 6)

# --- bots AI ---
def update_bots():
    for b in bots:
        b["timer"] -= 1
        if b["timer"] <= 0:
            if urandom.getrandbits(4) == 0:  # ~1/16 chance to stalk
                b["state"] = "stalk"
            else:
                b["state"] = "patrol"
            b["timer"] = 10 + urandom.getrandbits(3)

        if b["state"] == "patrol":
            if urandom.getrandbits(2) == 0:
                dirs = [(1,0),(-1,0),(0,1),(0,-1)]
                dx,dy = dirs[urandom.getrandbits(2)]
                move_entity(b, dx, dy)
        elif b["state"] == "stalk":
            dx = 1 if player["x"] > b["x"] else -1 if player["x"] < b["x"] else 0
            dy = 1 if player["y"] > b["y"] else -1 if player["y"] < b["y"] else 0
            if urandom.getrandbits(1):
                move_entity(b, dx, 0)
            else:
                move_entity(b, 0, dy)

# --- input ---
def update_player():
    if display.is_pressed(display.BUTTON_A): move_entity(player, -1, 0)
    if display.is_pressed(display.BUTTON_B): move_entity(player, 1, 0)
    if display.is_pressed(display.BUTTON_X): move_entity(player, 0, -1)
    if display.is_pressed(display.BUTTON_Y): move_entity(player, 0, 1)

# --- main loop ---
while True:
    update_player()
    update_bots()

    # viewport follows player
    vx = player["x"] - VIEW_W // 2
    vy = player["y"] - VIEW_H // 2
    vx = max(0, min(WORLD_W - VIEW_W, vx))
    vy = max(0, min(WORLD_H - VIEW_H, vy))

    display.set_pen(display.create_pen(0,0,0))
    display.clear()

    draw_world(vx, vy)
    draw_entity(player, vx, vy)
    for b in bots: draw_entity(b, vx, vy)

    display.update()
    utime.sleep(0.15)

