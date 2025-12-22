
## Vector text

Vector text is a method of representing and rendering characters using geometric shapes
rather than pixel-based bitmaps. Vector text stores each character as a series of *line segments*
or *curves* defined by mathematical coordinates. Instead of saying "pixel (10,15) is on, pixel (10,16) is on...",
vector text says "draw a line from point (0,0) to point (5,10)".


### Advantages

1. *Scalable*: You can make text any size without losing quality or getting pixelation
2. *Transformable*: Easy to rotate, skew, or apply other transformations
3. *Memory efficient*: A few coordinates take less space than storing every pixel
4. *Smooth*: At any scale, the text maintains clean edges (as long as your renderer supports it)


Example: In the code:

#### Character Definition
Each character is stored as a list of line segments:
```python
'A': [((0, 0), (2.5, 10)), ((2.5, 10), (5, 0)), ((1, 5), (4, 5))]
```
This says: "To draw 'A', draw three lines: one from bottom-left to top-center,
one from top-center to bottom-right, and one horisontal crossbar."

#### Rendering Process
1. *For each character*, retrieve its line segment definitions
2. *For each line segment*, apply any transformations (scale, rotation, translation)
3. *Draw the line* using Bresenham's algorithm (which determines which pixels to light
   up for a line between two points)

#### Affine Transformations
The code uses *affine transformations*, a mathematical way to combine multiple operations:
- *Scale*: Make text bigger or smaller
- *Rotate*: Spin text around a point
- *Translate*: Move text to a position
- *Shear*: Slant text (like italics)

These are represented as a 2x3 matrix that efficiently combines all transformations
into one operation per point.


### Comparison to Bitmap Fonts

*Bitmap fonts* store each character as a grid of pixels--simple but fixed-size.
To get 10 different sizes, you need 10 different bitmap sets, if you do not convert
the maps in a crude manner like doubling pixels.

*Vector fonts* store the mathematical description once, then can render at any size,
angle, or transformation on-the-fly.

This is why professional (typesetting) fonts (TrueType, OpenType) use vector definitions.
They work perfectly whether you're printing at 300 DPI or displaying on a low-res screen.


![Vector text](./../../../../../../assets/image/display/vectortext.png)
