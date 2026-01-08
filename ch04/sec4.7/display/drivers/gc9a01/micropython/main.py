"""
GC9A01 Display Driver for Raspberry Pi Pico 2/2W
240x240 Round LCD Display Driver with Hardware SPI
"""

from machine import Pin, SPI
from micropython import const
import framebuf
import time

# GC9A01 Commands
_SWRESET = const(0x01)
_SLPOUT = const(0x11)
_INVOFF = const(0x20)
_INVON = const(0x21)
_DISPOFF = const(0x28)
_DISPON = const(0x29)
_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)
_MADCTL = const(0x36)
_COLMOD = const(0x3A)
_TEON = const(0x35)

# MADCTL bits
_MADCTL_MH = const(0x04)
_MADCTL_RGB = const(0x00)
_MADCTL_BGR = const(0x08)
_MADCTL_ML = const(0x10)
_MADCTL_MV = const(0x20)
_MADCTL_MX = const(0x40)
_MADCTL_MY = const(0x80)


class GC9A01:
    """
    GC9A01 Display Driver
    
    Example usage:
        # Hardware SPI setup
        spi = SPI(0, baudrate=40000000, polarity=0, phase=0, 
                  sck=Pin(2), mosi=Pin(3))
        
        # Create display instance
        display = GC9A01(spi, dc=Pin(4), cs=Pin(5), rst=Pin(6), bl=Pin(7))
        
        # Fill screen with color
        display.fill(0xF800)  # Red in RGB565
        
        # Draw pixel
        display.pixel(120, 120, 0x07E0)  # Green
        
        # Draw text
        display.text("Hello!", 100, 120, 0xFFFF)
        
        # Show changes
        display.show()
    """
    
    def __init__(self, spi, dc, cs, rst=None, bl=None, width=240, height=240, rotation=0):
        """
        Initialize GC9A01 display
        
        Args:
            spi: SPI bus instance
            dc: Data/Command pin
            cs: Chip Select pin
            rst: Reset pin (optional)
            bl: Backlight pin (optional)
            width: Display width (default 240)
            height: Display height (default 240)
            rotation: Rotation 0-3 (default 0)
        """
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.rst = rst
        self.bl = bl
        self.width = width
        self.height = height
        
        # Configure pins
        self.dc.init(Pin.OUT, value=0)
        self.cs.init(Pin.OUT, value=1)
        
        if self.rst:
            self.rst.init(Pin.OUT, value=1)
        
        if self.bl:
            self.bl.init(Pin.OUT, value=1)
        
        # Create framebuffer
        self.buffer = bytearray(width * height * 2)  # RGB565 = 2 bytes per pixel
        self.fbuf = framebuf.FrameBuffer(self.buffer, width, height, framebuf.RGB565)
        
        # Initialize display
        self._init_display()
        self.set_rotation(rotation)
        
    def _write_cmd(self, cmd):
        """Send command byte"""
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
    
    def _write_data(self, data):
        """Send data byte(s)"""
        self.cs(0)
        self.dc(1)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs(1)
    
    def _init_display(self):
        """Initialize display with configuration sequence"""
        # Hardware reset
        if self.rst:
            self.rst(1)
            time.sleep_ms(5)
            self.rst(0)
            time.sleep_ms(20)
            self.rst(1)
            time.sleep_ms(150)
        
        # Software reset
        self._write_cmd(_SWRESET)
        time.sleep_ms(120)
        
        # Inter Register Enable1
        self._write_cmd(0xFE)
        self._write_cmd(0xEF)
        
        # Inter Register Enable2
        self._write_cmd(0xEB)
        self._write_data(0x14)
        
        # Display Function Control
        self._write_cmd(0x84)
        self._write_data(0x40)
        
        self._write_cmd(0x85)
        self._write_data(0xFF)
        
        self._write_cmd(0x86)
        self._write_data(0xFF)
        
        self._write_cmd(0x87)
        self._write_data(0xFF)
        
        self._write_cmd(0x88)
        self._write_data(0x0A)
        
        self._write_cmd(0x89)
        self._write_data(0x21)
        
        self._write_cmd(0x8A)
        self._write_data(0x00)
        
        self._write_cmd(0x8B)
        self._write_data(0x80)
        
        self._write_cmd(0x8C)
        self._write_data(0x01)
        
        self._write_cmd(0x8D)
        self._write_data(0x01)
        
        self._write_cmd(0x8E)
        self._write_data(0xFF)
        
        self._write_cmd(0x8F)
        self._write_data(0xFF)
        
        # Power Control
        self._write_cmd(0xB6)
        self._write_data(0x00)
        self._write_data(0x00)
        
        # Pixel Format Set (16-bit color)
        self._write_cmd(_COLMOD)
        self._write_data(0x05)
        
        # Gamma correction
        self._write_cmd(0xF0)
        self._write_data(bytearray([0x45, 0x09, 0x08, 0x08, 0x26, 0x2A]))
        
        self._write_cmd(0xF1)
        self._write_data(bytearray([0x43, 0x70, 0x72, 0x36, 0x37, 0x6F]))
        
        self._write_cmd(0xF2)
        self._write_data(bytearray([0x45, 0x09, 0x08, 0x08, 0x26, 0x2A]))
        
        self._write_cmd(0xF3)
        self._write_data(bytearray([0x43, 0x70, 0x72, 0x36, 0x37, 0x6F]))
        
        # Tearing Effect Line ON
        self._write_cmd(_TEON)
        self._write_data(0x00)
        
        # Sleep Out
        self._write_cmd(_SLPOUT)
        time.sleep_ms(120)
        
        # Display ON
        self._write_cmd(_DISPON)
        time.sleep_ms(20)
    
    def set_rotation(self, rotation):
        """Set display rotation (0-3)"""
        rotation = rotation % 4
        self._write_cmd(_MADCTL)
        
        if rotation == 0:
            self._write_data(_MADCTL_MX | _MADCTL_BGR)
        elif rotation == 1:
            self._write_data(_MADCTL_MV | _MADCTL_BGR)
        elif rotation == 2:
            self._write_data(_MADCTL_MY | _MADCTL_BGR)
        elif rotation == 3:
            self._write_data(_MADCTL_MX | _MADCTL_MY | _MADCTL_MV | _MADCTL_BGR)
    
    def set_window(self, x0, y0, x1, y1):
        """Set active drawing window"""
        # Column address
        self._write_cmd(_CASET)
        self._write_data(bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        
        # Row address
        self._write_cmd(_RASET)
        self._write_data(bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        
        # Write to RAM
        self._write_cmd(_RAMWR)
    
    def show(self):
        """Write framebuffer to display"""
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)
    
    def fill(self, color):
        """Fill entire display with color (RGB565)"""
        self.fbuf.fill(color)
    
    def pixel(self, x, y, color):
        """Draw a single pixel"""
        self.fbuf.pixel(x, y, color)
    
    def hline(self, x, y, w, color):
        """Draw horizontal line"""
        self.fbuf.hline(x, y, w, color)
    
    def vline(self, x, y, h, color):
        """Draw vertical line"""
        self.fbuf.vline(x, y, h, color)
    
    def line(self, x0, y0, x1, y1, color):
        """Draw line"""
        self.fbuf.line(x0, y0, x1, y1, color)
    
    def rect(self, x, y, w, h, color, fill=False):
        """Draw rectangle"""
        if fill:
            self.fbuf.fill_rect(x, y, w, h, color)
        else:
            self.fbuf.rect(x, y, w, h, color)
    
    def circle(self, x, y, r, color):
        """Draw circle outline"""
        f = 1 - r
        dx = 0
        dy = -2 * r
        px = 0
        py = r
        
        self.pixel(x, y + r, color)
        self.pixel(x, y - r, color)
        self.pixel(x + r, y, color)
        self.pixel(x - r, y, color)
        
        while px < py:
            if f >= 0:
                py -= 1
                dy += 2
                f += dy
            px += 1
            dx += 2
            f += dx + 1
            
            self.pixel(x + px, y + py, color)
            self.pixel(x - px, y + py, color)
            self.pixel(x + px, y - py, color)
            self.pixel(x - px, y - py, color)
            self.pixel(x + py, y + px, color)
            self.pixel(x - py, y + px, color)
            self.pixel(x + py, y - px, color)
            self.pixel(x - py, y - px, color)
    
    def fill_circle(self, x, y, r, color):
        """Draw filled circle"""
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(x - dx, y + dy, 2 * dx + 1, color)
    
    def text(self, text, x, y, color):
        """Draw text (8x8 font)"""
        self.fbuf.text(text, x, y, color)
    
    def backlight(self, state):
        """Control backlight (if connected)"""
        if self.bl:
            self.bl(state)
    
    def invert(self, state):
        """Invert display colors"""
        self._write_cmd(_INVON if state else _INVOFF)
    
    def power(self, state):
        """Turn display on/off"""
        self._write_cmd(_DISPON if state else _DISPOFF)
    
    @staticmethod
    def rgb(r, g, b):
        """Convert RGB888 to RGB565"""
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


# Example usage and demo
def demo():
    """Run a simple demo"""
    from machine import SPI, Pin
    
    # Initialize SPI and display
    # Adjust pins according to your wiring
    spi = SPI(0, baudrate=40000000, polarity=0, phase=0,
              sck=Pin(2), mosi=Pin(3))
    
    display = GC9A01(spi, dc=Pin(4), cs=Pin(5), rst=Pin(6), bl=Pin(7))
    
    # Define colors
    BLACK = 0x0000
    RED = 0xF800
    GREEN = 0x07E0
    BLUE = 0x001F
    WHITE = 0xFFFF
    YELLOW = 0xFFE0
    CYAN = 0x07FF
    MAGENTA = 0xF81F
    
    # Fill screen
    display.fill(BLACK)
    display.show()
    time.sleep(1)
    
    # Draw some shapes
    display.fill(BLUE)
    display.fill_circle(120, 120, 100, RED)
    display.fill_circle(120, 120, 70, GREEN)
    display.text("GC9A01", 85, 115, WHITE)
    display.text("Pico 2", 90, 125, WHITE)
    display.show()
    
    print("Demo complete!")


if __name__ == "__main__":
    demo()
