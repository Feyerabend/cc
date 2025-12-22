import time
import math
from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

# Init display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

W2 = WIDTH // 2
H2 = HEIGHT // 2

RED = display.create_pen(255, 0, 0)
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 0, 255)
CYAN = display.create_pen(0, 255, 255)
YELLOW = display.create_pen(255, 255, 0)
MAGENTA = display.create_pen(255, 0, 255)
ORANGE = display.create_pen(255, 128, 0)

# Init buttons
button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Character data - vector definitions
CHAR_DATA = {
    'A': [((0, 0), (2.5, 10)), ((2.5, 10), (5, 0)), ((1, 5), (4, 5))],
    'B': [((0, 0), (0, 10)), ((0, 10), (3, 10)), ((3, 10), (4, 9)), ((4, 9), (4, 6)), 
          ((4, 6), (3, 5)), ((3, 5), (4, 4)), ((4, 4), (4, 1)), ((4, 1), (3, 0)), 
          ((3, 0), (0, 0)), ((0, 5), (3, 5))],
    'C': [((5, 0), (1, 0)), ((1, 0), (0, 1)), ((0, 1), (0, 9)), ((0, 9), (1, 10)),
          ((1, 10), (5, 10))],
    'D': [((0, 0), (0, 10)), ((0, 10), (3, 10)), ((3, 10), (4, 9)), ((4, 9), (4, 1)),
          ((4, 1), (3, 0)), ((0, 0), (3, 0))],
    'E': [((5, 0), (0, 0)), ((0, 0), (0, 10)), ((0, 10), (5, 10)), ((0, 5), (3, 5))],
    'F': [((0, 0), (0, 10)), ((0, 10), (5, 10)), ((0, 5), (3, 5))],
    'G': [((5, 7), (5, 10)), ((5, 10), (1, 10)), ((1, 10), (0, 9)), ((0, 9), (0, 1)),
          ((0, 1), (1, 0)), ((1, 0), (5, 0)), ((5, 0), (5, 4)), ((3, 4), (5, 4))],
    'H': [((0, 0), (0, 10)), ((5, 0), (5, 10)), ((0, 5), (5, 5))],
    'I': [((2, 0), (2, 10)), ((0, 0), (4, 0)), ((0, 10), (4, 10))],
    'J': [((5, 10), (5, 1)), ((5, 1), (4, 0)), ((4, 0), (1, 0)), ((1, 0), (0, 1))],
    'K': [((0, 0), (0, 10)), ((5, 10), (0, 5)), ((0, 5), (5, 0))],
    'L': [((0, 10), (0, 0)), ((0, 0), (5, 0))],
    'M': [((0, 0), (0, 10)), ((0, 10), (2.5, 5)), ((2.5, 5), (5, 10)), ((5, 10), (5, 0))],
    'N': [((0, 0), (0, 10)), ((0, 10), (5, 0)), ((5, 0), (5, 10))],
    'O': [((0, 0), (5, 0)), ((5, 0), (5, 10)), ((5, 10), (0, 10)), ((0, 10), (0, 0))],
    'P': [((0, 0), (0, 10)), ((0, 10), (4, 10)), ((4, 10), (5, 9)), ((5, 9), (5, 6)),
          ((5, 6), (4, 5)), ((4, 5), (0, 5))],
    'Q': [((0, 0), (5, 0)), ((5, 0), (5, 10)), ((5, 10), (0, 10)), ((0, 10), (0, 0)),
          ((3, 3), (5, 0))],
    'R': [((0, 0), (0, 10)), ((0, 10), (4, 10)), ((4, 10), (5, 9)), ((5, 9), (5, 6)),
          ((5, 6), (4, 5)), ((4, 5), (0, 5)), ((0, 5), (5, 0))],
    'S': [((5, 10), (1, 10)), ((1, 10), (0, 9)), ((0, 9), (1, 5)), ((1, 5), (4, 5)), 
          ((4, 5), (5, 1)), ((5, 1), (4, 0)), ((4, 0), (0, 0))],
    'T': [((2.5, 0), (2.5, 10)), ((0, 10), (5, 10))],
    'U': [((0, 10), (0, 1)), ((0, 1), (1, 0)), ((1, 0), (4, 0)), ((4, 0), (5, 1)),
          ((5, 1), (5, 10))],
    'V': [((0, 10), (2.5, 0)), ((2.5, 0), (5, 10))],
    'W': [((0, 10), (1.5, 0)), ((1.5, 0), (2.5, 5)), ((2.5, 5), (3.5, 0)), ((3.5, 0), (5, 10))],
    'X': [((0, 10), (5, 0)), ((5, 10), (0, 0))],
    'Y': [((0, 10), (2.5, 5)), ((2.5, 5), (5, 10)), ((2.5, 5), (2.5, 0))],
    'Z': [((0, 10), (5, 10)), ((5, 10), (0, 0)), ((0, 0), (5, 0))],
    '.': [((1, 0), (1, 1))],
    ',': [((1, 0), (1, 1)), ((1, 0), (0.5, -0.5))],
    '!': [((4, 10), (4, 3)), ((4, 1), (4, 0))],
    '?': [((1, 7), (2.5, 10)), ((2.5, 10), (5, 7)), ((5, 7), (4, 5)), ((4, 5), (2.5, 3)), ((2.5, 3), (2.5, 1))],
    '0': [((1, 0), (4, 0)), ((4, 0), (5, 1)), ((5, 1), (5, 9)), ((5, 9), (4, 10)),
          ((4, 10), (1, 10)), ((1, 10), (0, 9)), ((0, 9), (0, 1)), ((0, 1), (1, 0)),
          ((5, 10), (0, 0))],
    '1': [((2.5, 0), (2.5, 10))],
    '2': [((0, 9), (1, 10)), ((1, 10), (4, 10)), ((4, 10), (5, 9)), ((5, 9), (5, 5)), 
          ((5, 5), (0, 0)), ((0, 0), (5, 0))],
    '3': [((0, 10), (5, 10)), ((5, 10), (3, 5)), ((3, 5), (5, 0)), ((0, 0), (5, 0))],
    '4': [((4, 10), (4, 0)), ((0, 5), (5, 5)), ((4, 10), (0, 5))],
    '5': [((5, 10), (0, 10)), ((0, 10), (0, 5)), ((0, 5), (4, 5)), ((4, 5), (5, 4)),
          ((5, 4), (5, 0)), ((5, 0), (0, 0))],
    '6': [((5, 10), (0, 10)), ((0, 10), (0, 0)), ((0, 0), (5, 0)), ((5, 0), (5, 4)), 
          ((5, 4), (4, 5)), ((4, 5), (0, 5))],
    '7': [((0, 10), (5, 10)), ((5, 10), (2, 0))],
    '8': [((1, 5), (4, 5)), ((1, 10), (4, 10)), ((4, 10), (5, 9)), ((5, 9), (5, 1)), 
          ((5, 1), (4, 0)), ((4, 0), (1, 0)), ((1, 0), (0, 1)), ((0, 1), (0, 9)), 
          ((0, 9), (1, 10))],
    '9': [((5, 0), (5, 10)), ((5, 10), (0, 10)), ((0, 10), (0, 6)), ((0, 6), (1, 5)), 
          ((1, 5), (5, 5))],
    ' ': []
}

class AffineTransform:    
    def __init__(self):
        self.reset()
    
    # id matrix
    def reset(self):
        self.matrix = [1, 0, 0, 1, 0, 0]  # [a, b, c, d, tx, ty]
    
    def rotate(self, angle_deg):
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        a, b, c, d, tx, ty = self.matrix
        self.matrix = [
            a * cos_a + c * sin_a,
            b * cos_a + d * sin_a,
            a * (-sin_a) + c * cos_a,
            b * (-sin_a) + d * cos_a,
            tx, ty
        ]
    
    def scale(self, sx, sy=None):
        if sy is None:
            sy = sx
        a, b, c, d, tx, ty = self.matrix
        self.matrix = [a * sx, b * sx, c * sy, d * sy, tx, ty]
    
    def translate(self, tx, ty):
        a, b, c, d, curr_tx, curr_ty = self.matrix
        self.matrix = [
            a, b, c, d,
            a * tx + c * ty + curr_tx,
            b * tx + d * ty + curr_ty
        ]
    
    def shear(self, shx, shy=0):
        a, b, c, d, tx, ty = self.matrix
        self.matrix = [
            a + b * shx, b + a * shy,
            c + d * shx, d + c * shy,
            tx, ty
        ]
    
    def transform_point(self, x, y):
        a, b, c, d, tx, ty = self.matrix
        new_x = a * x + c * y + tx
        new_y = b * x + d * y + ty
        return int(new_x), int(new_y)


class VectorTextRenderer:
    def __init__(self, display):
        self.display = display
        self.char_width = 6
        self.char_height = 11
        self.spacing = 2
        self.line_thickness = 1
    
    def draw_line_bresenham(self, x1, y1, x2, y2, color):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            if 0 <= x1 < WIDTH and 0 <= y1 < HEIGHT:
                self.display.pixel(x1, y1)
                # Add thickness
                for i in range(1, self.line_thickness):
                    if 0 <= x1 + i < WIDTH and 0 <= y1 < HEIGHT:
                        self.display.pixel(x1 + i, y1)
            
            if x1 == x2 and y1 == y2:
                break
            
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    def render_char(self, char, x_offset, y_offset, transform=None, color=None):
        if color:
            self.display.set_pen(color)
        
        char_upper = char.upper()
        if char_upper not in CHAR_DATA:
            return
        
        for line in CHAR_DATA[char_upper]:
            (x1, y1), (x2, y2) = line
            
            if transform:
                # Add character offset to local coordinates,
                # flip Y for screen coords, then transform
                # Character data has Y=0 at bottom, Y=10 at top
                # We flip it so Y increases downward for screen coordinates
                tx1, ty1 = transform.transform_point(x1 + x_offset, 10 - y1)
                tx2, ty2 = transform.transform_point(x2 + x_offset, 10 - y2)
            else:
                # Simple translation only - Y axis flipped for screen
                tx1, ty1 = int(x_offset + x1), int(y_offset - y1)
                tx2, ty2 = int(x_offset + x2), int(y_offset - y2)
            
            self.draw_line_bresenham(tx1, ty1, tx2, ty2, color)
    
    def render_text(self, text, x, y, transform=None, color=None):
        if transform:
            # Work in local coordinate space when using transforms
            current_x = 0
            for char in text:
                if char == ' ':
                    current_x += self.char_width + self.spacing
                    continue
                
                self.render_char(char, current_x, 0, transform, color)
                current_x += self.char_width + self.spacing
        else:
            # Simple case without transforms
            current_x = x
            for char in text:
                if char == ' ':
                    current_x += self.char_width + self.spacing
                    continue
                
                self.render_char(char, current_x, y, None, color)
                current_x += self.char_width + self.spacing
    
    # Render text with rotation around a center point
    def render_text_transformed(self, text, center_x, center_y, angle=0, scale=1.0, color=None):
        # Calculate text dimensions for centering (in local space before scaling)
        text_width = len(text) * (self.char_width + self.spacing)
        text_height = self.char_height
        
        # Create transform that rotates around text center, then moves to position
        transform = AffineTransform()
        
        # Scale first
        transform.scale(scale, scale)
        # Rotate (around origin)
        transform.rotate(angle)
        
        # Now translate to final position, accounting for centering
        # After scaling, the text dimensions are scaled too
        scaled_width = text_width * scale
        scaled_height = text_height * scale
        transform.translate(center_x - scaled_width / 2, center_y - scaled_height / 2)
        
        self.render_text(text, 0, 0, transform, color)


def demo_rotation():
    renderer = VectorTextRenderer(display)
    renderer.line_thickness = 2
    
    angle = 0
    
    while not button_a.read():
        display.set_pen(BLACK)
        display.clear()
        
        display.set_pen(CYAN)
        renderer.render_text_transformed(
            "PICO", 
            W2, H2 - 15,
            angle, 1.5, CYAN
        )

        # counter rotating text
        display.set_pen(RED)
        renderer.render_text_transformed(
            "DISPLAY", 
            W2, H2 + 15,
            -angle * 0.7, 1.2, RED
        )
        
        display.set_pen(GREEN)
        renderer.render_text("PRESS A", 5, HEIGHT - 5, color=GREEN)
        
        display.update()
        angle += 2
        time.sleep(0.03)


def demo_multiple_styles():
    renderer = VectorTextRenderer(display)
    
    display.set_pen(BLACK)
    display.clear()
    
    # Normal text
    display.set_pen(WHITE)
    renderer.render_text("NORMAL", 10, 25, color=WHITE)
    
    # Rotated text
    display.set_pen(YELLOW)
    renderer.render_text_transformed("ROTATED", W2, 50, 25, 1.0, YELLOW)
    
    # Scaled text
    display.set_pen(MAGENTA)
    renderer.render_text_transformed("BIG", W2, 85, 0, 1.8, MAGENTA)
    
    # Small rotated text
    display.set_pen(ORANGE)
    renderer.render_text_transformed("TINY", W2, 115, -15, 0.7, ORANGE)
    
    display.set_pen(WHITE)
    renderer.line_thickness = 1
    renderer.render_text("PRESS B", 5, HEIGHT - 5, color=WHITE)
    
    display.update()
    
    while not button_b.read():
        time.sleep(0.1)


def demo_spiral_text():
    renderer = VectorTextRenderer(display)
    renderer.line_thickness = 2
    
    BLACK = display.create_pen(0, 0, 0)
    
    colors = [
        display.create_pen(255, 0, 0),
        display.create_pen(255, 128, 0),
        display.create_pen(255, 255, 0),
        display.create_pen(0, 255, 0),
        display.create_pen(0, 255, 255),
        display.create_pen(0, 0, 255),
        display.create_pen(255, 0, 255),
    ]
    
    text = "HELLO"
    center_x, center_y = W2, H2
    offset = 0
    
    while not button_x.read():
        display.set_pen(BLACK)
        display.clear()
        
        for i in range(7):
            angle = (offset + i * 51.4) % 360
            radius = 30 + i * 3
            
            x = center_x + int(radius * math.cos(math.radians(angle)))
            y = center_y + int(radius * math.sin(math.radians(angle)))
            
            display.set_pen(colors[i])
            renderer.render_text_transformed(
                text, x, y, angle + 90, 0.8 + i * 0.05, colors[i]
            )
        
        display.update()
        offset += 3
        time.sleep(0.05)


def main():
    renderer = VectorTextRenderer(display)
    
    colors = [CYAN, YELLOW, MAGENTA, WHITE]
    color_index = 0
    
    # Calculate text width for scrolling
    text = "VECTOR TEXT"
    text_width = len(text) * (renderer.char_width + renderer.spacing) * 1.5
    scroll_x = WIDTH
    
    while True:
        display.set_pen(BLACK)
        display.clear()
        
        # Scrolling title with color changes
        renderer.line_thickness = 2
        renderer.render_text_transformed(text, scroll_x, 30, 0, 1.5, colors[color_index])
        
        # Static subtitle
        renderer.line_thickness = 1
        display.set_pen(GREEN)
        renderer.render_text("DEMO", W2 - 20, 55, color=GREEN)
        
        # Menu options
        display.set_pen(WHITE)
        renderer.render_text("A: ROTATION", 10, 80, color=WHITE)
        renderer.render_text("B: STYLES", 10, 95, color=WHITE)
        renderer.render_text("X: SPIRAL", 10, 110, color=WHITE)
        renderer.render_text("Y: EXIT", 10, 125, color=WHITE)
        
        display.update()
        
        # Update scroll position
        scroll_x -= 3
        if scroll_x < -text_width:
            scroll_x = WIDTH
            color_index = (color_index + 1) % len(colors)
        
        # Check for button presses
        if button_a.read():
            demo_rotation()
            scroll_x = WIDTH  # Reset scroll
            color_index = 0
            
        elif button_b.read():
            demo_multiple_styles()
            scroll_x = WIDTH
            color_index = 0
            
        elif button_x.read():
            demo_spiral_text()
            scroll_x = WIDTH
            color_index = 0
            
        elif button_y.read():
            display.set_pen(BLACK)
            display.clear()
            display.set_pen(WHITE)
            renderer.render_text("GOODBYE!", W2 - 40, H2, color=WHITE)
            display.update()
            break
        
        time.sleep(0.03)

# Run the demo
main()
