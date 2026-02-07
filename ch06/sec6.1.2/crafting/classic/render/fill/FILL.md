
## Fill Polygons

Filling a polygon in computer graphics involves determining which pixels
inside a defined boundary should be colored. This process, essential for
rendering shapes and regions, can be approached using simple or sophisticated
algorithms, depending on the complexity of the polygon and the desired visual
effect.

### Flood Fill Algorithm

The flood-fill algorithm is a simple and intuitive method to fill contiguous
areas in raster graphics.

1. Start from a seed pixel *inside* the polygon.

2. Recursively or iteratively:
   - Check adjacent pixels (usually four or eight neighbors).
   - If the pixel hasn’t been filled and matches the target color,
     fill it and add it to the list of pixels to process.

3. Continue until no more adjacent pixels meet the criteria.


Advantages:
- Simple to implement.
- Works well for contiguous regions with a single boundary.

Disadvantages:
- Inefficient for large or complex polygons.
- Risk of stack overflow in recursive implementations for large areas.
- Requires a pre-existing boundary to work.


#### Example

```python
def flood_fill(canvas, x, y, target_color, fill_color):
    if target_color == fill_color:
        return

    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if canvas[cy][cx] == target_color:
            canvas[cy][cx] = fill_color
            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
```

### Winding Number and Even-Odd Rule

The winding number and even-odd rule are used to determine if a
point lies inside a polygon. These rules are more sophisticated and
suitable for non-contiguous, complex polygons.


#### Even-Odd Rule

- Concept: Draw an imaginary ray from the test point to infinity.

- Rule: Count the number of edges the ray crosses. If the count is
  odd, the point is inside the polygon; if even, it’s outside.

#### Winding Number Rule
- Concept: Count how many times the polygon winds around the test point.
- Calculation:
	* Assign a direction to each edge (clockwise or counterclockwise).
	* Increment or decrement a counter based on the direction of crossing.
	* A nonzero result indicates the point is inside the polygon.

Advantages
- Handles complex polygons, including those with holes or overlapping edges.
- Works well with non-contiguous boundaries.

Disadvantages
- Computationally more intensive than flood fill.
- Requires preprocessing the polygon edges.


#### Example Even-Odd Rule

```python
def is_point_inside_polygon(point, polygon):
    x, y = point
    crossings = 0
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        if (y1 > y) != (y2 > y):  # Check if point is between the y-coordinates of the edge
            intersect_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < intersect_x:
                crossings += 1
    return crossings % 2 == 1
```

Comparison

|Feature|Flood Fill|Even-Odd/Winding Rule|
|-------|----------|---------------------|
|Complexity|Simple|More advanced|
|Use Case|Filling contiguous regions|Arbitrary, complex polygons|
|Efficiency|Inefficient for large areas|More efficient for large shapes|
|Handling Holes|Not suitable|Handles holes and overlapping edges|


Applications
1. Flood Fill:
   - Painting tools in graphic software (e.g. "bucket fill").
   - Simple 2D games where regions are enclosed by boundaries.

2. Even-Odd/Winding Rule:
   - Rendering polygons in vector graphics software (e.g., SVGs).
   - 2D and 3D rendering engines for determining pixel coverage.

Understanding these algorithms gives you the foundation for implementing
polygon filling in graphics software, balancing simplicity and computational
requirements based on the application’s needs.
