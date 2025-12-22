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

class Snake:
    def __init__(self):
        self.segments = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = (1, 0)
        self.speed = 5
        self.grow = False

    def update(self, dt):
        head_x, head_y = self.segments[0]
        dx, dy = self.direction
        new_head = (head_x + dx * self.speed, head_y + dy * self.speed)

        if read_button(button_a) and self.direction != (0, 1):
            self.direction = (0, -1)
        elif read_button(button_b) and self.direction != (0, -1):
            self.direction = (0, 1)
        elif read_button(button_x) and self.direction != (1, 0):
            self.direction = (-1, 0)
        elif read_button(button_y) and self.direction != (-1, 0):
            self.direction = (1, 0)

        self.segments.insert(0, new_head)
        if not self.grow:
            self.segments.pop()
        else:
            self.grow = False

    def check_collision(self):
        head = self.segments[0]
        if head[0] < 0 or head[0] >= WIDTH or head[1] < 0 or head[1] >= HEIGHT:
            return True
        if head in self.segments[1:]:
            return True
        return False

    def eat(self, food):
        head = self.segments[0]
        if abs(head[0] - food.x) < 10 and abs(head[1] - food.y) < 10:
            self.grow = True
            return True
        return False

    def draw(self):
        display.set_pen(GREEN)
        for segment in self.segments:
            display.rectangle(int(segment[0] - 5), int(segment[1] - 5), 10, 10)

class Food:
    def __init__(self):
        self.x = random.randint(10, WIDTH - 10)
        self.y = random.randint(10, HEIGHT - 10)

    def draw(self):
        display.set_pen(RED)
        display.circle(int(self.x), int(self.y), 5)

snake = Snake()
food = Food()
score = 0
game_over = False
clock = 0

while not game_over:
    dt = 1/15
    clock += 1

    snake.update(dt)

    if snake.check_collision():
        game_over = True

    if snake.eat(food):
        score += 1
        food = Food()

    display.set_pen(BLACK)
    display.rectangle(0, 0, WIDTH, HEIGHT)

    snake.draw()
    food.draw()

    display.set_pen(WHITE)
    display.text(f"Score: {score}", 10, 10, scale=1)
    display.text("A:Up B:Down X:Left Y:Right", 10, HEIGHT - 15, scale=1)

    display.update()
    time.sleep(dt)

display.set_pen(BLACK)
display.rectangle(0, 0, WIDTH, HEIGHT)
display.set_pen(WHITE)
display.text("GAME OVER", WIDTH // 2 - 40, HEIGHT // 2 - 10, scale=2)
display.text(f"Score: {score}", WIDTH // 2 - 40, HEIGHT // 2 + 10, scale=2)
display.update()
time.sleep(3)

print("Game over!")
