# this sample requires installment of PIL
# check for installments: python -m pip list

from PIL import Image, ImageDraw
import math

def midpoint(p1, p2):
    """Calculate midpoint between two points"""
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def sierpinski_triangle(p1, p2, p3, iterations):
    """
    Recursively generate Sierpinski triangle points
    Returns list of triangles to draw (each triangle is a list of 3 points)
    """
    if iterations == 0:
        # Base case: return the original triangle
        return [[p1, p2, p3]]
    
    # Calculate midpoints of each side
    mid1 = midpoint(p1, p2)
    mid2 = midpoint(p2, p3)
    mid3 = midpoint(p3, p1)
    
    # Recursively generate three smaller triangles
    triangles = []
    triangles += sierpinski_triangle(p1, mid1, mid3, iterations - 1)
    triangles += sierpinski_triangle(mid1, p2, mid2, iterations - 1)
    triangles += sierpinski_triangle(mid3, mid2, p3, iterations - 1)
    
    return triangles

def draw_sierpinski(iterations, image_size=(600, 600)):
    """Draw Sierpinski triangle"""
    # blank image with white background
    img = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(img)

    # initial points of an equilateral triangle
    size = 500
    height = size * math.sqrt(3) / 2
    xCenter = image_size[0] / 2
    yCenter = image_size[1] / 2

    # three vertices of the triangle
    p1 = (xCenter, yCenter - height / 2)
    p2 = (xCenter - size / 2, yCenter + height / 2)
    p3 = (xCenter + size / 2, yCenter + height / 2)

    # generate all triangles
    triangles = sierpinski_triangle(p1, p2, p3, iterations)
    
    # draw each triangle
    for triangle in triangles:
        points = [triangle[0], triangle[1], triangle[2], triangle[0]]
        draw.polygon(points, outline="blue", fill=None)
    
    img.show()

# number of iterations
iterations = int(input("Enter the number of iterations (1-7): "))

# draw Sierpinski triangle with specified number of iterations
draw_sierpinski(iterations)
