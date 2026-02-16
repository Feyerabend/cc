#!/usr/bin/env python3
"""
PAM Animation to GIF Converter
Converts a series of PAM 7 ASCII files into an animated GIF
"""

from PIL import Image
import glob
import os
import sys
import re

def parse_pam7_ascii(file_path: str) -> Image.Image:
    """Parse a PAM 7 ASCII format image file and return a PIL Image."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    
    # Verify it's P7 format
    if lines[0] != 'P7':
        raise ValueError(f"Not a PAM P7 file: {file_path}")
    
    # Extract metadata
    width = height = depth = maxval = None
    header_end = 0
    
    for i, line in enumerate(lines[1:], 1):
        if line.startswith('WIDTH'):
            width = int(line.split()[1])
        elif line.startswith('HEIGHT'):
            height = int(line.split()[1])
        elif line.startswith('DEPTH'):
            depth = int(line.split()[1])
        elif line.startswith('MAXVAL'):
            maxval = int(line.split()[1])
        elif line == 'ENDHDR':
            header_end = i + 1
            break
    
    if not all([width, height, depth, maxval]):
        raise ValueError(f"Invalid PAM header in {file_path}")
    
    # Extract pixel data
    pixel_data_lines = lines[header_end:]
    pixel_data_str = ' '.join(pixel_data_lines)
    pixel_values = [int(x) for x in pixel_data_str.split()]
    
    # Verify we have the right amount of data
    expected_values = width * height * depth
    if len(pixel_values) != expected_values:
        raise ValueError(f"Expected {expected_values} pixel values, got {len(pixel_values)}")
    
    # Convert to PIL Image
    if depth == 4:  # RGBA
        pixels = []
        for i in range(0, len(pixel_values), 4):
            r, g, b, a = pixel_values[i:i+4]
            r = int((r / maxval) * 255)
            g = int((g / maxval) * 255)
            b = int((b / maxval) * 255)
            a = int((a / maxval) * 255)
            pixels.append((r, g, b, a))
        
        img = Image.new('RGBA', (width, height))
        img.putdata(pixels)
        
    elif depth == 3:  # RGB
        pixels = []
        for i in range(0, len(pixel_values), 3):
            r, g, b = pixel_values[i:i+3]
            r = int((r / maxval) * 255)
            g = int((g / maxval) * 255)
            b = int((b / maxval) * 255)
            pixels.append((r, g, b))
        
        img = Image.new('RGB', (width, height))
        img.putdata(pixels)
        
    elif depth == 1:  # Grayscale
        pixels = []
        for i in range(0, len(pixel_values), 1):
            gray = int((pixel_values[i] / maxval) * 255)
            pixels.append(gray)
        
        img = Image.new('L', (width, height))
        img.putdata(pixels)
        
    else:
        raise ValueError(f"Unsupported depth: {depth}")
    
    return img

def natural_sort_key(s):
    """Sort strings containing numbers in natural order."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def create_gif_from_pattern(pattern: str, output_path: str, 
                           duration: int = 100, loop: int = 0,
                           optimize: bool = True) -> None:
    """
    Create a GIF from PAM files matching a pattern.
    
    Args:
        pattern: Glob pattern for PAM files (e.g., "frame_*.pam")
        output_path: Output GIF file path
        duration: Duration per frame in milliseconds
        loop: Number of loops (0 = infinite)
        optimize: Whether to optimize the GIF
    """
    # Find all PAM files matching pattern
    pam_files = sorted(glob.glob(pattern), key=natural_sort_key)
    
    if not pam_files:
        raise ValueError(f"No PAM files found matching pattern: {pattern}")
    
    print(f"Found {len(pam_files)} PAM files")
    
    # Parse all PAM files
    images = []
    
    for i, file_path in enumerate(pam_files):
        try:
            img = parse_pam7_ascii(file_path)
            
            # Convert to RGB if needed (for consistent GIF format)
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (20, 20, 30))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode == 'L':
                img = img.convert('RGB')
            
            images.append(img)
            print(f"  [{i+1}/{len(pam_files)}] Processed {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"  [ERROR] Failed to process {file_path}: {e}")
            continue
    
    if not images:
        raise ValueError("No valid images could be processed")
    
    # Create GIF
    print(f"\nCreating GIF: {output_path}")
    print(f"  Frames: {len(images)}")
    print(f"  Duration: {duration}ms per frame")
    print(f"  Loop: {'infinite' if loop == 0 else f'{loop} times'}")
    print(f"  Optimize: {optimize}")
    
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop,
        optimize=optimize
    )
    
    file_size = os.path.getsize(output_path)
    print(f"\nGIF created successfully!")
    print(f"  Output: {output_path}")
    print(f"  Size: {file_size / 1024:.1f} KB")

def create_gif_from_files(files: list, output_path: str,
                         duration: int = 100, loop: int = 0,
                         optimize: bool = True) -> None:
    """
    Create a GIF from a list of PAM files.
    
    Args:
        files: List of PAM file paths
        output_path: Output GIF file path
        duration: Duration per frame in milliseconds
        loop: Number of loops (0 = infinite)
        optimize: Whether to optimize the GIF
    """
    if not files:
        raise ValueError("No PAM files provided")
    
    # Sort files naturally
    files = sorted(files, key=natural_sort_key)
    
    print(f"Found {len(files)} PAM files")
    
    # Parse all PAM files
    images = []
    
    for i, file_path in enumerate(files):
        try:
            img = parse_pam7_ascii(file_path)
            
            # Convert to RGB if needed
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (20, 20, 30))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode == 'L':
                img = img.convert('RGB')
            
            images.append(img)
            print(f"  [{i+1}/{len(files)}] Processed {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"  [ERROR] Failed to process {file_path}: {e}")
            continue
    
    if not images:
        raise ValueError("No valid images could be processed")
    
    # Create GIF
    print(f"\nCreating GIF: {output_path}")
    print(f"  Frames: {len(images)}")
    print(f"  Duration: {duration}ms per frame")
    print(f"  Loop: {'infinite' if loop == 0 else f'{loop} times'}")
    print(f"  Optimize: {optimize}")
    
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop,
        optimize=optimize
    )
    
    file_size = os.path.getsize(output_path)
    print(f"\nGIF created successfully!")
    print(f"  Output: {output_path}")
    print(f"  Size: {file_size / 1024:.1f} KB")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pam_to_gif.py <pattern_or_files> [output.gif] [duration_ms] [loop]")
        print("\nExamples:")
        print("  python3 pam_to_gif.py 'frame_*.pam'                    # Quoted pattern (recommended)")
        print("  python3 pam_to_gif.py frame_*.pam                      # Unquoted (shell expands)")
        print("  python3 pam_to_gif.py 'frame_*.pam' animation.gif")
        print("  python3 pam_to_gif.py 'frame_*.pam' animation.gif 50")
        print("  python3 pam_to_gif.py frame_001.pam frame_002.pam ... output.gif 100")
        print("\nArguments:")
        print("  pattern     - Glob pattern for PAM files (e.g., 'frame_*.pam') - USE QUOTES!")
        print("                OR list of PAM files if shell expands the glob")
        print("  output.gif  - Output filename (default: animation.gif)")
        print("  duration_ms - Frame duration in milliseconds (default: 100)")
        print("  loop        - Number of loops, 0 = infinite (default: 0)")
        print("\nNote: Always use quotes around glob patterns to prevent shell expansion!")
        sys.exit(1)
    
    # Detect if first argument is a glob pattern or already-expanded files
    first_arg = sys.argv[1]
    
    # Check if it looks like a pattern (contains * or ?) or is a single file
    if '*' in first_arg or '?' in first_arg:
        # It's a pattern - use glob
        pattern = first_arg
        output = sys.argv[2] if len(sys.argv) > 2 else "animation.gif"
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        loop = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        
        try:
            create_gif_from_pattern(pattern, output, duration, loop)
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    else:
        # Collect all .pam files from arguments
        pam_files = []
        output = "animation.gif"
        duration = 100
        loop = 0
        
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg.endswith('.pam'):
                pam_files.append(arg)
            elif arg.endswith('.gif'):
                output = arg
            elif i > len(pam_files) + 1:  # After files and output name
                try:
                    val = int(arg)
                    if duration == 100:
                        duration = val
                    else:
                        loop = val
                except ValueError:
                    pass
        
        if not pam_files:
            print("\nError: No PAM files found in arguments")
            print("Usage: python3 pam_to_gif.py 'pattern*.pam' [output.gif] [duration] [loop]")
            print("   or: python3 pam_to_gif.py file1.pam file2.pam ... [output.gif] [duration] [loop]")
            sys.exit(1)
        
        try:
            create_gif_from_files(pam_files, output, duration, loop)
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
