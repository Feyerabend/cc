import re
import math
from xml.etree import ElementTree as ET


class Edge:
    def __init__(self, x1, y1, x2, y2):
        if y1 > y2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.slope = (x2 - x1) / (y2 - y1) if y1 != y2 else None

    def x_at(self, y):
        if self.slope is None:
            return self.x1
        return self.x1 + (y - self.y1) * self.slope


class Rasterizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = [[(255, 255, 255) for _ in range(width)]
                       for _ in range(height)]

    def _clamp(self, x, y):
        return (
            max(0, min(self.width - 1, int(x))),
            max(0, min(self.height - 1, int(y)))
        )

    def fill_polygon(self, polygon, color):
        if not polygon or len(polygon) < 3:
            return

        edges = []
        for i in range(len(polygon)):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]
            if y1 != y2:
                edges.append(Edge(x1, y1, x2, y2))

        if not edges:
            return

        min_y = max(0, int(min(e.y1 for e in edges)))
        max_y = min(self.height - 1, int(max(e.y2 for e in edges)))

        for y in range(min_y, max_y + 1):
            active = [e for e in edges if e.y1 <= y < e.y2]
            xs = sorted(e.x_at(y) for e in active)

            for i in range(0, len(xs) - 1, 2):
                x0 = int(xs[i])
                x1 = int(xs[i + 1])
                if x0 > x1:
                    x0, x1 = x1, x0
                for x in range(max(0, x0), min(self.width, x1 + 1)):
                    self.canvas[y][x] = color

    def draw_line(self, p0, p1, color):
        x0, y0 = self._clamp(*p0)
        x1, y1 = self._clamp(*p1)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.canvas[y0][x0] = color
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def stroke_polygon(self, polygon, color):
        if not polygon or len(polygon) < 2:
            return
        for i in range(len(polygon)):
            self.draw_line(
                polygon[i],
                polygon[(i + 1) % len(polygon)],
                color
            )

    def save_ppm(self, filename):
        with open(filename, "w") as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            for row in self.canvas:
                for r, g, b in row:
                    f.write(f"{r} {g} {b} ")
                f.write("\n")


class SVGPathParser:
    NUMBER = r'[-+]?(?:\d*\.\d+|\d+)'
    TOKEN_RE = re.compile(rf'[MmLlCcZz]|{NUMBER}')

    def __init__(self, d):
        self.tokens = self.TOKEN_RE.findall(d)
        self.pos = 0

    def _next(self):
        if self.pos >= len(self.tokens):
            return None
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def get_polygon(self, tolerance=1.0):
        poly = []
        cur = (0.0, 0.0)
        start = None
        cmd = None

        while True:
            t = self._next()
            if t is None:
                break

            if re.match(r'[MmLlCcZz]', t):
                cmd = t
            else:
                # implicit lineto
                self.pos -= 1

            try:
                if cmd in ("M", "m"):
                    x = float(self._next())
                    y = float(self._next())
                    cur = (x, y)
                    start = cur
                    poly.append((int(x), int(y)))
                    cmd = "L" if cmd == "M" else "l"

                elif cmd in ("L", "l"):
                    x = float(self._next())
                    y = float(self._next())
                    cur = (x, y)
                    poly.append((int(x), int(y)))

                elif cmd in ("C", "c"):
                    p0 = cur
                    x1, y1 = float(self._next()), float(self._next())
                    x2, y2 = float(self._next()), float(self._next())
                    x3, y3 = float(self._next()), float(self._next())
                    p3 = (x3, y3)
                    segments = self._subdivide_bezier(
                        p0, (x1, y1), (x2, y2), p3, tolerance
                    )
                    for x, y in segments:
                        poly.append((int(x), int(y)))
                    cur = p3

                elif cmd in ("Z", "z"):
                    if start:
                        poly.append((int(start[0]), int(start[1])))
                        cur = start

            except (TypeError, ValueError):
                break

        return poly

    def _subdivide_bezier(self, p0, p1, p2, p3, tol):
        mx = (p0[0] + p3[0]) * 0.5
        my = (p0[1] + p3[1]) * 0.5
        cx = (p1[0] + p2[0]) * 0.5
        cy = (p1[1] + p2[1]) * 0.5

        if abs(mx - cx) + abs(my - cy) < tol:
            return [p3]

        m01 = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5)
        m12 = ((p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5)
        m23 = ((p2[0] + p3[0]) * 0.5, (p2[1] + p3[1]) * 0.5)
        m012 = ((m01[0] + m12[0]) * 0.5, (m01[1] + m12[1]) * 0.5)
        m123 = ((m12[0] + m23[0]) * 0.5, (m12[1] + m23[1]) * 0.5)
        mid = ((m012[0] + m123[0]) * 0.5, (m012[1] + m123[1]) * 0.5)

        left = self._subdivide_bezier(p0, m01, m012, mid, tol)
        right = self._subdivide_bezier(mid, m123, m23, p3, tol)
        return left[:-1] + right



class SVGParser:
    def __init__(self, filename):
        self.root = ET.parse(filename).getroot()

    def parse(self):
        out = []
        for el in self.root:
            if el.tag.endswith("path"):
                d = el.attrib.get("d", "")
                fill = self._color(el.attrib.get("style", ""), "fill")
                stroke = self._color(el.attrib.get("style", ""), "stroke")
                out.append(("path", d, fill, stroke))
        return out

    def _color(self, style, key):
        m = re.search(rf"{key}:\s*(#[0-9a-fA-F]{{6}})", style)
        if not m:
            return None
        h = m.group(1)
        return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))



def main():
    width, height = 600, 600
    svg = SVGParser("tiger.svg")
    rast = Rasterizer(width, height)

    for kind, d, fill, stroke in svg.parse():
        if kind != "path":
            continue
        poly = SVGPathParser(d).get_polygon()
        if fill:
            rast.fill_polygon(poly, fill)
        if stroke:
            rast.stroke_polygon(poly, stroke)

    rast.save_ppm("output3.ppm")


if __name__ == "__main__":
    main()
