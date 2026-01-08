import random
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from pimoroni import Button

# Init display (320x240 resolution)
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()

# Init buttons
button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Colour palettes
BLACK = display.create_pen(0, 0, 0)

# Green palette
DARK_GREEN = display.create_pen(0, 180, 0)
MID_GREEN = display.create_pen(100, 220, 100)
LIGHT_GREEN = display.create_pen(150, 240, 150)
YELLOW_GREEN = display.create_pen(180, 240, 100)

# Grayscale palette
DARK_GRAY = display.create_pen(60, 60, 60)
MID_GRAY = display.create_pen(120, 120, 120)
LIGHT_GRAY = display.create_pen(180, 180, 180)
VERY_LIGHT_GRAY = display.create_pen(220, 220, 220)

# Colour mode flag
color_mode = True  # True = color, False = grayscale

def plot_point(x, y, pen):
    # Map x from [-3, 3] to screen width
    px = int((x + 3) * (WIDTH / 6))
    # Map y from [0, 10] to screen height (inverted for display)
    py = int(y * (HEIGHT / 10))
    py = HEIGHT - py - 1  # Flip y-axis
    
    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
        display.pixel(px, py)

def generate_fern_layer(iterations, pen):
    x, y = 0.0, 0.0
    display.set_pen(pen)
    
    for _ in range(iterations):
        r = random.random()
        
        # Barnsley fern transformation functions
        if r < 0.01:
            # Stem
            x_new = 0
            y_new = 0.16 * y
        elif r < 0.86:
            # Successively smaller leaflets
            x_new = 0.85 * x + 0.04 * y
            y_new = -0.04 * x + 0.85 * y + 1.6
        elif r < 0.93:
            # Largest left-hand leaflet
            x_new = 0.2 * x - 0.26 * y
            y_new = 0.23 * x + 0.22 * y + 1.6
        else:
            # Largest right-hand leaflet
            x_new = -0.15 * x + 0.28 * y
            y_new = 0.26 * x + 0.24 * y + 0.44
        
        x, y = x_new, y_new
        plot_point(x, y, pen)

def draw_fern():
    # Clear screen
    display.set_pen(BLACK)
    display.clear()
    
    # Choose color palette based on mode
    if color_mode:
        colors = [DARK_GREEN, MID_GREEN, LIGHT_GREEN, YELLOW_GREEN]
    else:
        colors = [DARK_GRAY, MID_GRAY, LIGHT_GRAY, VERY_LIGHT_GRAY]
    
    # Draw layers from darkest to lightest
    print("Drawing base layer..")
    generate_fern_layer(25000, colors[0])
    
    print("Drawing second layer..")
    generate_fern_layer(15000, colors[1])
    
    print("Drawing third layer..")
    generate_fern_layer(10000, colors[2])
    
    print("Drawing highlights..")
    generate_fern_layer(7500, colors[3])
    
    # Update display
    display.update()
    print("Fern complete!")

# Main program
print("Barnsley Fern Generator")
print("Press A to generate fern")
print("Press B to clear screen")
print("Press X to toggle color/grayscale")

draw_fern()  # Draw initial fern

# Main loop
while True:
    if button_a.read():
        print("Regenerating fern..")
        draw_fern()
        while button_a.read():  # Wait for release
            pass
    
    if button_b.read():
        print("Clearing screen..")
        display.set_pen(BLACK)
        display.clear()
        display.update()
        while button_b.read():  # Wait for release
            pass
    
    if button_x.read():
        color_mode = not color_mode
        mode_text = "color" if color_mode else "grayscale"
        print(f"Switching to {mode_text} mode..")
        draw_fern()
        while button_x.read():  # Wait for release
            pass
