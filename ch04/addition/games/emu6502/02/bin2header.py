#!/usr/bin/env python3
"""
Convert a binary file to a C header file with byte array.
Usage: python bin2header.py input.bin output.h [array_name]
"""

import sys
import os

def bin2header(input_file, output_file, array_name="rom_data"):
    """Convert binary file to C header with byte array."""
    
    # Read binary file
    try:
        with open(input_file, 'rb') as f:
            data = f.read()
    except IOError as e:
        print(f"Error reading {input_file}: {e}", file=sys.stderr)
        return False
    
    if len(data) == 0:
        print(f"Warning: {input_file} is empty", file=sys.stderr)
    
    # Generate header
    guard_name = f"{array_name.upper()}_H"
    
    try:
        with open(output_file, 'w') as f:
            f.write(f"// Auto-generated from {os.path.basename(input_file)}\n")
            f.write(f"// Size: {len(data)} bytes\n\n")
            f.write(f"#ifndef {guard_name}\n")
            f.write(f"#define {guard_name}\n\n")
            f.write("#include <stdint.h>\n\n")
            f.write(f"const uint8_t {array_name}[] = {{\n")
            
            # Write bytes in rows of 16
            for i in range(0, len(data), 16):
                row = data[i:i+16]
                hex_bytes = ', '.join(f'0x{b:02X}' for b in row)
                f.write(f"    {hex_bytes}")
                if i + 16 < len(data):
                    f.write(',')
                f.write('\n')
            
            f.write("};\n\n")
            f.write(f"#define {array_name.upper()}_SIZE {len(data)}\n\n")
            f.write(f"#endif // {guard_name}\n")
    
    except IOError as e:
        print(f"Error writing {output_file}: {e}", file=sys.stderr)
        return False
    
    print(f"Generated {output_file}: {len(data)} bytes as '{array_name}'")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python bin2header.py input.bin output.h [array_name]")
        print("Example: python bin2header.py program.bin rom.h rom_data")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    array_name = sys.argv[3] if len(sys.argv) > 3 else "rom_data"
    
    # Validate array name (C identifier)
    if not array_name.replace('_', '').isalnum() or array_name[0].isdigit():
        print(f"Error: '{array_name}' is not a valid C identifier", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found", file=sys.stderr)
        sys.exit(1)
    
    if bin2header(input_file, output_file, array_name):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()

