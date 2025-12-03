# this sample requires installment of PIL
# check for installments: python -m pip list

from PIL import Image, ImageDraw
import math

# add extra points along side to simulate the "V" shape
def divide_side(x1, y1, x2, y2, segments):
    points = []
    # starting point
    points.append((x1, y1))
    
    # intermediate points along the side
    for i in range(1, segments):
        x = x1 + (x2 - x1) * i / segments
        y = y1 + (y2 - y1) * i / segments
        points.append((x, y))
    
    # final point
    points.append((x2, y2))
    
    return points

# simulate the "V" shape and create more fractal details
def koch_snowflake(x1, y1, x2, y2, iterations, segments=4):
    points = divide_side(x1, y1, x2, y2, segments)
    
    # init list to store new points for fractal
    new_points = []
    
    for i in range(len(points) - 1):
        x_start, y_start = points[i]
        x_end, y_end = points[i + 1]
        
        # "V" shape (peak of Koch curve)
        dx = (x_end - x_start) / 3
        dy = (y_end - y_start) / 3
        xA = x_start + dx
        yA = y_start + dy
        xB = x_start + 2 * dx
        yB = y_start + 2 * dy
        
        # peak of triangle
        x_peak = (xA + xB) / 2 - (math.sqrt(3) / 6) * (yB - yA)
        y_peak = (yA + yB) / 2 + (math.sqrt(3) / 6) * (xB - xA)
        
        # new points to list
        new_points.append((x_start, y_start))
        new_points.append((xA, yA))
        new_points.append((x_peak, y_peak))
        new_points.append((xB, yB))
    
    # final point
    new_points.append((points[-1][0], points[-1][1]))
    
    return new_points

# draw Koch snowflake
def draw_snowflake(iterations, segments=4, image_size=(600, 600)):
    # blank image with white background
    img = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(img)

    # initial points of an equilateral triangle
    size = 300
    height = size * math.sqrt(3) / 2
    xCenter = image_size[0] / 2
    yCenter = image_size[1] / 2

    # three vertices of the triangle
    p1 = (xCenter, yCenter - height / 2)
    p2 = (xCenter - size / 2, yCenter + height / 2)
    p3 = (xCenter + size / 2, yCenter + height / 2)

    # init list of points
    points = []
    
    # divide each side of triangle into smaller segments
    points += koch_snowflake(p1[0], p1[1], p2[0], p2[1], iterations, segments)
    points += koch_snowflake(p2[0], p2[1], p3[0], p3[1], iterations, segments)
    points += koch_snowflake(p3[0], p3[1], p1[0], p1[1], iterations, segments)
    
    # plot Koch snowflake by connecting points
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        draw.line([x1, y1, x2, y2], fill="blue")

    img.show()

# number of iterations
iterations = int(input("Enter the number of iterations (1-4): "))

# draw snowflake with specified number of iterations
draw_snowflake(iterations)
