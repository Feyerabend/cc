
## Graphics and 3D

The choice of C, Python, and JavaScript simplifies the approach to programming,
but it also introduces certain limitations. As seen in the collection of C and
Python [files](./c/), producing graphics without direct access to a rendering window
results in modest visual output. Instead of real-time rendering, images are 
generated, sometimes assembled into animated GIFs.

Previously in ch04 we also hinted at 3D graphics with
[games](./../../../ch04/sec4.7/display/games/c/maze/)
as an application in programming the Raspberry Pico with a Pimorni DisplayPack 2.0.

The [JavaScript](./js/) implementations, however, are generally easier to follow.
The Canvas API enables richer graphics, and handling user input—particularly from
the keyboard—is more straightforward. This environment provides immediate visual
feedback, which is especially valuable when experimenting, prototyping, or learning.

Graphics programming is not solely about games; it extends to simulations,
data visualisation, user interfaces, and interactive tools. Nevertheless, if the goal
is to begin developing games, the choice of setup becomes critically important. Games
are among the most demanding types of software, often pushing hardware to its
limits in terms of processing power, memory, and rendering performance.

For this reason, a more specialised technical foundation is often necessary. Preparing
for game development may involve learning graphics pipelines, understanding frame-based
rendering, managing performance constraints, and working with engines or frameworks
designed for real-time interaction. Such preparation helps bridge the gap between
simple graphical experiments and the complexity of modern games.

In essence, the tools and languages chosen shape both the learning experience and
the scope of achievable projects. Simpler environments reduce barriers to entry,
while more advanced setups unlock greater creative and technical possibilities.

One valuable source is to learn graphics with the primary aim of gaming at:
[https://scratchapixel.com/index.html](https://scratchapixel.com/index.html).

