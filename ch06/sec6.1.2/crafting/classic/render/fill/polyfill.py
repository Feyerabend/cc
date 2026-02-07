
class Edge:
    def __init__(self, x1, y1, x2, y2):
        # edges must be orderd from top to bottom
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.slope = (x2 - x1) / (y2 - y1) if y1 != y2 else None

    def __repr__(self):
        return f"Edge(({self.x1}, {self.y1}) -> ({self.x2}, {self.y2}))"

    def x_at(self, y): # calculate the x-coordinate on the edge for a given y-coordinate
        if self.slope is None:
            return self.x1
        return self.x1 + (y - self.y1) * self.slope


class Rasterizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]

    def fill_polygon(self, polygon, color, fill_rule="even-odd"):
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
            intersections.sort() # for effective use

            if fill_rule == "even-odd":
                for i in range(0, len(intersections), 2):
                    x_start = int(max(0, min(intersections[i], self.width - 1)))
                    x_end = int(max(0, min(intersections[i + 1], self.width - 1)))
                    for x in range(x_start, x_end + 1):
                        self.canvas[y][x] = color

            elif fill_rule == "winding":
                winding_count = 0
                for x in range(self.width):
                    for edge in active_edges:
                        if edge.x_at(y) == x:
                            winding_count += 1
                    if winding_count % 2 != 0:
                        self.canvas[y][x] = color

    def save_ppm(self, filename):
        with open(filename, 'w') as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            for row in self.canvas:
                for r, g, b in row:
                    f.write(f"{r} {g} {b} ")
                f.write("\n")


class SVGPathParser:
    def __init__(self, path_data):
        self.commands = self.parse_path(path_data)

    def parse_path(self, path_data):
        commands = []
        tokens = path_data.replace(',', ' ').split()
        i = 0
        while i < len(tokens):
            command = tokens[i]
            i += 1
            if command == 'M':  # move to
                x, y = float(tokens[i]), float(tokens[i + 1])
                commands.append(('M', x, y))
                i += 2
            elif command == 'L':  # line to
                x, y = float(tokens[i]), float(tokens[i + 1])
                commands.append(('L', x, y))
                i += 2
            elif command == 'Z':  # close path
                commands.append(('Z',))
            else:
                raise ValueError(f"Unknown command: {command}")
        return commands

    def get_polygon(self):
        polygon = []
        for command in self.commands:
            if command[0] in ('M', 'L'):
                polygon.append((int(command[1]), int(command[2])))
        return polygon


def main():
    width, height = 200, 200
#    svg_path = "M 50 50 L 150 50 L 150 150 L 50 150 Z"
    svg_path = "M 50 50 L 150 50 L 150 150 L 50 150 Z M 50 50 L 50 150 L 100 100 L 100 50 Z M 150 50 L 150 150 L 100 100 L 100 50 Z"
    color = (255, 0, 0)  # red

    parser = SVGPathParser(svg_path)
    polygon = parser.get_polygon()

    rasterizer = Rasterizer(width, height)
    rasterizer.fill_polygon(polygon, color, fill_rule="even-odd")  # alt: "winding"

    rasterizer.save_ppm("output.ppm")
    print("Saved to output.ppm")


if __name__ == "__main__":
    main()
