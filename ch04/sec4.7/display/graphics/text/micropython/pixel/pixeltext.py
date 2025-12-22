# Bitmap Font Renderer for Pimoroni Display Pack 2.0

import time
from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

# Init display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

# Init buttons
button_a = Button(12)
button_b = Button(13)

# 5x7 Bitmap Font Data
# Each character is 5 bytes, each byte represents a column
# Bit 0 = top pixel, Bit 6 = bottom pixel
# Format: binary representation where 1 = pixel on, 0 = pixel off

FONT_5X7 = {
    'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],  # A
    'B': [0x7F, 0x49, 0x49, 0x49, 0x36],  # B
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22],  # C
    'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],  # D
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],  # E
    'F': [0x7F, 0x09, 0x09, 0x09, 0x01],  # F
    'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],  # G
    'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],  # H
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],  # I
    'J': [0x20, 0x40, 0x41, 0x3F, 0x01],  # J
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41],  # K
    'L': [0x7F, 0x40, 0x40, 0x40, 0x40],  # L
    'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],  # M
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],  # N
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],  # O
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06],  # P
    'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],  # Q
    'R': [0x7F, 0x09, 0x19, 0x29, 0x46],  # R
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],  # S
    'T': [0x01, 0x01, 0x7F, 0x01, 0x01],  # T
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],  # U
    'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],  # V
    'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],  # W
    'X': [0x63, 0x14, 0x08, 0x14, 0x63],  # X
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07],  # Y
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],  # Z
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],  # 0
    '1': [0x00, 0x42, 0x7F, 0x40, 0x00],  # 1
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],  # 2
    '3': [0x21, 0x41, 0x45, 0x4B, 0x31],  # 3
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10],  # 4
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],  # 5
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],  # 6
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],  # 7
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],  # 8
    '9': [0x06, 0x49, 0x49, 0x29, 0x1E],  # 9
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],  # Space
    '.': [0x00, 0x60, 0x60, 0x00, 0x00],  # .
    ',': [0x00, 0x80, 0x60, 0x00, 0x00],  # ,
    '!': [0x00, 0x00, 0x5F, 0x00, 0x00],  # !
    '?': [0x02, 0x01, 0x51, 0x09, 0x06],  # ?
    '-': [0x08, 0x08, 0x08, 0x08, 0x08],  # -
    '+': [0x08, 0x08, 0x3E, 0x08, 0x08],  # +
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],  # :
}


class BitmapFont:    
    def __init__(self, display, font_data):
        self.display = display
        self.font_data = font_data
        self.char_width = 5
        self.char_height = 7
        self.spacing = 1
        self.scale = 1

    # 1. Look up the character's bitmap (5 bytes)
    # 2. Each byte represents a column of pixels
    # 3. Each bit in the byte represents a pixel (bit 0 = top, bit 6 = bottom)
    # 4. For each bit that's 1, draw a pixel (or scaled block)
    def draw_char(self, x, y, char, color):
        char_upper = char.upper()
        if char_upper not in self.font_data:
            return x  # Skip unknown characters
        
        bitmap = self.font_data[char_upper]
        
        # Set color
        self.display.set_pen(color)
        
        # Process each column (5 columns per character)
        for col in range(self.char_width):
            column_data = bitmap[col]
            
            # Process each row (7 rows per character)
            for row in range(self.char_height):
                # Check if this bit is set (pixel should be drawn)
                if (column_data >> row) & 1:
                    # Draw pixel or scaled block
                    if self.scale == 1:
                        self.display.pixel(x + col, y + row)
                    else:
                        # Draw scaled block
                        for sy in range(self.scale):
                            for sx in range(self.scale):
                                px = x + col * self.scale + sx
                                py = y + row * self.scale + sy
                                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                                    self.display.pixel(px, py)
        
        # Return x position for next character
        return x + (self.char_width + self.spacing) * self.scale
    
    def draw_text(self, x, y, text, color):
        current_x = x
        for char in text:
            current_x = self.draw_char(current_x, y, char, color)
        return current_x
    
    def measure_text(self, text):
        return len(text) * (self.char_width + self.spacing) * self.scale


def demo_basic_text():
    font = BitmapFont(display, FONT_5X7)
    
    BLACK = display.create_pen(0, 0, 0)
    WHITE = display.create_pen(255, 255, 255)
    CYAN = display.create_pen(0, 255, 255)
    YELLOW = display.create_pen(255, 255, 0)
    GREEN = display.create_pen(0, 255, 0)
    
    display.set_pen(BLACK)
    display.clear()
    
    # Scale 1 (normal size)
    font.scale = 1
    font.draw_text(5, 5, "SCALE 1X", WHITE)
    font.draw_text(5, 15, "ABCDEFGHIJKLM", CYAN)
    font.draw_text(5, 25, "NOPQRSTUVWXYZ", CYAN)
    font.draw_text(5, 35, "0123456789", YELLOW)
    
    # Scale 2 (double size)
    font.scale = 2
    font.draw_text(5, 50, "SCALE 2X", WHITE)
    font.draw_text(5, 65, "BITMAP!", GREEN)
    
    # Scale 3
    font.scale = 3
    font.draw_text(5, 95, "BIG!", YELLOW)
    
    font.scale = 1
    font.draw_text(5, HEIGHT - 10, "PRESS A", WHITE)
    
    display.update()
    
    while not button_a.read():
        time.sleep(0.1)


def demo_scrolling_text():
    font = BitmapFont(display, FONT_5X7)
    font.scale = 2
    
    BLACK = display.create_pen(0, 0, 0)
    RED = display.create_pen(255, 0, 0)
    GREEN = display.create_pen(0, 255, 0)
    BLUE = display.create_pen(0, 0, 255)
    WHITE = display.create_pen(255, 255, 255)
    
    colors = [RED, GREEN, BLUE, WHITE]
    color_idx = 0
    
    text = "BITMAP FONTS ARE PIXEL GRIDS!"
    text_width = font.measure_text(text)
    scroll_x = WIDTH
    
    while not button_b.read():
        display.set_pen(BLACK)
        display.clear()
        
        # Draw scrolling text
        font.draw_text(scroll_x, 50, text, colors[color_idx])
        
        # Instructions
        font.scale = 1
        font.draw_text(5, HEIGHT - 10, "PRESS B", WHITE)
        font.scale = 2
        
        display.update()
        
        # Update scroll position
        scroll_x -= 2
        if scroll_x < -text_width:
            scroll_x = WIDTH
            color_idx = (color_idx + 1) % len(colors)
        
        time.sleep(0.03)


def demo_rainbow_text():
    font = BitmapFont(display, FONT_5X7)
    font.scale = 2
    
    BLACK = display.create_pen(0, 0, 0)
    WHITE = display.create_pen(255, 255, 255)
    
    # Colours
    colors = [
        display.create_pen(255, 0, 0),    # Red
        display.create_pen(255, 128, 0),  # Orange
        display.create_pen(255, 255, 0),  # Yellow
        display.create_pen(0, 255, 0),    # Green
        display.create_pen(0, 255, 255),  # Cyan
        display.create_pen(0, 0, 255),    # Blue
        display.create_pen(255, 0, 255),  # Magenta
    ]
    
    text = "COLOURS!"
    offset = 0
    
    while not button_a.read() and not button_b.read():
        display.set_pen(BLACK)
        display.clear()
        
        # Draw each character in a different colour
        x = 20
        y = 50
        for i, char in enumerate(text):
            color_idx = (i + offset) % len(colors)
            x = font.draw_char(x, y, char, colors[color_idx])
        
        # Instructions
        font.scale = 1
        font.draw_text(5, HEIGHT - 10, "PRESS A OR B", WHITE)
        font.scale = 2
        
        display.update()
        offset += 1
        time.sleep(0.1)


def main():
    font = BitmapFont(display, FONT_5X7)
    
    BLACK = display.create_pen(0, 0, 0)
    WHITE = display.create_pen(255, 255, 255)
    CYAN = display.create_pen(0, 255, 255)
    GREEN = display.create_pen(0, 255, 0)
    
    display.set_pen(BLACK)
    display.clear()
    
    # Title
    font.scale = 2
    font.draw_text(10, 10, "BITMAP", CYAN)
    font.draw_text(10, 30, "FONTS", CYAN)
    
    # Menu
    font.scale = 1
    font.draw_text(5, 60, "HOW PIXEL FONTS WORK:", WHITE)
    font.draw_text(5, 70, "EACH CHARACTER IS A", WHITE)
    font.draw_text(5, 80, "GRID OF PIXELS STORED", WHITE)
    font.draw_text(5, 90, "AS BYTES. BITS=PIXELS!", WHITE)
    
    font.draw_text(5, 110, "A: BASIC DEMO", GREEN)
    font.draw_text(5, 120, "B: SCROLL+COLOURS", GREEN)
    
    display.update()
    
    while True:
        if button_a.read():
            demo_basic_text()
            time.sleep(0.3)
            main()
        elif button_b.read():
            # Choose demo
            demo_scrolling_text()
            time.sleep(0.3)
            demo_rainbow_text()
            time.sleep(0.3)
            main()
        
        time.sleep(0.1)

# Run
main()
