#!/usr/bin/env python3
"""
PAM 7 ASCII to GIF Converter - Updated for 3D Renderer Output
Converts PAM 7 ASCII format files to animated GIF
Works with the output from the 3D renderer C program
"""

import re
import os
from PIL import Image
import numpy as np
from typing import List, Optional

def parse_pam7_ascii(file_path: str) -> Image.Image:
    """
    Parse a PAM 7 ASCII format file and return PIL Image
    
    Args:
        file_path: Path to the PAM file
        
    Returns:
        PIL Image object
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse header
    header_match = re.search(r'P7\s+WIDTH\s+(\d+)\s+HEIGHT\s+(\d+)\s+DEPTH\s+(\d+)\s+MAXVAL\s+(\d+)\s+TUPLTYPE\s+(\w+)\s+ENDHDR\s+(.*)', 
                            content, re.DOTALL)
    
    if not header_match:
        raise ValueError(f"Invalid PAM 7 format in {file_path}")
    
    width = int(header_match.group(1))
    height = int(header_match.group(2))
    depth = int(header_match.group(3))
    maxval = int(header_match.group(4))
    tupltype = header_match.group(5)
    data_section = header_match.group(6)
    
    # Parse pixel data
    pixel_values = []
    for line in data_section.strip().split('\n'):
        if line.strip():
            values = [int(x) for x in line.split() if x.strip().isdigit()]
            pixel_values.extend(values)
    
    expected_pixels = width * height * depth
    if len(pixel_values) != expected_pixels:
        raise ValueError(f"Expected {expected_pixels} pixel values, got {len(pixel_values)} in {file_path}")
    
    # Convert to numpy array and reshape
    pixel_array = np.array(pixel_values, dtype=np.uint8)
    
    if tupltype == "GRAYSCALE":
        image_array = pixel_array.reshape((height, width))
        return Image.fromarray(image_array, mode='L')
    elif tupltype == "RGB":
        image_array = pixel_array.reshape((height, width, 3))
        return Image.fromarray(image_array, mode='RGB')
    else:
        raise ValueError(f"Unsupported TUPLTYPE: {tupltype}")

def create_gif_from_pam7_files(file_list: List[str], output_path: str, 
                              duration: int = 100, loop: int = 0) -> None:
    """
    Create animated GIF from list of PAM 7 files
    
    Args:
        file_list: List of PAM file paths
        output_path: Output GIF file path
        duration: Frame duration in milliseconds
        loop: Number of loops (0 = infinite)
    """
    images = []
    
    print(f"Converting {len(file_list)} PAM files to GIF...")
    
    for i, file_path in enumerate(file_list):
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            continue
            
        try:
            img = parse_pam7_ascii(file_path)
            images.append(img)
            print(f"Processed: {file_path} ({i+1}/{len(file_list)})")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    if not images:
        raise ValueError("No valid images found")
    
    # Save as animated GIF
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=loop,
        optimize=True
    )
    
    print(f"Created animated GIF: {output_path}")
    print(f"Frames: {len(images)}, Duration: {duration}ms per frame")

def create_gif_from_pam7_directory(directory: str, output_path: str, 
                                  duration: int = 100, loop: int = 0,
                                  pattern: str = "frame_*.pam") -> None:
    """
    Create animated GIF from all PAM files in a directory
    
    Args:
        directory: Directory containing PAM files
        output_path: Output GIF file path
        duration: Frame duration in milliseconds
        loop: Number of loops (0 = infinite)
        pattern: File pattern to match (supports wildcards)
    """
    import glob
    
    # Find all matching PAM files
    search_pattern = os.path.join(directory, pattern)
    pam_files = sorted(glob.glob(search_pattern))
    
    if not pam_files:
        raise FileNotFoundError(f"No PAM files found matching pattern: {search_pattern}")
    
    print(f"Found {len(pam_files)} PAM files in {directory}")
    create_gif_from_pam7_files(pam_files, output_path, duration, loop)

# Example usage updated for 3D renderer output
if __name__ == "__main__":
    # Generate file list for the 3D renderer frames (frame_000.pam to frame_059.pam)
    renderer_frames = [f"frame_{i:03d}.pam" for i in range(60)]
    
    # Add the wireframe file for comparison
    all_files = renderer_frames + ["wireframe.pam"]
    
    print("3D Renderer PAM to GIF Converter")
    print("=" * 40)
    
    try:
        # Method 1: Convert the animation frames
        print("Converting 3D renderer animation frames...")
        create_gif_from_pam7_files(renderer_frames, "3d_animation.gif", duration=167)  # ~6fps
        
        # Method 2: Create a slower version
        print("\nCreating slower animation...")
        create_gif_from_pam7_files(renderer_frames, "3d_animation_slow.gif", duration=333)  # ~3fps
        
        # Method 3: Convert using directory method (if files are in a subdirectory)
        try:
            create_gif_from_pam7_directory("./", "3d_animation_auto.gif", 
                                         duration=200, pattern="frame_*.pam")
        except FileNotFoundError:
            print("Directory method skipped - files not found in current directory")
        
        # Method 4: Create a comparison GIF with wireframe at the end
        print("\nCreating animation with wireframe comparison...")
        comparison_frames = renderer_frames + ["wireframe.pam"] * 10  # Hold wireframe for 10 frames
        create_gif_from_pam7_files(comparison_frames, "3d_with_wireframe.gif", duration=200)
        
    except FileNotFoundError as e:
        print(f"Files not found: {e}")
        print("\nMake sure you've run the 3D renderer C program first!")
        print("The renderer should generate files: frame_000.pam through frame_059.pam")
        
    except Exception as e:
        print(f"Error: {e}")
        
    print("\nUsage Notes:")
    print("1. First compile and run the 3D renderer C program")
    print("2. This will generate frame_000.pam through frame_059.pam")
    print("3. Run this Python script to convert frames to animated GIF")
    print("4. View the resulting .gif files in any image viewer")
    
    # Optional: Create individual PNG files for inspection
    try:
        print("\nConverting first few frames to PNG for inspection...")
        for i in range(min(5, len(renderer_frames))):
            pam_file = f"frame_{i:03d}.pam"
            if os.path.exists(pam_file):
                img = parse_pam7_ascii(pam_file)
                png_file = f"frame_{i:03d}.png"
                img.save(png_file)
                print(f"Saved: {png_file}")
    except Exception as e:
        print(f"PNG conversion error: {e}")
