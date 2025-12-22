
## Games

Not every, but many digital games take their departure from the visual. In the early history of arcade and video games,
the attraction often lay first in what players could see--the colours, shapes, and movement on the screen--even before
the depth of interaction was considered. Games like *Pong* (1972) demonstrated how a simple visual metaphor, two paddles
and a bouncing ball, could be enough to sustain competitive play. Similarly, *Space Invaders* (1978) and *Pac-Man* (1980)
relied heavily on striking visual identities: rows of alien sprites marching downward, or a yellow character pursued
through a neon maze. These designs were simple due to technical constraints, but their visual impact made them immediately
recognisable and compelling in a crowded arcade hall.


### Tetris

Tetris, however, represents a different strand of development. Its appeal is not based on character animation, narrative
images, or graphic spectacle. Instead, it reduces the visual field to the barest of forms: blocks made of four squares,
falling at a constant pace. Here, the focus shifts from visual recognition to cognitive challenge--from how the game looks
to how the player organises and anticipates patterns. This marks a significant divergence in digital game history. While
many arcade titles enticed players with characters and environments that could be "seen" as a form of story or identity,
Tetris drew players into a purely abstract, logical puzzle, visual only in the sense of geometry and spatial fit.

Thus, Tetris illustrates that not all digital games are visually driven in the same sense. Some games use imagery to
construct a world or characters with which the player engages, while others, like Tetris, use minimal visuals as a
vehicle for mechanics that are almost entirely cognitive. The history of video games therefore contains both traditions:
one built on spectacle and representation, the other on abstraction and mental engagement, both using the screen but
for very different ends.


### Racer

One of my earliest memories of arcade games goes back to *Night Driver* (1976) and *Gun Fight*--also known in Japan as
*Western Gun* (1975). Which company actually brought those cabinets to Sweden I could never say; at the time, they simply
appeared in restaurants and cafés as if by magic, their origins unknown and unimportant to us as young players.

Night Driver was always a precarious experience, since the steering wheels on the cabinets were often broken or loose,
making what was already a crude simulation of driving into something almost tragic to play. Gun Fight was different:
two cowboys duelling across a screen, firing through cacti and wooden obstacles. But the game depended on having an
opponent, and in my case that usually meant my sister, who had little interest in the gameplay--or at least that
was how I perceived it.

Racing games provide a useful counterpoint to the minimalism of Tetris. From the earliest examples such as *Night Driver*
but also later *Pole Position* (1982), the focus was overwhelmingly visual: the illusion of speed, the winding of
the road, and the shifting perspective of the horizon line. The player’s engagement depended as much on the sensation 
of movement across a landscape as on the underlying mechanics of steering and avoiding obstacles. In the arcade,
the physical cabinet often reinforced this visual immersion, surrounding the player with a wheel, pedals, and
sometimes even a moving seat. Here, the visual design aimed to replicate an external world--the road, the track,
the rival cars--and the appeal lay in inhabiting that simulated environment.

Placed alongside a game like Tetris, racing games highlight two very different traditions in digital play. Racing relies
on spectacle, the recreation of a recognisable activity through dynamic graphics and motion cues. Tetris, by contrast,
strips away any reference to a real-world activity and situates its challenge purely within the manipulation of abstract
forms. Both genres depend on the screen, but one does so to create an illusion of realism, the other to pose
an intellectual problem. This divergence shows how video games can evolve from the same technological
basis--the pixel and the display--yet move in profoundly different aesthetic and experiential directions.



### Project: Asteroids

You are tasked with recreating and improving a version of the iconic Asteroids game on the Raspberry Pi Pico
with a 320×240 ST7789 Display Pack. Originally released by Atari in 1979, Asteroids is a classic arcade title
in which the player pilots a spaceship, fires at drifting rocks, and avoids collisions—all rendered in
vector-style graphics. In this project, you begin with an existing codebase, but it suffers from a clear
problem: screen flickering. Your challenge is to eliminate this flicker while keeping the game responsive
within the Pico’s constraints (264 KB RAM, 133 MHz CPU). Along the way, you will document your process,
the tools you use, the difficulties you encounter, and the solutions you devise—gaining practical
experience in embedded programming.

Before diving in, however, it is worth pausing to reflect. The current implementation is crude, perhaps
even “bad.” This raises a common question in real-world development: is the existing codebase worth
building on at all? Or would it be wiser to discard it and design a fresh solution from the ground up?
This perspective treats code not as a final product but as a medium for exploration--__code as thinking__.
In this case, the program is small and malleable, making it a useful playground for testing new ideas
before committing to a larger redesign.


#### Project Objectives
- Understand the provided code and get it running on your Raspberry Pi Pico.
- Identify why the game flickers during gameplay.
- Experiment with at least one solution to reduce or eliminate flickering.
- Measure the impact of your changes (e.g., FPS, memory usage, visual quality).
- Document your work, including the history of *Asteroids*, your code changes,
  tools used, issues faced, and how you addressed them.


#### Getting Started

You'll need:
- *Hardware*: Raspberry Pi Pico 2 (the original is a bit too slow for this code),
  ST7789 Display Pack 2.0 (320x240), USB cable for flashing and debugging.
- *Software*: Pico SDK (install via the official guide), CMake, and a
  C compiler (e.g., GCC for ARM).
- *Files Provided* (wrapped below in an artifact):
  - `main.c`: Core game logic (ship, bullets, asteroids, collision detection).
  - `display.h`: Defines display and button interfaces.
  - `display.c`: Low-level display driver using SPI and DMA.
  - `CMakeLists.txt`: Build configuration.


*Possible Setup Steps*:
1. Clone the Pico SDK if not already installed.
2. Create a project directory with the provided files.
3. Run: `mkdir build; cd build; cmake ..; make`.
4. Flash the generated `asteroids_pico.uf2` to your Pico.
5. Connect via serial (e.g., `minicom -D /dev/ttyACM0`) to see debug output.


*Controls*:
- *B*: Turn left
- *Y*: Turn right
- *A*: Thrust
- *X*: Shoot (or restart when game over)
- *RGB LED*: Shows game state (blue for thrust,
  yellow for shooting, green for idle, red for game over).


#### Task Details

The starter code works but flickers because it clears old object positions
(using bounding rectangles) before drawing new ones, causing visible (black out)
flashes. Your goal is to improve the display handling to make the game smoother
while respecting these constraints:
- *Memory*: ~512KB total RAM. A full 320x240 16-bit frame buffer uses ~150KB.
- *Performance*: Target 30+ FPS. SPI transfers for large blits (~10-20ms at 31.25MHz)
  can slow things down.
- *No External Libraries*: Use only the Pico SDK.

*Experiments to Try* (Choose 1-2):
1. *Optimise Dirty Rectangles*: Merge overlapping bounding rectangles to reduce
   clears. Modify `game_loop()` to clear fewer areas.
2. *Partial Frame Buffer*: Use a small buffer (e.g., 32KB for a 64x64 tile)
   for changed regions. Track dirty areas, composite them, and blit only those.
3. *Full Frame Buffer*: Allocate `uint16_t frame_buffer[320*240]` in `main.c`.
   Redirect drawing functions (e.g., `draw_line_clipped`) to the buffer, then use
   `display_blit_full`. Clear the buffer each frame with `memset`.
4. *Reduce Complexity*: Lower asteroid vertices (e.g., from 6 to 4), cap bullets/asteroids,
   or skip edge draws.
5. *SPI/DMA Tweaks*: Increase SPI speed (up to 62.5MHz) or overclock Pico (e.g.,
   `set_sys_clock_khz(200000, true)`). Test stability.
6. *V-Sync Approximation*: Use `absolute_time_t` to sync updates to ~50Hz, avoiding
   mid-frame SPI conflicts.

*Measurement Tips*:
- *FPS*: Add a counter in `game_loop()`; `printf` every second
  (`to_ms_since_boot(get_absolute_time())`).
- *Memory*: Estimate free RAM with
  `extern char __StackLimit; printf("Free RAM: %dKB\n", (uint32_t)&__StackLimit - (uint32_t)malloc(1));`.
- *Flicker*: Observe on hardware or record video.
- *Profiling*: Time sections (e.g., clear, draw, blit) with `absolute_time_t`.


#### Deliverable
Submit:
1. Your modified code (update `main.c` or other files as needed).
2. A report (1-2 pages) covering:
   - *History of Asteroids*: Briefly describe its origins (1979, Atari, vector graphics, inspired by Spacewar!).
   - *Code Overview*: Summarize what `main.c`, `display.h`, and `display.c` do (e.g., game logic, display driver).
   - *Tools Used*: List hardware, SDK, and build process.
   - *Flaws Found*: Explain flickering and any other issues (e.g., slow FPS, button jitter).
   - *Solutions Tried*: Describe your approach (e.g., full buffer), code changes, and why you chose it.
   - *Results*: Report FPS, memory usage, and flicker improvement. Note failures
     (e.g., "Double buffering crashed due to 300KB RAM usage").
   - *Lessons Learned*: What worked, what didn’t, and what you’d try next (e.g., sound via PWM).


#### Example Solution: Full Frame Buffer

In `main.c`, add:
```c
uint16_t frame_buffer[SCREEN_WIDTH * SCREEN_HEIGHT];
void buffer_draw_pixel(int x, int y, uint16_t color) {
    if (x >= 0 && x < SCREEN_WIDTH && y >= 0 && y < SCREEN_HEIGHT) {
        frame_buffer[y * SCREEN_WIDTH + x] = color;
    }
}
```
Update `draw_ship()`, `draw_bullets()`, `draw_asteroids()`, and `draw_ui()`
to use `buffer_draw_pixel`. In `game_loop()`:
- Clear buffer: `memset(frame_buffer, 0, sizeof(frame_buffer));`.
- Draw all objects to buffer.
- Blit with `display_blit_full(frame_buffer);`.
- Remove incremental clears (`clear_object_rect`).

*Trade-offs*: No flicker, but FPS may drop to ~30 due to full blits. Overclocking
can help but risks heat. A partial buffer might be better for balance.


#### Tips for Success
- Test on hardware—emulators won’t show real flicker or SPI timing.
- Start simple (e.g., optimise rectangles) before trying complex buffering.
- If memory runs out, try a 1-bit-per-pixel buffer (saves ~75% RAM but needs conversion logic).
- Document failures—they’re as valuable as successes for learning.
- Have fun! This project blends retro gaming with modern embedded programming.


