from PIL import Image
import sys
import os

def png_to_pam7_ascii(input_path, output_path=None):
    """
    Convert PNG image to PAM 7 ASCII format.
    PAM 7 uses ASCII encoding for pixel values.
    """
    try:
        # Open the PNG image
        img = Image.open(input_path)
        
        # Convert to RGB if it has an alpha channel or is in a different mode
        if img.mode in ('RGBA', 'LA'):
            # Create white background for transparency
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            else:  # LA mode
                background.paste(img.convert('RGB'))
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get image dimensions
        width, height = img.size
        
        # Generate output filename if not provided
        if output_path is None:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}.pam"
        
        # Write PAM 7 ASCII format
        with open(output_path, 'w') as f:
            # PAM header
            f.write("P7\n")
            f.write(f"WIDTH {width}\n")
            f.write(f"HEIGHT {height}\n")
            f.write("DEPTH 3\n")  # RGB = 3 channels
            f.write("MAXVAL 255\n")
            f.write("TUPLTYPE RGB\n")
            f.write("ENDHDR\n")
            
            # Write pixel data in ASCII format
            for y in range(height):
                for x in range(width):
                    r, g, b = img.getpixel((x, y))
                    f.write(f"{r} {g} {b}\n")
        
        print(f"Successfully converted {input_path} to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error converting {input_path}: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python png_to_pam7.py <input.png> [output.pam]")
        print("If output filename is not specified, it will use the input filename with .pam extension")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)
    
    if not input_file.lower().endswith('.png'):
        print("Warning: Input file doesn't have .png extension")
    
    result = png_to_pam7_ascii(input_file, output_file)
    if result:
        print(f"Conversion completed successfully!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
