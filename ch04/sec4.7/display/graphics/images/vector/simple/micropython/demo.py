"""
Vector Graphics Demo for Pimoroni Display Pack 2.0
"""

import time
import math
from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

# Init display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

# Init buttons
button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Colors
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 0, 255)
CYAN = display.create_pen(0, 255, 255)
YELLOW = display.create_pen(255, 255, 0)
MAGENTA = display.create_pen(255, 0, 255)

# Vector and Matrix classes
class Vec2:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

class Matrix3:    
    def __init__(self):
        # Identity matrix by default
        self.m = [[1.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0],
                  [0.0, 0.0, 1.0]]
    
    @staticmethod
    def identity():
        return Matrix3()
    
    @staticmethod
    def translate(x, y):
        m = Matrix3()
        m.m[0][2] = x
        m.m[1][2] = y
        return m
    
    @staticmethod
    def rotate(angle):
        m = Matrix3()
        c = math.cos(angle)
        s = math.sin(angle)
        m.m[0][0] = c
        m.m[0][1] = -s
        m.m[1][0] = s
        m.m[1][1] = c
        return m
    
    @staticmethod
    def scale(sx, sy):
        m = Matrix3()
        m.m[0][0] = sx
        m.m[1][1] = sy
        return m
    
    def multiply(self, other):
        """
        CRITICAL: Matrix multiplication order matters!
        To transform: Scale -> Rotate -> Translate
        Result = Translate * Rotate * Scale
        """
        result = Matrix3()
        for i in range(3):
            for j in range(3):
                result.m[i][j] = 0.0
                for k in range(3):
                    result.m[i][j] += self.m[i][k] * other.m[k][j]
        return result
    
    def transform_point(self, point):
        x = self.m[0][0] * point.x + self.m[0][1] * point.y + self.m[0][2]
        y = self.m[1][0] * point.x + self.m[1][1] * point.y + self.m[1][2]
        return Vec2(x, y)

class Shape:
    def __init__(self, vertices, color):
        self.vertices = [Vec2(v[0], v[1]) for v in vertices]
        self.color = color
    
    def draw(self, transform):
        if len(self.vertices) < 2:
            return
        
        # Transform all vertices
        transformed = [transform.transform_point(v) for v in self.vertices]
        
        # Draw edges
        display.set_pen(self.color)
        for i in range(len(transformed)):
            p0 = transformed[i]
            p1 = transformed[(i + 1) % len(transformed)]
            draw_line(int(p0.x), int(p0.y), int(p1.x), int(p1.y))

def draw_line(x0, y0, x1, y1):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        if 0 <= x0 < WIDTH and 0 <= y0 < HEIGHT:
            display.pixel(x0, y0)
        
        if x0 == x1 and y0 == y1:
            break
        
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

# Define shapes
shapes = [
    # Triangle
    Shape([(0, -30), (26, 15), (-26, 15)], CYAN),
    
    # Square
    Shape([(-25, -25), (25, -25), (25, 25), (-25, 25)], YELLOW),
    
    # Pentagon
    Shape([(0, -30), (28, -9), (17, 24), (-17, 24), (-28, -9)], MAGENTA),
    
    # Hexagon
    Shape([(0, -30), (26, -15), (26, 15), (0, 30), (-26, 15), (-26, -15)], GREEN),
    
    # Star
    Shape([(0, -30), (7, -10), (28, -10), (11, 5), (18, 25),
           (0, 15), (-18, 25), (-11, 5), (-28, -10), (-7, -10)], RED)
]

# Demo state
current_shape = 0
rotation = 0.0
scale = 1.0
translation = Vec2(WIDTH // 2, HEIGHT // 2)
auto_rotate = True

def draw_ui():
    display.set_pen(WHITE)
    
    # Shape info
    display.text(f"Shape: {current_shape + 1}/{len(shapes)}", 10, 10, scale=1)
    
    # Rotation in degrees
    deg = math.degrees(rotation) % 360
    display.text(f"Rot: {deg:.1f}", 10, 20, scale=1)
    
    # Scale
    display.text(f"Scale: {scale:.2f}", 10, 30, scale=1)
    
    # Auto-rotate status
    display.text(f"Auto: {'ON' if auto_rotate else 'OFF'}", 10, 40, scale=1)
    
    # Instructions
    display.set_pen(YELLOW)
    display.text("A:Shape B:Auto X:+ Y:-", 10, HEIGHT - 20, scale=1)

def draw_axes(transform):
    origin = Vec2(0, 0)
    x_axis = Vec2(40, 0)
    y_axis = Vec2(0, 40)
    
    o = transform.transform_point(origin)
    x = transform.transform_point(x_axis)
    y = transform.transform_point(y_axis)
    
    # X-axis in red
    display.set_pen(RED)
    draw_line(int(o.x), int(o.y), int(x.x), int(x.y))
    
    # Y-axis in green
    display.set_pen(GREEN)
    draw_line(int(o.x), int(o.y), int(y.x), int(y.y))

# Main loop
print("Vector Graphics Demo Started")
last_a = False
last_b = False
last_x = False
last_y = False

while True:
    # Handle button presses with edge detection
    a_pressed = button_a.is_pressed
    b_pressed = button_b.is_pressed
    x_pressed = button_x.is_pressed
    y_pressed = button_y.is_pressed
    
    if a_pressed and not last_a:
        current_shape = (current_shape + 1) % len(shapes)
    
    if b_pressed and not last_b:
        auto_rotate = not auto_rotate
    
    if x_pressed and not last_x:
        scale += 0.2
        if scale > 3.0:
            scale = 3.0
    
    if y_pressed and not last_y:
        scale -= 0.2
        if scale < 0.2:
            scale = 0.2
    
    last_a = a_pressed
    last_b = b_pressed
    last_x = x_pressed
    last_y = y_pressed
    
    # Update rotation
    if auto_rotate:
        rotation += 0.02
        if rotation > 2 * math.pi:
            rotation -= 2 * math.pi
    
    # Clear screen
    display.set_pen(BLACK)
    display.clear()
    
    # IMPORTANT: Transformation composition order!
    # We want to: scale the shape, rotate it, then move it to position
    # Matrix multiplication is right-to-left, so: T * R * S
    m_scale = Matrix3.scale(scale, scale)
    m_rotate = Matrix3.rotate(rotation)
    m_translate = Matrix3.translate(translation.x, translation.y)
    
    # Compose transformations: first apply scale, then rotation, then translation
    # In matrix math: result = T * (R * S)
    temp = m_rotate.multiply(m_scale)
    transform = m_translate.multiply(temp)
    
    # Draw coordinate axes (translation only)
    axis_transform = Matrix3.translate(translation.x, translation.y)
    draw_axes(axis_transform)
    
    # Draw the current shape with composed transformation
    shapes[current_shape].draw(transform)
    
    # Draw UI overlay
    draw_ui()
    
    # Update display
    display.update()
    
    # Frame delay (~60 FPS)
    time.sleep(0.016)
