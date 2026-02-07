def validate_ppm3(file_path):
    try:
        with open(file_path, 'r') as f:
            # Validate header
            header = f.readline().strip()
            if header != "P3":
                print("Error: Missing or invalid header. Expected 'P3'.")
                return

            # Skip comments
            line = f.readline().strip()
            while line.startswith("#"):
                print(f"Comment: {line}")
                line = f.readline().strip()

            # Read dimensions
            try:
                width, height = map(int, line.split())
            except ValueError:
                print("Error: Could not parse dimensions.")
                return

            print(f"Dimensions: {width} x {height}")

            # Read max color value
            max_color = int(f.readline().strip())
            if max_color > 255:
                print("Error: Max color value greater than 255 is unsupported.")
                return
            print(f"Max Color Value: {max_color}")

            # Read pixel data
            pixels = []
            for line in f:
                if line.startswith("#"):
                    print(f"Comment in data: {line.strip()}")
                else:
                    pixels.extend(line.split())

            # Validate pixel count
            pixel_count = len(pixels)
            expected_count = width * height * 3
            print(f"Pixel data count: {pixel_count}, Expected: {expected_count}")
            if pixel_count != expected_count:
                print("Error: Pixel data does not match expected count.")
                return

            # Check for invalid values
            invalid_pixels = [p for p in pixels if not p.isdigit() or int(p) < 0 or int(p) > max_color]
            if invalid_pixels:
                print(f"Invalid pixel values: {invalid_pixels[:10]}...")
                return

            print("PPM file is valid.")

    except FileNotFoundError:
        print("Error: File not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Example usage
if __name__ == "__main__":
    file_path = input("Enter the path to the PPM3 file: ").strip()
    validate_ppm3(file_path)
