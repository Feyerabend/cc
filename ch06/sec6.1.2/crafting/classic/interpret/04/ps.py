import logging
import math

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GraphicsState:
    def __init__(self):
        self.path = []
        self.line_width = 1.0
        self.fill_color = (0, 0, 0)
        self.stroke_color = (0, 0, 0)
        self.current_position = (0, 0)
        self.subpath_start = (0, 0)
        self.saved_states = []

    def save(self):
        logging.debug("Saving state")
        self.saved_states.append({
            "path": self.path.copy(),
            "line_width": self.line_width,
            "fill_color": self.fill_color,
            "stroke_color": self.stroke_color,
            "current_position": self.current_position,
            "subpath_start": self.subpath_start
        })

    def restore(self):
        if self.saved_states:
            state = self.saved_states.pop()
            logging.debug("Restoring state")
            self.path = state["path"]
            self.line_width = state["line_width"]
            self.fill_color = state["fill_color"]
            self.stroke_color = state["stroke_color"]
            self.current_position = state["current_position"]
            self.subpath_start = state["subpath_start"]

class Command:
    def execute(self, interpreter):
        raise NotImplementedError("Execute must be implemented by subclasses")

class NewPathCommand(Command):
    def execute(self, interpreter):
        interpreter.graphics_state.path = []

class MoveToCommand(Command):
    def execute(self, interpreter):
        y, x = interpreter.pop_two()
        x, y = float(x), float(y)
        interpreter.graphics_state.path.append(('moveto', (x, y)))
        interpreter.graphics_state.current_position = (x, y)
        interpreter.graphics_state.subpath_start = (x, y)

class LineToCommand(Command):
    def execute(self, interpreter):
        y, x = interpreter.pop_two()
        x, y = float(x), float(y)
        interpreter.graphics_state.path.append(('lineto', (x, y)))
        interpreter.graphics_state.current_position = (x, y)

class CurveToCommand(Command):
    def execute(self, interpreter):
        y3, x3 = interpreter.pop_two()
        y2, x2 = interpreter.pop_two()
        y1, x1 = interpreter.pop_two()
        x1, y1, x2, y2, x3, y3 = float(x1), float(y1), float(x2), float(y2), float(x3), float(y3)
        interpreter.graphics_state.path.append(('curveto', ((x1, y1), (x2, y2), (x3, y3))))
        interpreter.graphics_state.current_position = (x3, y3)

class ClosePathCommand(Command):
    def execute(self, interpreter):
        interpreter.graphics_state.path.append(('closepath', ))

class SetLineWidthCommand(Command):
    def execute(self, interpreter):
        line_width = float(interpreter.stack.pop())
        interpreter.graphics_state.line_width = line_width

class SetGrayCommand(Command):
    def execute(self, interpreter):
        gray = float(interpreter.stack.pop())
        color = (gray, gray, gray)
        interpreter.graphics_state.fill_color = color
        interpreter.graphics_state.stroke_color = color

class SetRGBColorCommand(Command):
    def execute(self, interpreter):
        b, g, r = interpreter.pop_three()
        r, g, b = float(r), float(g), float(b)
        color = (r, g, b)
        interpreter.graphics_state.fill_color = color
        interpreter.graphics_state.stroke_color = color

class StrokeCommand(Command):
    def execute(self, interpreter):
        path = interpreter.graphics_state.path
        color = interpreter.graphics_state.stroke_color
        line_width = interpreter.graphics_state.line_width
        interpreter.rasterizer.stroke(path, color, line_width)

class FillCommand(Command):
    def execute(self, interpreter):
        path = interpreter.graphics_state.path
        color = interpreter.graphics_state.fill_color
        interpreter.rasterizer.fill(path, color)

class SaveCommand(Command):
    def execute(self, interpreter):
        interpreter.graphics_state.save()

class RestoreCommand(Command):
    def execute(self, interpreter):
        interpreter.graphics_state.restore()

class Interpreter:
    def __init__(self, rasterizer):
        self.stack = []
        self.graphics_state = GraphicsState()
        self.rasterizer = rasterizer
        self.commands = {
            "newpath": NewPathCommand(),
            "moveto": MoveToCommand(),
            "lineto": LineToCommand(),
            "curveto": CurveToCommand(),
            "closepath": ClosePathCommand(),
            "setlinewidth": SetLineWidthCommand(),
            "setgray": SetGrayCommand(),
            "setrgbcolor": SetRGBColorCommand(),
            "stroke": StrokeCommand(),
            "fill": FillCommand(),
            "gsave": SaveCommand(),
            "grestore": RestoreCommand(),
        }

    def execute(self, program):
        for token in program:
            if isinstance(token, (int, float)):
                self.stack.append(token)
            elif isinstance(token, str):
                if token in self.commands:
                    logging.debug("Executing command: %s", token)
                    self.commands[token].execute(self)
                else:
                    raise ValueError(f"Unknown command: {token}")
            else:
                raise ValueError(f"Invalid token: {token}")

    def pop_two(self):
        return self.stack.pop(), self.stack.pop()

    def pop_three(self):
        return self.stack.pop(), self.stack.pop(), self.stack.pop()

class Rasterizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = [[(1.0, 1.0, 1.0) for _ in range(width)] for _ in range(height)]

    def _plot(self, x, y, intensity, color):
        x = int(x)
        y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            r, g, b = color
            br, bg, bb = self.canvas[y][x]
            self.canvas[y][x] = (
                r * intensity + br * (1 - intensity),
                g * intensity + bg * (1 - intensity),
                b * intensity + bb * (1 - intensity),
            )

    def stroke(self, path, color, line_width):
        current = (0, 0)
        substart = (0, 0)
        for op in path:
            op_type = op[0]
            args = op[1] if len(op) > 1 else None
            if op_type == 'moveto':
                current = args
                substart = args
            elif op_type == 'lineto':
                self._draw_line(current, args, color, line_width)
                current = args
            elif op_type == 'curveto':
                self._draw_bezier(current, args[0], args[1], args[2], color, line_width)
                current = args[2]
            elif op_type == 'closepath':
                self._draw_line(current, substart, color, line_width)
                current = substart

    def fill(self, path, color):
        polygons = []
        current_points = []
        current = (0, 0)
        substart = (0, 0)
        for op in path:
            op_type = op[0]
            args = op[1] if len(op) > 1 else None
            if op_type == 'moveto':
                if current_points:
                    polygons.append(current_points)
                current_points = [args]
                current = args
                substart = args
            elif op_type == 'lineto':
                current_points.append(args)
                current = args
            elif op_type == 'curveto':
                flat = self._flatten_bezier(current, args[0], args[1], args[2])
                current_points.extend(flat[1:])
                current = args[2]
            elif op_type == 'closepath':
                if current_points:
                    current_points.append(substart)
                    polygons.append(current_points)
                    current_points = []
        if current_points:
            polygons.append(current_points)
        for poly in polygons:
            self._fill_polygon(poly, color)

    def _flat_enough(self, p0, p1, p2, p3):
        d1 = self._distance_point_line(p1, p0, p3)
        d2 = self._distance_point_line(p2, p0, p3)
        return max(d1, d2) < 1.0

    def _distance_point_line(self, p, a, b):
        abx = b[0] - a[0]
        aby = b[1] - a[1]
        apx = p[0] - a[0]
        apy = p[1] - a[1]
        proj = apx * abx + apy * aby
        len2 = abx**2 + aby**2
        if len2 == 0:
            return math.sqrt(apx**2 + apy**2)
        t = proj / len2
        if t < 0:
            return math.sqrt(apx**2 + apy**2)
        if t > 1:
            dx = p[0] - b[0]
            dy = p[1] - b[1]
            return math.sqrt(dx**2 + dy**2)
        close_x = a[0] + t * abx
        close_y = a[1] + t * aby
        dx = p[0] - close_x
        dy = p[1] - close_y
        return math.sqrt(dx**2 + dy**2)

    def _flatten_bezier(self, p0, p1, p2, p3):
        points = [p0]
        def recurse(p0, p1, p2, p3):
            if self._flat_enough(p0, p1, p2, p3):
                points.append(p3)
            else:
                p01 = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                p12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                p23 = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
                p012 = ((p01[0] + p12[0]) / 2, (p01[1] + p12[1]) / 2)
                p123 = ((p12[0] + p23[0]) / 2, (p12[1] + p23[1]) / 2)
                p0123 = ((p012[0] + p123[0]) / 2, (p012[1] + p123[1]) / 2)
                recurse(p0, p01, p012, p0123)
                recurse(p0123, p123, p23, p3)
        recurse(p0, p1, p2, p3)
        return points

    def _draw_bezier(self, p0, p1, p2, p3, color, line_width):
        points = self._flatten_bezier(p0, p1, p2, p3)
        for i in range(len(points) - 1):
            self._draw_line(points[i], points[i + 1], color, line_width)

    def _fill_polygon(self, points, color):
        if not points:
            return
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        if min_y == max_y:
            return
        scan_min = math.floor(min_y + 1e-6)
        scan_max = math.floor(max_y - 1e-6)
        for y in range(scan_min, scan_max + 1):
            intersections = []
            n = len(points)
            for i in range(n):
                p1 = points[i]
                p2 = points[(i + 1) % n]
                if p1[1] == p2[1]:
                    continue
                miny = min(p1[1], p2[1])
                maxy = max(p1[1], p2[1])
                if not (miny <= y < maxy):
                    continue
                x_inter = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                direction = 1 if p1[1] < p2[1] else -1
                intersections.append((x_inter, direction))
            if not intersections:
                continue
            intersections.sort(key=lambda t: t[0])
            winding = 0
            prev_x = -math.inf
            for x_inter, dir in intersections:
                if winding != 0:
                    x_start = max(math.ceil(prev_x + 1e-6), 0)
                    x_end = min(math.floor(x_inter - 1e-6), self.width - 1)
                    if x_start <= x_end:
                        for x in range(x_start, x_end + 1):
                            self.canvas[y][x] = color
                winding += dir
                prev_x = x_inter

    def _draw_line(self, start, end, color, line_width=1.0):
        if line_width <= 0:
            return
        half_w = line_width / 2.0
        x0, y0 = start
        x1, y1 = end
        dx = x1 - x0
        dy = y1 - y0
        len_sq = dx**2 + dy**2
        if len_sq == 0:
            return
        min_x = min(x0, x1) - half_w - 1
        max_x = max(x0, x1) + half_w + 1
        min_y = min(y0, y1) - half_w - 1
        max_y = max(y0, y1) + half_w + 1
        left = max(0, math.floor(min_x))
        right = min(self.width, math.ceil(max_x))
        top = max(0, math.floor(min_y))
        bottom = min(self.height, math.ceil(max_y))
        for iy in range(top, bottom):
            for ix in range(left, right):
                px = ix + 0.5
                py = iy + 0.5
                apx = px - x0
                apy = py - y0
                proj = apx * dx + apy * dy
                t = proj / len_sq
                if t < 0 or t > 1:
                    continue
                close_x = x0 + t * dx
                close_y = y0 + t * dy
                dist = math.sqrt((px - close_x)**2 + (py - close_y)**2)
                if dist > half_w:
                    continue
                intensity = 1 - (dist / half_w)
                self._plot(ix, iy, intensity, color)

    def save_to_ppm(self, filename):
        with open(filename, 'w') as f:
            f.write("P3\n")
            f.write(f"{self.width} {self.height}\n")
            f.write("255\n")
            for row in self.canvas:
                for pixel in row:
                    r, g, b = pixel
                    f.write(f"{int(r * 255)} {int(g * 255)} {int(b * 255)} ")
                f.write("\n")

if __name__ == "__main__":
    rasterizer = Rasterizer(300, 300)
    interpreter = Interpreter(rasterizer)
    # Insert one of the sample programs here, e.g.:
    program = [
        "newpath",
        150, 100, "moveto",  # Start at bottom
        150, 55.228, 194.772, 10, 240, 10, "curveto",  # Bottom arc
        285.228, 10, 330, 55.228, 330, 100, "curveto",  # Right arc
        330, 145.228, 285.228, 190, 240, 190, "curveto",  # Top arc
        194.772, 190, 150, 145.228, 150, 100, "curveto",  # Left arc
        "closepath",
        1, 0, 0, "setrgbcolor",  # Red
        "fill",
    ]
    interpreter.execute(program)
    rasterizer.save_to_ppm("output.ppm")

'''
    program = [
        "newpath",
        50, 50, "moveto",
        250, 50, "lineto",
        250, 250, "lineto",
        50, 250, "lineto",
        "closepath",
        0, 0, 1, "setrgbcolor",  # Set blue for fill/stroke
        "fill",
        1, 0, 0, "setrgbcolor",  # Set red for stroke
        2, "setlinewidth",
        "stroke",
    ]

    program = [
        "newpath",
        50, 50, "moveto",
        100, 200, 150, 0, 200, 150, "curveto",  # Curve from (50,50) to (200,150) with controls (100,200) and (150,0)
        250, 50, "lineto",
        200, 0, 150, 200, 100, 50, "curveto",  # Curve back to (100,50) with controls (200,0) and (150,200)
        "closepath",
        0, 1, 0, "setrgbcolor",  # Green
        "fill",
        0, "setgray",  # Black (grayscale 0)
        3, "setlinewidth",
        "stroke",
    ]

    program = [
        "newpath",
        50, 50, "moveto",
        150, 50, "lineto",
        150, 150, "lineto",
        50, 150, "lineto",
        "closepath",
        0.5, "setgray",  # Medium gray
        "fill",  # Fill first rect

        "gsave",  # Save state
        "newpath",
        100, 100, "moveto",
        250, 100, "lineto",
        250, 250, "lineto",
        100, 250, "lineto",
        "closepath",
        0, 0, 1, "setrgbcolor",  # Blue
        4, "setlinewidth",
        "stroke",  # Stroke second rect
        "grestore",  # Restore to previous state (gray, no path changes affect original)
    ]

    program = [
        "newpath",
        150, 100, "moveto",  # Start at bottom
        150, 55.228, 194.772, 10, 240, 10, "curveto",  # Bottom arc
        285.228, 10, 330, 55.228, 330, 100, "curveto",  # Right arc
        330, 145.228, 285.228, 190, 240, 190, "curveto",  # Top arc
        194.772, 190, 150, 145.228, 150, 100, "curveto",  # Left arc
        "closepath",
        1, 0, 0, "setrgbcolor",  # Red
        "fill",
    ]
'''