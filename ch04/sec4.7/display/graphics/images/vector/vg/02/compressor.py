import json
import struct
import sys

def compress_json(input_file, output_file):
    """
    Compress simplified SVG JSON format for RPi Pico display.
    Optimised for DisplayPack 2.0 (320x240 pixels).
    """
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Start with meta information
    compressed = {
        'v': 1,  # version
        'w': data['meta']['targetWidth'],
        'h': data['meta']['targetHeight'],
        's': []  # shapes
    }
    
    # Color palette to reduce repetition
    color_map = {}
    color_index = 0
    
    def get_color_index(color):
        nonlocal color_index
        if color is None:
            return None
        if color not in color_map:
            color_map[color] = color_index
            color_index += 1
        return color_map[color]
    
    # Compress each shape
    for shape in data['shapes']:
        compressed_shape = {
            't': shape['tag']  # tag
        }
        
        # Compress path data - convert to coordinate pairs
        if 'path' in shape:
            path_str = shape['path']
            # Parse path string into commands
            coords = []
            parts = path_str.split()
            i = 0
            while i < len(parts):
                if parts[i] in ['M', 'L']:
                    # Skip command, just take coordinates
                    i += 1
                    if i < len(parts):
                        x = int(parts[i])
                        i += 1
                        if i < len(parts):
                            y = int(parts[i])
                            coords.extend([x, y])
                            i += 1
                else:
                    i += 1
            
            compressed_shape['p'] = coords  # path as coordinate array
        
        # Store colors with indices
        if 'fill' in shape:
            compressed_shape['f'] = get_color_index(shape['fill'])
        
        if 'stroke' in shape:
            compressed_shape['st'] = get_color_index(shape['stroke'])
        
        if 'strokeWidth' in shape and shape['strokeWidth'] != 0:
            compressed_shape['sw'] = shape['strokeWidth']
        
        compressed['s'].append(compressed_shape)
    
    # Add color palette
    palette = [''] * len(color_map)
    for color, idx in color_map.items():
        palette[idx] = color
    compressed['c'] = palette  # color palette
    
    # Save compressed version
    with open(output_file, 'w') as f:
        json.dump(compressed, f, separators=(',', ':'))
    
    # Calculate compression ratio
    original_size = len(json.dumps(data))
    compressed_size = len(json.dumps(compressed, separators=(',', ':')))
    ratio = (1 - compressed_size / original_size) * 100
    
    print(f"Original size: {original_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")
    print(f"Compression ratio: {ratio:.1f}%")
    print(f"Colors in palette: {len(palette)}")
    print(f"Total shapes: {len(compressed['s'])}")


def main(argv):
    if len(argv) < 3:
        print('Usage: compress.py input.json output.json')
        return 1
    infile = argv[1]
    outfile = argv[2]
    compress_json(infile, outfile)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

