import re
import math
from xml.etree import ElementTree as ET

class Edge:
    def __init__(self, x1, y1, x2, y2):
        # edges must be ordered from top to bottom
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.slope = (x2 - x1) / (y2 - y1) if y1 != y2 else None

    def __repr__(self):
        return f"Edge(({self.x1}, {self.y1}) -> ({self.x2}, {self.y2}))"

    def x_at(self, y):  # calculate the x-coordinate on the edge for a given y-coordinate
        if self.slope is None:
            return self.x1
        return self.x1 + (y - self.y1) * self.slope


class Rasterizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]

    def fill_polygon(self, polygon, color, fill_rule="even-odd"):
        def hex_to_rgb(hex_color):
            # Strip the '#' character and convert the hex color to an RGB tuple
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        # Convert the hex color string to an RGB tuple
        color_rgb = hex_to_rgb(color)

        # convert polygon into list of edges
        edges = []
        for i in range(len(polygon)):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]  # wrap around to first point
            if y1 != y2:  # ignore horizontal edges
                edges.append(Edge(x1, y1, x2, y2))

        # group edges by scanline
        edges.sort(key=lambda e: e.y1)
        min_y = max(0, min(edge.y1 for edge in edges))
        max_y = min(self.height - 1, max(edge.y2 for edge in edges))

        for y in range(min_y, max_y + 1):

            # active edges for current scanline
            active_edges = [edge for edge in edges if edge.y1 <= y < edge.y2]
            intersections = [edge.x_at(y) for edge in active_edges]
            intersections.sort()  # for effective use

            if fill_rule == "even-odd":
                for i in range(0, len(intersections), 2):
                    x_start = int(max(0, min(intersections[i], self.width - 1)))
                    x_end = int(max(0, min(intersections[i + 1], self.width - 1)))
                    for x in range(x_start, x_end + 1):
                        self.canvas[y][x] = color_rgb

            elif fill_rule == "winding":
                winding_count = 0
                for x in range(self.width):
                    for edge in active_edges:
                        if edge.x_at(y) == x:
                            winding_count += 1
                    if winding_count % 2 != 0:
                        self.canvas[y][x] = color_rgb

    def save_ppm(self, filename):
        with open(filename, 'w') as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            for row in self.canvas:
                for pixel in row:
                    # Ensure that each pixel is an RGB tuple
                    if len(pixel) != 3:
                        print(f"Error: Pixel doesn't have 3 values. Pixel: {pixel}")
                    r, g, b = pixel  # Unpack each pixel into r, g, b values
                    f.write(f"{r} {g} {b} ")
                f.write("\n")

class SVGPathParser:
    def __init__(self, path_data):
        self.commands = self.parse_path(path_data)

    def parse_path(self, path_data):
        # Add whitespace between commands and arguments if there is none
        path_data = re.sub(r'([a-zA-Z])(?=\d)', r'\1 ', path_data)  # Command followed directly by a digit
        path_data = re.sub(r'([a-zA-Z])(?=[a-zA-Z])', r'\1 ', path_data)  # Command followed by another command
        
        commands = []
        tokens = path_data.replace(',', ' ').split()
        i = 0
        while i < len(tokens):
            try:
                command = tokens[i]
                i += 1
                if command == 'M' or command == 'm':  # move to
                    x, y = float(tokens[i]), float(tokens[i + 1])
                    commands.append(('M', x, y))
                    i += 2
                elif command == 'L' or command == 'l':  # line to
                    x, y = float(tokens[i]), float(tokens[i + 1])
                    commands.append(('L', x, y))
                    i += 2
                elif command == 'C' or command == 'c':  # cubic Bezier curve
                    x1, y1, x2, y2, x3, y3 = float(tokens[i]), float(tokens[i + 1]), float(tokens[i + 2]), float(tokens[i + 3]), float(tokens[i + 4]), float(tokens[i + 5])
                    commands.append(('C', x1, y1, x2, y2, x3, y3))
                    i += 6
                elif command == 'Z' or command == 'z':  # close path
                    commands.append(('Z',))
                else:
                    # Skip unknown commands silently - just move to next token
                    pass
            except (ValueError, IndexError):
                # If we can't parse a command, skip it and continue
                pass
        return commands

    def get_polygon(self):
        polygon = []
        for command in self.commands:
            try:
                if command[0] in ('M', 'L'):
                    polygon.append((int(command[1]), int(command[2])))
                elif command[0] == 'C':
                    # Approximate cubic Bezier curve as a series of line segments
                    if len(polygon) == 0:
                        # Need at least one point to start from
                        continue
                    x1, y1, x2, y2, x3, y3 = command[1:]
                    steps = 10
                    for t in range(steps + 1):
                        t /= steps
                        x = (1 - t)**3 * polygon[-1][0] + 3 * (1 - t)**2 * t * x1 + 3 * (1 - t) * t**2 * x2 + t**3 * x3
                        y = (1 - t)**3 * polygon[-1][1] + 3 * (1 - t)**2 * t * y1 + 3 * (1 - t) * t**2 * y2 + t**3 * y3
                        polygon.append((int(x), int(y)))
            except (IndexError, ValueError):
                # Skip problematic commands
                pass
        return polygon

class SVGParser:
    def __init__(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()

    def parse(self):
        elements = []
        for elem in self.root:
            if elem.tag == '{http://www.w3.org/2000/svg}path':
                d = elem.attrib['d']
                style = elem.attrib.get('style', '')
                color = self.extract_color(style)
                elements.append(('path', d, color))
            elif elem.tag == '{http://www.w3.org/2000/svg}rect':
                x = float(elem.attrib['x'])
                y = float(elem.attrib['y'])
                width = float(elem.attrib['width'])
                height = float(elem.attrib['height'])
                style = elem.attrib.get('style', '')
                color = self.extract_color(style)
                elements.append(('rect', (x, y, width, height), color))
            elif elem.tag == '{http://www.w3.org/2000/svg}circle':
                cx = float(elem.attrib['cx'])
                cy = float(elem.attrib['cy'])
                r = float(elem.attrib['r'])
                style = elem.attrib.get('style', '')
                color = self.extract_color(style)
                elements.append(('circle', (cx, cy, r), color))
        return elements

    def extract_color(self, style):
        match = re.search(r'fill:\s*(#[0-9a-fA-F]{6})', style)
        return match.group(1) if match else "#000000"  # Default to black as hex string

def main():
    width, height = 600, 600
    svg_filename = "tiger.svg"
    
    svg_parser = SVGParser(svg_filename)
    elements = svg_parser.parse()

    rasterizer = Rasterizer(width, height)
    
    for elem in elements:
        try:
            if elem[0] == 'path':
                path_data = elem[1]
                color = elem[2]
                parser = SVGPathParser(path_data)
                polygon = parser.get_polygon()
                if len(polygon) > 2:  # Need at least 3 points for a polygon
                    rasterizer.fill_polygon(polygon, color)
            elif elem[0] == 'rect':
                x, y, w, h = elem[1]
                color = elem[2]
                rasterizer.fill_polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], color)
            elif elem[0] == 'circle':
                cx, cy, r = elem[1]
                color = elem[2]
                steps = 100
                circle_points = []
                for i in range(steps):
                    angle = 2 * math.pi * i / steps
                    x = cx + r * math.cos(angle)
                    y = cy + r * math.sin(angle)
                    circle_points.append((int(x), int(y)))
                rasterizer.fill_polygon(circle_points, color)
        except Exception as e:
            # Skip elements that cause errors
            print(f"Skipping element: {e}")

    rasterizer.save_ppm("output2.ppm")
    print("Saved to output2.ppm")


if __name__ == "__main__":
    main()