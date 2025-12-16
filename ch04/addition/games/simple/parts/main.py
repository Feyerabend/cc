import picodisplay as display
import utime
import urandom

# --- setup display ---
buf = bytearray(display.get_width() * display.get_height() * 2)
display.init(buf)

WIDTH, HEIGHT = display.get_width(), display.get_height()
TILE = 20
MAP_W, MAP_H = 12, 7

# --- simple map generation ---
world = []
for y in range(MAP_H):
    row = []
    for x in range(MAP_W):
        if x == 0 or y == 0 or x == MAP_W - 1 or y == MAP_H - 1 or urandom.getrandbits(4) == 0:
            row.append(1)  # wall
        else:
            row.append(0)  # floor
    world.append(row)

# --- entities ---
player = {
    "x": 2,
    "y": 2,
    "color": display.create_pen(0, 255, 255)
}

bots = []
for i in range(3):
    bots.append({"x": 5 + i * 2, "y": 4, "state": "patrol",
                 "timer": 0, "color": display.create_pen(255, 0, 0)})

# --- helpers ---
def is_wall(x, y):
    if x < 0 or y < 0 or x >= MAP_W or y >= MAP_H:
        return True
    return world[y][x] == 1

def move_entity(ent, dx, dy):
    nx, ny = ent["x"] + dx, ent["y"] + dy
    if not is_wall(nx, ny):
        ent["x"], ent["y"] = nx, ny

# --- drawing ---
def draw_world():
    for y in range(MAP_H):
        for x in range(MAP_W):
            if world[y][x] == 1:
                display.set_pen(display.create_pen(80, 80, 80))  # wall
            else:
                display.set_pen(display.create_pen(0, 0, 0))  # floor
            display.rectangle(x * TILE, y * TILE, TILE, TILE)

def draw_entity(e):
    display.set_pen(e["color"])
    display.rectangle(e["x"] * TILE + 4, e["y"] * TILE + 4, TILE - 8, TILE - 8)

# --- bots AI ---
def update_bots():
    for b in bots:
        b["timer"] -= 1
        if b["timer"] <= 0:
            if urandom.getrandbits(4) == 0:  # ~1/16 chance
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

    display.set_pen(display.create_pen(0,0,0))
    display.clear()

    draw_world()
    draw_entity(player)
    for b in bots: draw_entity(b)

    display.update()
    utime.sleep(0.15)
