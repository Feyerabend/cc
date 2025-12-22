#!/usr/bin/env python3
"""
Vector Graphics Binary Compressor
Compresses JSON vector graphics to efficient binary format for RPi Pico
"""

import json
import struct
import sys

def compress_vg(input_file, output_file):
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    with open(output_file, 'wb') as f:
        # Header: magic number, version, width, height
        f.write(b'VGF1')  # Magic: Vector Graphics Format v1
        f.write(struct.pack('<HH', data['w'], data['h']))  # width, height as uint16
        
        # Write color palette
        colors = data.get('c', [])
        f.write(struct.pack('<B', len(colors)))  # Number of colors
        for color in colors:
            # Convert hex color to RGB bytes
            color = color.lstrip('#')
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            f.write(struct.pack('<BBB', r, g, b))
        
        # Write number of shapes
        shapes = data.get('s', [])
        f.write(struct.pack('<H', len(shapes)))  # Number of shapes as uint16
        
        # Write shapes
        for shape in shapes:
            shape_type = shape['t']
            
            # Shape type: 0=path (only type we support for now)
            f.write(struct.pack('<B', 0 if shape_type == 'path' else 255))
            
            # Fill color index (255 = none)
            fill_idx = shape.get('f')
            f.write(struct.pack('<B', fill_idx if fill_idx is not None else 255))
            
            # Stroke color index (255 = none)
            stroke_idx = shape.get('st')
            f.write(struct.pack('<B', stroke_idx if stroke_idx is not None else 255))
            
            # Stroke width (0-255, scale by 10 for decimals)
            stroke_width = int((shape.get('sw', 1.0)) * 10)
            f.write(struct.pack('<B', stroke_width))
            
            # Path data - use delta encoding for compression
            path = shape.get('p', [])
            num_points = len(path) // 2
            f.write(struct.pack('<H', num_points))  # Number of coordinate pairs
            
            # Write first point as absolute coordinates
            if num_points > 0:
                f.write(struct.pack('<HH', path[0], path[1]))
                
                # Write remaining points as deltas (signed bytes)
                for i in range(1, num_points):
                    dx = path[i*2] - path[(i-1)*2]
                    dy = path[i*2+1] - path[(i-1)*2+1]
                    
                    # Clamp to -127 to 127 (if larger, use escape sequence)
                    if -127 <= dx <= 127 and -127 <= dy <= 127:
                        f.write(struct.pack('<bb', dx, dy))
                    else:
                        # Escape sequence: -128 followed by full int16 delta
                        f.write(struct.pack('<b', -128))
                        f.write(struct.pack('<hh', dx, dy))
    
    # Print compression stats
    import os
    orig_size = os.path.getsize(input_file)
    comp_size = os.path.getsize(output_file)
    ratio = (1 - comp_size / orig_size) * 100
    print(f"Original: {orig_size:,} bytes")
    print(f"Compressed: {comp_size:,} bytes")
    print(f"Ratio: {ratio:.1f}% reduction")

def decompress_vg(input_file, output_file):
    
    with open(input_file, 'rb') as f:
        # Read header
        magic = f.read(4)
        if magic != b'VGF1':
            raise ValueError("Invalid file format")
        
        width, height = struct.unpack('<HH', f.read(4))
        
        # Read color palette
        num_colors = struct.unpack('<B', f.read(1))[0]
        colors = []
        for _ in range(num_colors):
            r, g, b = struct.unpack('<BBB', f.read(3))
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        
        # Read shapes
        num_shapes = struct.unpack('<H', f.read(2))[0]
        shapes = []
        
        for _ in range(num_shapes):
            shape_type = struct.unpack('<B', f.read(1))[0]
            fill_idx = struct.unpack('<B', f.read(1))[0]
            stroke_idx = struct.unpack('<B', f.read(1))[0]
            stroke_width = struct.unpack('<B', f.read(1))[0] / 10.0
            
            num_points = struct.unpack('<H', f.read(2))[0]
            
            # Read path points
            path = []
            if num_points > 0:
                # First point (absolute)
                x, y = struct.unpack('<HH', f.read(4))
                path.extend([x, y])
                
                # Remaining points (delta encoded)
                for _ in range(num_points - 1):
                    dx = struct.unpack('<b', f.read(1))[0]
                    if dx == -128:  # Escape sequence
                        dx, dy = struct.unpack('<hh', f.read(4))
                    else:
                        dy = struct.unpack('<b', f.read(1))[0]
                    
                    x += dx
                    y += dy
                    path.extend([x, y])
            
            shape = {
                't': 'path',
                'p': path
            }
            if fill_idx != 255:
                shape['f'] = fill_idx
            if stroke_idx != 255:
                shape['st'] = stroke_idx
            if stroke_width != 1.0:
                shape['sw'] = stroke_width
            
            shapes.append(shape)
    
    # Write output JSON
    output = {
        'v': 1,
        'w': width,
        'h': height,
        'c': colors,
        's': shapes
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage:")
        print("  Compress:   python compress.py c input.json output.vgf")
        print("  Decompress: python compress.py d input.vgf output.json")
        sys.exit(1)
    
    mode = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3]
    
    if mode == 'c':
        compress_vg(input_file, output_file)
    elif mode == 'd':
        decompress_vg(input_file, output_file)
    else:
        print("Invalid mode. Use 'c' for compress or 'd' for decompress")
        sys.exit(1)
