from PIL import Image
import re
import os
from typing import List, Tuple

def parse_pam7_ascii(file_path: str) -> Image.Image:
    """
    Parse a PAM 7 ASCII format image file and return a PIL Image.
    
    PAM 7 format (RGBA):
    P7
    WIDTH <width>
    HEIGHT <height>
    DEPTH 4
    MAXVAL <maxval>
    TUPLTYPE RGB_ALPHA
    ENDHDR
    <pixel data as ASCII integers>
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse header
    lines = content.strip().split('\n')
    
    # Verify it's P7 format
    if lines[0] != 'P7':
        raise ValueError(f"Not a PAM P7 file: {file_path}")
    
    # Extract metadata
    width = height = depth = maxval = None
    tupltype = None
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
        elif line.startswith('TUPLTYPE'):
            tupltype = line.split()[1]
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
        # Group pixel values into RGBA tuples
        pixels = []
        for i in range(0, len(pixel_values), 4):
            r, g, b, a = pixel_values[i:i+4]
            # Scale to 0-255 range
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
        
    else:
        raise ValueError(f"Unsupported depth: {depth}")
    
    return img

def create_gif_from_pam7_files(input_files: List[str], output_path: str, 
                              duration: int = 500, loop: int = 0) -> None:
    """
    Create a GIF from a list of PAM 7 ASCII image files.
    
    Args:
        input_files: List of PAM 7 file paths
        output_path: Output GIF file path
        duration: Duration per frame in milliseconds
        loop: Number of loops (0 = infinite)
    """
    if not input_files:
        raise ValueError("No input files provided")
    
    # Parse all PAM files
    images = []
    print(f"Processing {len(input_files)} PAM files...")
    
    for i, file_path in enumerate(input_files):
        try:
            img = parse_pam7_ascii(file_path)
            # Convert RGBA to RGB if needed (GIF doesn't support transparency well)
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                img = background
            images.append(img)
            print(f"Processed {file_path} ({i+1}/{len(input_files)})")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    if not images:
        raise ValueError("No valid images could be processed")
    
    # Create GIF
    print(f"Creating GIF with {len(images)} frames...")
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop,
        optimize=True
    )
    
    print(f"GIF created successfully: {output_path}")

def create_gif_from_pam7_directory(directory_path: str, output_path: str,
                                  duration: int = 500, loop: int = 0,
                                  pattern: str = "*.pam") -> None:
    """
    Create a GIF from all PAM 7 files in a directory.
    
    Args:
        directory_path: Directory containing PAM files
        output_path: Output GIF file path
        duration: Duration per frame in milliseconds
        loop: Number of loops (0 = infinite)
        pattern: File pattern to match (e.g., "*.pam", "frame_*.pam")
    """
    import glob
    
    # Find all PAM files
    search_pattern = os.path.join(directory_path, pattern)
    pam_files = sorted(glob.glob(search_pattern))
    
    if not pam_files:
        raise ValueError(f"No PAM files found matching pattern: {search_pattern}")
    
    create_gif_from_pam7_files(pam_files, output_path, duration, loop)

# Example usage
if __name__ == "__main__":
    # Example 1: Convert specific files
    pam_files = [
        "cube_frame_01.pam",
        "cube_frame_02.pam", 
        "cube_frame_03.pam", 
        "cube_frame_04.pam", 
        "cube_frame_05.pam", 
        "cube_frame_06.pam", 
        "cube_frame_07.pam", 
        "cube_frame_08.pam", 
        "cube_frame_09.pam", 
        "cube_frame_10.pam", 
        "cube_frame_11.pam", 
        "cube_frame_12.pam", 
        "cube_frame_13.pam", 
        "cube_frame_14.pam", 
        "cube_frame_15.pam"
        # ... add more files
    ]
    
    try:
        create_gif_from_pam7_files(pam_files, "animation.gif", duration=200)
    except FileNotFoundError:
        print("PAM files not found. Using directory method instead...")
        
        # Example 2: Convert all PAM files in a directory
        try:
            create_gif_from_pam7_directory("./pam_frames/", "animation.gif", 
                                         duration=200, loop=0)
        except Exception as e:
            print(f"Error: {e}")
            print("\nTo use this script:")
            print("1. Place your PAM 7 ASCII files in a directory")
            print("2. Update the file paths or directory path")
            print("3. Run the script")