import picodisplay as display
import math, time

# Initialise display
buf = bytearray(display.get_width() * display.get_height() * 2)
display.init(buf)

WIDTH, HEIGHT = display.get_width(), display.get_height()

# World settings
WORLD_W, WORLD_H = 500, 500

# Player
player_x = WORLD_W // 2
player_y = WORLD_H // 2
player_angle = 0
player_speed = 2

# Obstacles (x,y,w,h)
obstacles = [
    (100, 100, 60, 30),
    (300, 200, 50, 50),
    (200, 350, 100, 40)
]

def collides(nx, ny):
    for ox, oy, ow, oh in obstacles:
        if nx > ox and nx < ox+ow and ny > oy and ny < oy+oh:
            return True
    return False

def draw_rect(x, y, w, h, r, g, b):
    display.set_pen(r, g, b)
    display.rectangle(int(x), int(y), int(w), int(h))

def draw_circle(x, y, r, cr, cg, cb):
    display.set_pen(cr, cg, cb)
    display.circle(int(x), int(y), int(r))

def draw_player():
    # player drawn at screen centre
    cx, cy = WIDTH//2, HEIGHT//2

    # rotate rectangle body
    body_w, body_h = 30, 20
    corners = [
        (-body_w//2, -body_h//2),
        ( body_w//2, -body_h//2),
        ( body_w//2,  body_h//2),
        (-body_w//2,  body_h//2)
    ]
    cos_a = math.cos(player_angle)
    sin_a = math.sin(player_angle)
    rotated = []
    for (x,y) in corners:
        rx = x*cos_a - y*sin_a
        ry = x*sin_a + y*cos_a
        rotated.append((cx+int(rx), cy+int(ry)))

    # draw body (simple polygon fill approximation)
    display.set_pen(0,0,255)
    display.polygon(rotated)

    # head circle on "front"
    hx = cx + int(-sin_a*0 + cos_a*0)
    hy = cy + int(sin_a*(-15) + cos_a*0)
    draw_circle(hx, hy, 6, 255, 200, 200)

def update():
    global player_x, player_y, player_angle

    # button states
    left   = display.is_pressed(display.BUTTON_A)
    right  = display.is_pressed(display.BUTTON_B)
    up     = display.is_pressed(display.BUTTON_X)
    down   = display.is_pressed(display.BUTTON_Y)

    if left:  player_angle -= 0.05
    if right: player_angle += 0.05

    nx, ny = player_x, player_y
    if up:
        nx += math.cos(player_angle) * player_speed
        ny += math.sin(player_angle) * player_speed
    if down:
        nx -= math.cos(player_angle) * player_speed
        ny -= math.sin(player_angle) * player_speed

    if not collides(nx, ny):
        player_x, player_y = nx, ny

def draw():
    display.set_pen(240,240,240)
    display.clear()

    # viewport
    view_x = player_x - WIDTH//2
    view_y = player_y - HEIGHT//2

    # draw obstacles
    for ox, oy, ow, oh in obstacles:
        sx = ox - view_x
        sy = oy - view_y
        if 0 <= sx+ow and sx < WIDTH and 0 <= sy+oh and sy < HEIGHT:
            draw_rect(sx, sy, ow, oh, 150, 75, 0)

    # draw player
    draw_player()

    display.update()

while True:
    update()
    draw()
    time.sleep(0.02)
