import random

def generate_barnsley_fern(width, height, filename="fern.ppm"):
    # PPM3 header
    header = f"P3\n{width} {height}\n255\n"
    
    # black canvas (RGB: 0, 0, 0)
    image_data = [["0 0 0" for _ in range(width)] for _ in range(height)]
    
    def plot_point(x, y, color):
        px = int((x + 3) * (width // 6))  # x between -3 and 3
        py = int((y + 0.5) * (height // 8))  # y between 0 and 10
        if 0 <= px < width and 0 <= py < height and image_data[height - py - 1][px] == "0 0 0":
            image_data[height - py - 1][px] = color

    # base layer (dark green)
    x, y = 0, 0  # Initial point
    for _ in range(50000):  # iterations for the base layer
        r = random.random()
        if r < 0.02:
            x_new = 0
            y_new = 0.16 * y
        elif r < 0.86:
            x_new = 0.85 * x + 0.04 * y
            y_new = -0.04 * x + 0.85 * y + 1.6
        elif r < 0.93:
            x_new = 0.2 * x - 0.26 * y
            y_new = 0.23 * x + 0.22 * y + 1.6
        else:
            x_new = -0.15 * x + 0.28 * y
            y_new = 0.26 * x + 0.24 * y + 0.44
        x, y = x_new, y_new
        plot_point(x, y, "0 255 0")  # dark green color (RGB: 0, 255, 0)

    # second layer (lighter green)
    x, y = 0, 0  # reset
    for _ in range(30000):  # iterations for the second layer
        r = random.random()
        if r < 0.02:
            x_new = 0
            y_new = 0.16 * y
        elif r < 0.86:
            x_new = 0.85 * x + 0.04 * y
            y_new = -0.04 * x + 0.85 * y + 1.6
        elif r < 0.93:
            x_new = 0.2 * x - 0.26 * y
            y_new = 0.23 * x + 0.22 * y + 1.6
        else:
            x_new = -0.15 * x + 0.28 * y
            y_new = 0.26 * x + 0.24 * y + 0.44
        x, y = x_new, y_new
        plot_point(x, y, "150 255 150")  # lighter green color (RGB: 150, 255, 150)

    # third layer (very light green)
    x, y = 0, 0  # reset
    for _ in range(20000):  # iterations for the third layer
        r = random.random()
        if r < 0.02:
            x_new = 0
            y_new = 0.16 * y
        elif r < 0.86:
            x_new = 0.85 * x + 0.04 * y
            y_new = -0.04 * x + 0.85 * y + 1.6
        elif r < 0.93:
            x_new = 0.2 * x - 0.26 * y
            y_new = 0.23 * x + 0.22 * y + 1.6
        else:
            x_new = -0.15 * x + 0.28 * y
            y_new = 0.26 * x + 0.24 * y + 0.44
        x, y = x_new, y_new
        plot_point(x, y, "200 255 200")  # very light green color (RGB: 200, 255, 200)

    # fourth layer (yellow-green nuance)
    x, y = 0, 0  # reset
    for _ in range(15000):  # iterations for subtle highlights
        r = random.random()
        if r < 0.02:
            x_new = 0
            y_new = 0.16 * y
        elif r < 0.86:
            x_new = 0.85 * x + 0.04 * y
            y_new = -0.04 * x + 0.85 * y + 1.6
        elif r < 0.93:
            x_new = 0.2 * x - 0.26 * y
            y_new = 0.23 * x + 0.22 * y + 1.6
        else:
            x_new = -0.15 * x + 0.28 * y
            y_new = 0.26 * x + 0.24 * y + 0.44
        x, y = x_new, y_new
        plot_point(x, y, "200 255 150")  # yellow-green nuance (RGB: 200, 255, 150)

    with open(filename, "w") as f:
        f.write(header)
        for row in image_data:
            f.write(" ".join(row) + "\n")

width = 800
height = 600
generate_barnsley_fern(width, height)
