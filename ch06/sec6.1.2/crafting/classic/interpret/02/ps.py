
class GraphicsState:

    def __init__(self):
        self.path = []  # current drawing path
        self.line_width = 1.0
        self.fill_color = (0, 0, 0)
        self.stroke_color = (0, 0, 0)
        self.current_position = (0, 0)
        self.saved_states = []

    def save(self):
        self.saved_states.append({
            "path": list(self.path),
            "line_width": self.line_width,
            "fill_color": self.fill_color,
            "stroke_color": self.stroke_color,
            "current_position": self.current_position
        })

    def restore(self):
        if self.saved_states:
            state = self.saved_states.pop()
            self.path = state["path"]
            self.line_width = state["line_width"]
            self.fill_color = state["fill_color"]
            self.stroke_color = state["stroke_color"]
            self.current_position = state["current_position"]


class Interpreter:
    def __init__(self, rasterizer):
        self.stack = []
        self.graphics_state = GraphicsState()
        self.rasterizer = rasterizer

    def execute(self, program):
        for command in program:
            self._execute_command(command)

    def _execute_command(self, command):
        cmd = command[0]
        args = command[1:]

        if cmd == "newpath":
            self.graphics_state.path = []

        elif cmd == "moveto":
            x, y = args
            self.graphics_state.current_position = (x, y)

        elif cmd == "lineto":
            x, y = args
            self.graphics_state.path.append((self.graphics_state.current_position, (x, y)))
            self.graphics_state.current_position = (x, y)

        elif cmd == "rlineto":
            dx, dy = args
            x, y = self.graphics_state.current_position
            new_x, new_y = x + dx, y + dy
            self.graphics_state.path.append(((x, y), (new_x, new_y)))
            self.graphics_state.current_position = (new_x, new_y)

        elif cmd == "arc":
            cx, cy, radius, start_angle, end_angle = args
            self.graphics_state.path.append(("arc", cx, cy, radius, start_angle, end_angle))

        elif cmd == "closepath":
            self.graphics_state.path.append("close")

        elif cmd == "stroke":
            self.rasterizer.stroke(self.graphics_state.path, self.graphics_state.stroke_color, self.graphics_state.line_width)

        elif cmd == "fill":
            self.rasterizer.fill(self.graphics_state.path, self.graphics_state.fill_color)

        elif cmd == "setlinewidth":
            self.graphics_state.line_width = args[0]

        elif cmd == "setgray":
            gray = args[0]
            self.graphics_state.fill_color = self.graphics_state.stroke_color = (gray, gray, gray)

        elif cmd == "setrgbcolor":
            self.graphics_state.fill_color = self.graphics_state.stroke_color = tuple(args)

        elif cmd == "gsave":
            self.graphics_state.save()

        elif cmd == "grestore":
            self.graphics_state.restore()


class Rasterizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = [[(1.0, 1.0, 1.0) for _ in range(width)] for _ in range(height)]  # white bg

    def stroke(self, path, color, line_width):
        # stroke a path with a specified color (and line width)
        for segment in path:
            if segment == "close":
                continue
            self._draw_line(segment[0], segment[1], color)

    def fill(self, path, color):
        # create an outline of the path by stroking it
        for segment in path:
            if isinstance(segment, tuple):
                self._draw_line(segment[0], segment[1], color)

        # simple flood fill algorithm
        self._flood_fill(color)

    def _draw_line(self, start, end, color): # Bresenham or Wu?
        x1, y1 = start
        x2, y2 = end
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= x1 < self.width and 0 <= y1 < self.height:
                self.canvas[y1][x1] = color
            if x1 == x2 and y1 == y2:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def _flood_fill(self, fill_color):
        seed_x, seed_y = self.width // 2, self.height // 2
        target_color = self.canvas[seed_y][seed_x]

        if target_color == fill_color:
            return  # no infinite recursion

        stack = [(seed_x, seed_y)]
        while stack:
            x, y = stack.pop()
            if 0 <= x < self.width and 0 <= y < self.height and self.canvas[y][x] == target_color:
                self.canvas[y][x] = fill_color
                stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

    def save_to_ppm(self, filename):
        # save the canvas of pixels as a PPM3
        with open(filename, 'w') as f:
            f.write("P3\n")
            f.write(f"{self.width} {self.height}\n")
            f.write("255\n")
            for row in self.canvas:
                for r, g, b in row:
                    f.write(f"{int(r * 255)} {int(g * 255)} {int(b * 255)} ")
                f.write("\n")


# example
rasterizer = Rasterizer(300, 300)
interpreter = Interpreter(rasterizer)

program = [
    ("newpath",),
    ("moveto", 50, 50),
    ("lineto", 250, 50),
    ("lineto", 250, 250),
    ("lineto", 50, 250),
    ("closepath",), # do anything?
    ("setrgbcolor", 0, 0, 1),  # blue? here
    ("fill",), # fill now?
    ("setrgbcolor", 1, 0, 0),  # red? here
    ("setlinewidth", 2), # no width impl.
    ("stroke",),
]
interpreter.execute(program)
rasterizer.save_to_ppm("output2.ppm")


#path = [
#    ((50, 50), (150, 50)),
#    ((150, 50), (100, 150)),
#    ((100, 150), (50, 50))
#]

#rasterizer = Rasterizer(200, 200)
#rasterizer.fill(path, (0, 0, 1))  # fill: blue
#rasterizer.stroke(path, (1, 0, 0), 1)  # stroke: red
#rasterizer.save_to_ppm("triangle.ppm")
