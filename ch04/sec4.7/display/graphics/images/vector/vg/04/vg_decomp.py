"""
MicroPython VGF Decompressor and Renderer
For RPi Pico with Pimoroni Display Pack 2.0 (320x240)
"""

import struct
from machine import SPI, Pin
import gc

class VGFReader:
    def __init__(self, filename):
        self.f = open(filename, 'rb')
        self._read_header()
    
    def _read_header(self):
        magic = self.f.read(4)
        if magic != b'VGF1':
            raise ValueError("Invalid VGF file")
        
        self.width, self.height = struct.unpack('<HH', self.f.read(4))
        
        # Read color palette
        num_colors = struct.unpack('<B', self.f.read(1))[0]
        self.colors = []
        for _ in range(num_colors):
            r, g, b = struct.unpack('<BBB', self.f.read(3))
            # Convert to RGB565 for display
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            self.colors.append(rgb565)
        
        self.num_shapes = struct.unpack('<H', self.f.read(2))[0]
        self.current_shape = 0
    
    def read_shape(self):
        if self.current_shape >= self.num_shapes:
            return None
        
        shape_type = struct.unpack('<B', self.f.read(1))[0]
        fill_idx = struct.unpack('<B', self.f.read(1))[0]
        stroke_idx = struct.unpack('<B', self.f.read(1))[0]
        stroke_width = struct.unpack('<B', self.f.read(1))[0] / 10.0
        
        num_points = struct.unpack('<H', self.f.read(2))[0]
        
        # Read path (streaming to save memory)
        path = bytearray(num_points * 4)  # Pre-allocate
        path_view = memoryview(path)
        
        if num_points > 0:
            # First point (absolute)
            x, y = struct.unpack('<HH', self.f.read(4))
            struct.pack_into('<HH', path_view, 0, x, y)
            
            # Remaining points (delta encoded)
            for i in range(1, num_points):
                dx = struct.unpack('<b', self.f.read(1))[0]
                if dx == -128:  # Escape sequence
                    dx, dy = struct.unpack('<hh', self.f.read(4))
                else:
                    dy = struct.unpack('<b', self.f.read(1))[0]
                
                x += dx
                y += dy
                struct.pack_into('<HH', path_view, i * 4, x, y)
        
        self.current_shape += 1
        
        return {
            'type': shape_type,
            'fill': self.colors[fill_idx] if fill_idx != 255 else None,
            'stroke': self.colors[stroke_idx] if stroke_idx != 255 else None,
            'stroke_width': stroke_width,
            'path': path_view,
            'num_points': num_points
        }
    
    def close(self):
        self.f.close()


# Simple renderer for Pimoroni Display Pack 2.0
# 320x240 resolution
# change to driver
class SimpleRenderer:
    def __init__(self, display):
        self.display = display
    
    def draw_path(self, shape):
        path = shape['path']
        num_points = shape['num_points']
        
        if num_points < 2:
            return
        
        # Fill (simple scanline fill for closed paths)
        if shape['fill'] is not None:
            self._fill_path(path, num_points, shape['fill'])
        
        # Stroke (draw lines between points)
        if shape['stroke'] is not None:
            color = shape['stroke']
            for i in range(num_points - 1):
                x1, y1 = struct.unpack_from('<HH', path, i * 4)
                x2, y2 = struct.unpack_from('<HH', path, (i + 1) * 4)
                self.display.line(x1, y1, x2, y2, color)
    
    # scanline fill algorithm
    def _fill_path(self, path, num_points, color):
        # Get bounding box
        min_y = 240
        max_y = 0
        
        for i in range(num_points):
            _, y = struct.unpack_from('<HH', path, i * 4)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
        
        # Scanline fill
        for y in range(min_y, max_y + 1):
            intersections = []
            
            # Find intersections with scanline
            for i in range(num_points):
                x1, y1 = struct.unpack_from('<HH', path, i * 4)
                x2, y2 = struct.unpack_from('<HH', path, ((i + 1) % num_points) * 4)
                
                if (y1 <= y < y2) or (y2 <= y < y1):
                    # Line intersects scanline
                    if y2 != y1:
                        x = x1 + (y - y1) * (x2 - x1) // (y2 - y1)
                        intersections.append(x)
            
            # Sort and fill between pairs
            intersections.sort()
            for i in range(0, len(intersections) - 1, 2):
                self.display.line(intersections[i], y, intersections[i + 1], y, color)
    

    # Render entire VGF file to display
    def render_file(self, filename):
        reader = VGFReader(filename)
        
        print(f"Rendering {reader.num_shapes} shapes...")
        
        while True:
            shape = reader.read_shape()
            if shape is None:
                break
            
            self.draw_path(shape)
            gc.collect()  # Clean up memory after each shape
        
        reader.close()
        self.display.update()


# Example usage for Pimoroni Display Pack 2.0
def main():
    from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
    
    # Initialize display
    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
    display.set_backlight(1.0)
    
    # Create renderer
    renderer = SimpleRenderer(display)
    
    # Render from SD card or flash
    renderer.render_file('image.vgf')
    
    print("Rendering complete!")


if __name__ == '__main__':
    main()
