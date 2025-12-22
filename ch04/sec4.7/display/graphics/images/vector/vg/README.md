
## Vector Representation on Small Devices

We begin with the challenge of displaying SVG images on a Raspberry Pi Pico equipped
with a Pimoroni DisplayPack 2.0. While SVG is a compact and scalable format, full SVG
parsers are complex and memory-intensive--often unsuitable for small embedded systems.
A naïve solution would be to simply render the SVG once on a larger computer, convert
it to a small raster (pixel-based) image, and then display that bitmap directly o
the Pico. That approach works, but it loses the advantages of vector graphics, such
as its scalability, compactness, and geometric precision.

A more interesting approach is to preserve at least part of the vector representation
while still adapting it to the limitations of a pixel-based display. By maintaining
essential vector information, we can support transformations (rotation, scaling, translation)
and potentially achieve better compression. The goal is therefore to find a balance
between *vector fidelity* and *binary compactness*.

You can probably do a better job with this as a project, but the idea is at least
illustrated here.



### *01. SVG Conversion*

We start with any arbitrary SVG image and use an existing SVG parser--for example,
one already available in a modern web browser--to interpret the geometry.
From this, we produce a simplified JSON representation that retains only the essential
elements, typically *paths* consisting of move, line, and curve commands.
This stripped-down form removes styles, gradients, and metadata, leaving a minimal
but somewhat complete geometric description.

### *02. Tokenisation*

Next, the JSON is tokenised to reduce redundancy. This step effectively compresses
the textual representation by mapping frequent command sequences, coordinates, or
symbols to compact tokens. The result is a more efficient intermediate form, still
readable but much smaller than the original JSON.


### *03. Binary Compression*

We then translate the tokenised data into a binary format. This further reduces size
and speeds up loading. Simple, well-chosen compression methods--such as run-length
encoding or delta encoding--are often sufficient here, avoiding the overhead of more
advanced algorithms.


### *04. Decompression and Rendering*

Finally, the compressed data can be unpacked directly on the microcontroller and
rendered on the display. The rendering engine reconstructs the paths, applies the
required transformations, and rasterises the shapes into the frame buffer. Despite
limited memory and processing power, this allows the Pico to display complex vector-derived
images efficiently.


### *05. Your Project*

Fill in the missing parts from the ideas above. Make your own extension to the project(s)!



### Project ..

This workflow maintains a degree of scalability and geometric precision while remaining
realistic for small embedded targets. It bridges the gap between high-level vector
representation and low-level pixel output, demonstrating how ideas from modern computer
graphics can be adapted to microcontroller environments.

