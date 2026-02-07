
import math

class Rasterizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = [['255 255 255' for _ in range(width)] for _ in range(height)]

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            r, g, b = color
            self.canvas[int(y)][int(x)] = f"{r} {g} {b}"

    def draw_line(self, x0, y0, x1, y1, color):
        x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx - dy
        while True:
            self.set_pixel(x0, y0, color)
            if (x0, y0) == (x1, y1):
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def to_ppm(self, filename="output.ppm"):
        with open(filename, "w") as f:
            f.write("P3\n")
            f.write(f"{self.width} {self.height}\n")
            f.write("255\n")
            for row in self.canvas:
                f.write(" ".join(row) + "\n")


class GraphicsState:
    def __init__(self, rasterizer):
        self.rasterizer = rasterizer
        self.line_width = 1
        self.fill_color = (0, 0, 0)  # default black
        self.stroke_color = (0, 0, 0)  # default black
        self.current_position = (0, 0) # coordinate system not ps!
        self.stack = []

    def save(self):
        return self.__dict__.copy()

    def restore(self, state):
        self.__dict__.update(state)


class PostScriptInterpreter:
    def __init__(self, rasterizer):
        self.state = GraphicsState(rasterizer)
        self.graphics_state_stack = []

    def execute(self, program):
        for command in program:
            operation = command[0]
            args = command[1:]
            if operation in self.commands:
                self.commands[operation](*args)
            else:
                raise ValueError(f"Unknown command: {operation}")

    @property
    def commands(self):
        return {
            "moveto": self.moveto,
            "lineto": self.lineto,
            "setrgbcolor": self.setrgbcolor,
            "stroke": self.stroke,
            "save": self.save,
            "restore": self.restore,
            "showpage": self.showpage,
            "newpath": self.newpath,
            "rlineto": self.rlineto,
            "closepath": self.closepath,
            "setgray": self.setgray,
            "fill": self.fill,
            "arc": self.arc,
        }

    def moveto(self, x, y):
        self.state.current_position = (x, y)

    def lineto(self, x, y):
        x0, y0 = self.state.current_position
        self.state.rasterizer.draw_line(x0, y0, x, y, self.state.stroke_color)
        self.state.current_position = (x, y)

    def rlineto(self, dx, dy):
        x0, y0 = self.state.current_position
        self.state.rasterizer.draw_line(x0, y0, x0 + dx, y0 + dy, self.state.stroke_color)
        self.state.current_position = (x0 + dx, y0 + dy)

    def arc(self, x, y, r, start_angle, end_angle):
        start_angle = math.radians(start_angle)
        end_angle = math.radians(end_angle)
        step_count = max(2, int(abs(end_angle - start_angle) / (math.pi / 180)))  # at least 2 steps!

        points = []
        for i in range(step_count + 1):
            t = start_angle + (end_angle - start_angle) * i / step_count
            x_pos = x + r * math.cos(t)
            y_pos = y + r * math.sin(t)
            points.append((x_pos, y_pos))

        x0, y0 = points[0]
        for x1, y1 in points[1:]:
            self.state.rasterizer.draw_line(x0, y0, x1, y1, self.state.stroke_color)
            x0, y0 = x1, y1

    def newpath(self):
        self.state.current_position = (0, 0)

    def closepath(self):
        x0, y0 = self.state.current_position
        self.state.rasterizer.draw_line(x0, y0, self.state.current_position[0], self.state.current_position[1], self.state.stroke_color)

    def setrgbcolor(self, r, g, b):
        self.state.stroke_color = (int(r * 255), int(g * 255), int(b * 255))

    def setgray(self, gray):
        self.state.stroke_color = (int(gray * 255), int(gray * 255), int(gray * 255))

    def fill(self):
        # fill path (not implemented!)
        pass

    def stroke(self):
        # stub for stroke, as lines are drawn immediately!
        pass

    def save(self):
        self.graphics_state_stack.append(self.state.save())

    def restore(self):
        if self.graphics_state_stack:
            self.state.restore(self.graphics_state_stack.pop())
        else:
            raise ValueError("Graphics state stack is empty")

    def showpage(self):
        self.state.rasterizer.to_ppm()


# example
rasterizer = Rasterizer(300, 300)
interpreter = PostScriptInterpreter(rasterizer)

program = [
    # draw and fill a rectangle
    ("newpath",),
    ("fill",),
    ("moveto", 100, 100),
    ("rlineto", 50, 0),
    ("rlineto", 0, 50),
    ("rlineto", -50, 0),
    ("rlineto", 0, -50),
    ("setgray", 0.8),  # light gray fill -- parsed but not rendered
    ("closepath",),

    # draw and stroke a circle
    ("newpath",),
    ("arc", 200, 200, 25, 0, 360),
    ("setrgbcolor", 1, 0, 0),  # red stroke?
    ("stroke",),
    ("showpage",),
]

interpreter.execute(program)
