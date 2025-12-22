from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import Button
import time
import random
import math

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0, pen_type=PEN_RGB565)

WIDTH, HEIGHT = display.get_bounds()

BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 100, 255)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GRAY = display.create_pen(128, 128, 128)
BROWN = display.create_pen(139, 69, 19)
YELLOW = display.create_pen(255, 255, 0)

button_a = 12
button_b = 13
button_x = 14
button_y = 15

def read_button(pin):
    import machine
    return machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP).value() == 0

class Paddle:
    def __init__(self, x, y, color, is_player=False):
        self.x = x
        self.y = y
        self.color = color
        self.is_player = is_player
        self.width = 10
        self.height = 40
        self.speed = 2.0
        self.ai_timer = 0

    def update(self, dt, ball=None):
        if self.is_player:
            if read_button(button_a):
                self.y = max(self.height // 2, self.y - self.speed)
            if read_button(button_b):
                self.y = min(HEIGHT - self.height // 2, self.y + self.speed)
        else:
            self.ai_timer += 1
            if self.ai_timer % 3 == 0 and ball:
                target_y = ball.y
                if random.random() < 0.02:
                    target_y += random.randint(-5, 5)
                ai_speed = self.speed * 1.4
                if self.y < target_y:
                    self.y = min(HEIGHT - self.height // 2, self.y + ai_speed)
                elif self.y > target_y:
                    self.y = max(self.height // 2, self.y - ai_speed)

    def draw(self):
        display.set_pen(self.color)
        display.rectangle(int(self.x - self.width // 2), int(self.y - self.height // 2), self.width, self.height)

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.choice([-4.2, 4.2])
        self.dy = random.uniform(-2.8, 2.8)
        self.radius = 5
        self.speed = 4.2

    def update(self, dt, player_paddle, enemy_paddle):
        self.x += self.dx * dt * 60
        self.y += self.dy * dt * 60

        if self.y - self.radius < 0 or self.y + self.radius > HEIGHT:
            self.dy = -self.dy
            self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        if (self.x - self.radius < player_paddle.x + player_paddle.width // 2 and
            self.x > player_paddle.x - player_paddle.width // 2 and
            abs(self.y - player_paddle.y) < player_paddle.height // 2 + self.radius):
            self.dx = -self.dx
            hit_pos = (self.y - player_paddle.y) / (player_paddle.height // 2)
            self.dy += hit_pos * 0.5
            self.x = player_paddle.x + player_paddle.width // 2 + self.radius

        if (self.x + self.radius > enemy_paddle.x - enemy_paddle.width // 2 and
            self.x < enemy_paddle.x + enemy_paddle.width // 2 and
            abs(self.y - enemy_paddle.y) < enemy_paddle.height // 2 + self.radius):
            self.dx = -self.dx
            hit_pos = (self.y - enemy_paddle.y) / (enemy_paddle.height // 2)
            self.dy += hit_pos * 0.5
            self.x = enemy_paddle.x - enemy_paddle.width // 2 - self.radius

        speed = math.sqrt(self.dx**2 + self.dy**2)
        if speed > 0:
            self.dx = (self.dx / speed) * self.speed
            self.dy = (self.dy / speed) * self.speed

    def draw(self):
        display.set_pen(YELLOW)
        display.circle(int(self.x), int(self.y), self.radius)

player_paddle = Paddle(20, HEIGHT // 2, BLUE, True)
enemy_paddle = Paddle(WIDTH - 20, HEIGHT // 2, RED, False)
ball = Ball(WIDTH // 2, HEIGHT // 2)
player_score = 0
enemy_score = 0
game_over = False
winner = None
clock = 0

while not game_over:
    dt = 1/60
    clock += 1

    player_paddle.update(dt)
    enemy_paddle.update(dt, ball)
    ball.update(dt, player_paddle, enemy_paddle)

    if ball.x < 0:
        enemy_score += 1
        ball.x = WIDTH // 2
        ball.y = HEIGHT // 2
        ball.dx = 4.2
        ball.dy = random.uniform(-2.8, 2.8)
    elif ball.x > WIDTH:
        player_score += 1
        ball.x = WIDTH // 2
        ball.y = HEIGHT // 2
        ball.dx = -4.2
        ball.dy = random.uniform(-2.8, 2.8)

    if player_score >= 5:
        winner = "PLAYER WINS!"
        game_over = True
    elif enemy_score >= 5:
        winner = "ENEMY WINS!"
        game_over = True

    display.set_pen(BLACK)
    display.rectangle(0, 0, WIDTH, HEIGHT)

    display.set_pen(GRAY)
    for y in range(0, HEIGHT, 10):
        display.rectangle(WIDTH // 2 - 2, y, 4, 5)

    player_paddle.draw()
    enemy_paddle.draw()
    ball.draw()

    display.set_pen(WHITE)
    display.text(f"Player: {player_score}", 10, 10, scale=1)
    display.text(f"Enemy: {enemy_score}", WIDTH - 80, 10, scale=1)
    display.text("A:Up B:Down", 10, HEIGHT - 15, scale=1)

    display.update()
    time.sleep(dt)

if winner:
    display.set_pen(BLACK)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(WHITE)
    display.text(winner, WIDTH // 2 - 40, HEIGHT // 2, scale=2)
    display.update()
    time.sleep(3)

print("Game over!")
