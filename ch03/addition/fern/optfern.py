import random

def generate_barnsley_fern(width, height, filename="optfern.ppm"):
    # PPM3 header
    header = f"P3\n{width} {height}\n255\n"
    
    # black canvas (RGB: 0, 0, 0)
    image_data = [["0 0 0" for _ in range(width)] for _ in range(height)]
    
    def plot_point(x, y, color):
        px = int((x + 3) * (width // 6))  # x between -3 and 3
        py = int((y + 0.5) * (height // 8))  # y between 0 and 10
        if 0 <= px < width and 0 <= py < height and image_data[height - py - 1][px] == "0 0 0":
            image_data[height - py - 1][px] = color

    def generate_layer(iterations, color):
        x, y = 0, 0  # Reset initial point
        for _ in range(iterations):
            r = random.random()
            if r < 0.02:
                x_new, y_new = 0, 0.16 * y
            elif r < 0.86:
                x_new, y_new = 0.85 * x + 0.04 * y, -0.04 * x + 0.85 * y + 1.6
            elif r < 0.93:
                x_new, y_new = 0.2 * x - 0.26 * y, 0.23 * x + 0.22 * y + 1.6
            else:
                x_new, y_new = -0.15 * x + 0.28 * y, 0.26 * x + 0.24 * y + 0.44
            x, y = x_new, y_new
            plot_point(x, y, color)

    layers = [
        (50000, "0 255 0"),      # dark green
        (30000, "150 255 150"),  # lighter green
        (20000, "200 255 200"),  # very light green
        (15000, "200 255 150"),  # yellow-green nuance
    ]
    for iterations, color in layers:
        generate_layer(iterations, color)

    with open(filename, "w") as f:
        f.write(header)
        for row in image_data:
            f.write(" ".join(row) + "\n")

width = 800
height = 600
generate_barnsley_fern(width, height)
