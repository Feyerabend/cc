import machine
import time
import utime
import random
import _thread
import array

# Display Pack 2.0 specifications
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

# Colours (RGB565 format)
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED = 0xF800
COLOR_GREEN = 0x07E0
COLOR_BLUE = 0x001F
COLOR_YELLOW = 0xFFE0
COLOR_CYAN = 0x07FF
COLOR_MAGENTA = 0xF81F

# Display pins
DISPLAY_CS_PIN = 17
DISPLAY_CLK_PIN = 18
DISPLAY_MOSI_PIN = 19
DISPLAY_DC_PIN = 16
DISPLAY_RESET_PIN = 21
DISPLAY_BL_PIN = 20

# Button pins
BUTTON_A_PIN = 12
BUTTON_B_PIN = 13
BUTTON_X_PIN = 14
BUTTON_Y_PIN = 15

# Particle system parameters
MAX_PARTICLES = 200
GRAVITY = 0.12
BOUNCE_DAMPING = 0.85
BOUNDS_TOP = 25
BOUNDS_BOTTOM = DISPLAY_HEIGHT

# Global state
_spi = None
_cs = None
_dc = None
_reset = None
_bl = None
particles = []
particle_count = MAX_PARTICLES
wind_x = 0.0
wind_y = 0.0
core1_ready = False
core1_done = True
current_fps = 0.0
framebuffer = bytearray(DISPLAY_WIDTH * DISPLAY_HEIGHT * 2)

# Buttons
buttons = {}
prev_buttons = {}

# ST7789 Display Init
def display_init():
    global _spi, _cs, _dc, _reset, _bl
    
    # SPI setup
    _spi = machine.SPI(0, baudrate=31250000, polarity=0, phase=0,
                      sck=machine.Pin(DISPLAY_CLK_PIN), 
                      mosi=machine.Pin(DISPLAY_MOSI_PIN))
    _cs = machine.Pin(DISPLAY_CS_PIN, machine.Pin.OUT, value=1)
    _dc = machine.Pin(DISPLAY_DC_PIN, machine.Pin.OUT, value=1)
    _reset = machine.Pin(DISPLAY_RESET_PIN, machine.Pin.OUT, value=1)
    _bl = machine.Pin(DISPLAY_BL_PIN, machine.Pin.OUT, value=0)

    # Reset sequence
    _reset.value(1)
    time.sleep_ms(10)
    _reset.value(0)
    time.sleep_ms(10)
    _reset.value(1)
    time.sleep_ms(120)

    def cmd(c):
        _dc.value(0)
        _cs.value(0)
        _spi.write(bytes([c]))
        _cs.value(1)

    def data(d):
        _dc.value(1)
        _cs.value(0)
        if isinstance(d, int):
            _spi.write(bytes([d]))
        else:
            _spi.write(bytes(d))
        _cs.value(1)

    # ST7789 init
    cmd(0x01)  # Software reset
    time.sleep_ms(150)
    cmd(0x11)  # Sleep out
    time.sleep_ms(120)
    cmd(0x3A)
    data(0x55)  # RGB565
    cmd(0x36)
    data(0x70)  # Memory access control
    cmd(0x2A)
    data([0x00, 0x00, 0x01, 0x3F])  # Column
    cmd(0x2B)
    data([0x00, 0x00, 0x00, 0xEF])  # Row
    cmd(0xB2)
    data([0x0C, 0x0C, 0x00, 0x33, 0x33])
    cmd(0xB7)
    data(0x35)
    cmd(0xBB)
    data(0x19)
    cmd(0xC0)
    data(0x2C)
    cmd(0xC2)
    data(0x01)
    cmd(0xC3)
    data(0x12)
    cmd(0xC4)
    data(0x20)
    cmd(0xC6)
    data(0x0F)
    cmd(0xD0)
    data([0xA4, 0xA1])
    cmd(0xE0)
    data([0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23])
    cmd(0xE1)
    data([0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23])
    cmd(0x21)  # Inversion
    cmd(0x13)  # Normal display
    time.sleep_ms(10)
    cmd(0x29)  # Display on
    time.sleep_ms(100)

    _bl.value(1)  # Backlight on

# frame to display
def display_blit():
    # Set window
    _dc.value(0)
    _cs.value(0)
    _spi.write(b'\x2A')
    _cs.value(1)
    _dc.value(1)
    _cs.value(0)
    _spi.write(bytes([0, 0, (DISPLAY_WIDTH - 1) >> 8, (DISPLAY_WIDTH - 1) & 0xFF]))
    _cs.value(1)

    _dc.value(0)
    _cs.value(0)
    _spi.write(b'\x2B')
    _cs.value(1)
    _dc.value(1)
    _cs.value(0)
    _spi.write(bytes([0, 0, (DISPLAY_HEIGHT - 1) >> 8, (DISPLAY_HEIGHT - 1) & 0xFF]))
    _cs.value(1)

    _dc.value(0)
    _cs.value(0)
    _spi.write(b'\x2C')
    _cs.value(1)
    
    # Send framebuffer
    _dc.value(1)
    _cs.value(0)
    chunk_size = 4096
    for i in range(0, len(framebuffer), chunk_size):
        _spi.write(framebuffer[i:i + chunk_size])
    _cs.value(1)

def clear_fb(color):
    hi = (color >> 8) & 0xFF
    lo = color & 0xFF
    for i in range(0, len(framebuffer), 2):
        framebuffer[i] = hi
        framebuffer[i + 1] = lo

def fill_rect(x, y, w, h, color):
    hi = (color >> 8) & 0xFF
    lo = color & 0xFF
    for row in range(y, min(y + h, DISPLAY_HEIGHT)):
        offset = (row * DISPLAY_WIDTH + x) * 2
        for col in range(w):
            if x + col < DISPLAY_WIDTH:
                framebuffer[offset] = hi
                framebuffer[offset + 1] = lo
                offset += 2

# igonre for the moment
def draw_text(x, y, text, color):
    # Simplified - just draw colored blocks for now
    offset = 0
    for char in text:
        fill_rect(x + offset, y, 6, 8, color)
        offset += 7

def randf(min_val, max_val):
    return min_val + random.random() * (max_val - min_val)

def init_particles():
    global particles
    particles = []
    colors = [COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, 
              COLOR_CYAN, COLOR_MAGENTA, 0xFD20, 0x07E0]
    
    for _ in range(MAX_PARTICLES):
        # [x, y, vx, vy, color]
        p = array.array('f', [
            randf(10, DISPLAY_WIDTH - 10),
            randf(BOUNDS_TOP + 10, BOUNDS_BOTTOM - 10),
            randf(-2.0, 2.0),
            randf(-2.0, 2.0),
            float(random.choice(colors))
        ])
        particles.append(p)

def update_particles_range(start, end):
    for i in range(start, min(end, len(particles))):
        p = particles[i]
        
        # Apply forces
        p[3] += GRAVITY  # vy += gravity
        p[2] += wind_x * 0.1  # vx += wind
        p[3] += wind_y * 0.1  # vy += wind
        
        # Update position
        p[0] += p[2]  # x += vx
        p[1] += p[3]  # y += vy
        
        # Boundary collisions
        if p[0] <= 2:
            p[0] = 2
            p[2] = -p[2] * BOUNCE_DAMPING
        if p[0] >= DISPLAY_WIDTH - 2:
            p[0] = DISPLAY_WIDTH - 2
            p[2] = -p[2] * BOUNCE_DAMPING
        if p[1] <= BOUNDS_TOP + 2:
            p[1] = BOUNDS_TOP + 2
            p[3] = -p[3] * BOUNCE_DAMPING
        if p[1] >= BOUNDS_BOTTOM - 2:
            p[1] = BOUNDS_BOTTOM - 2
            p[3] = -p[3] * BOUNCE_DAMPING
            p[2] *= 0.95  # Friction on ground

def render_particles():
    # Clear simulation area
    fill_rect(0, BOUNDS_TOP, DISPLAY_WIDTH, DISPLAY_HEIGHT - BOUNDS_TOP, COLOR_BLACK)
    
    # Draw particles as 3x3 blocks
    for i in range(particle_count):
        p = particles[i]
        x = int(p[0])
        y = int(p[1])
        color = int(p[4])
        
        if 1 <= x < DISPLAY_WIDTH - 1 and BOUNDS_TOP <= y < DISPLAY_HEIGHT - 1:
            fill_rect(x - 1, y - 1, 3, 3, color)

def draw_status():
    fill_rect(0, 0, DISPLAY_WIDTH, BOUNDS_TOP - 2, COLOR_BLACK)
    # Simple FPS display (would need proper text rendering)
    fps_color = COLOR_GREEN if current_fps > 30 else COLOR_YELLOW if current_fps > 20 else COLOR_RED
    bar_width = int(current_fps * 2)
    if bar_width > 0:
        fill_rect(5, 5, min(bar_width, 100), 8, fps_color)
    
    # Particle count indicator
    count_width = int((particle_count / MAX_PARTICLES) * 100)
    fill_rect(5, 15, count_width, 6, COLOR_CYAN)

def handle_input():
    global wind_x, wind_y, particle_count, prev_buttons
    
    curr = {k: b.value() for k, b in buttons.items()}
    
    # A: Reset (button press = 0)
    if curr['A'] == 0 and prev_buttons['A'] == 1:
        init_particles()
    
    # B: Cycle particle count
    if curr['B'] == 0 and prev_buttons['B'] == 1:
        particle_count += 100
        if particle_count > MAX_PARTICLES:
            particle_count = 100
    
    # X: Wind right (hold)
    wind_x = 0.5 if curr['X'] == 0 else wind_x * 0.95
    
    # Y: Wind up (hold)
    wind_y = -0.3 if curr['Y'] == 0 else wind_y * 0.95
    
    prev_buttons = curr

# update second half of particles on core1
def core1_thread():
    global core1_ready, core1_done
    while True:
        if core1_ready:
            mid = particle_count // 2
            update_particles_range(mid, particle_count)
            core1_done = True
            core1_ready = False
        time.sleep_ms(1)

def main():
    global core1_ready, core1_done, current_fps, buttons, prev_buttons
    
    print(" - Pico Particle System - ")
    print("Init display..")
    display_init()
    
    # Init buttons
    buttons = {
        'A': machine.Pin(BUTTON_A_PIN, machine.Pin.IN, machine.Pin.PULL_UP),
        'B': machine.Pin(BUTTON_B_PIN, machine.Pin.IN, machine.Pin.PULL_UP),
        'X': machine.Pin(BUTTON_X_PIN, machine.Pin.IN, machine.Pin.PULL_UP),
        'Y': machine.Pin(BUTTON_Y_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    }
    prev_buttons = {k: 1 for k in buttons.keys()}
    
    print("Init particles..")
    init_particles()
    
    print("Starting Core 1..")
    _thread.start_new_thread(core1_thread, ())
    
    clear_fb(COLOR_BLACK)
    display_blit()
    
    frame_count = 0
    last_fps_time = utime.ticks_ms()
    
    print("Running! A=Reset B=Count X=WindR Y=WindUp")
    
    while True:
        frame_start = utime.ticks_ms()
        
        # Input
        handle_input()
        
        # Physics: Core 0 updates first half
        mid = particle_count // 2
        update_particles_range(0, mid)
        
        # Signal Core 1 and wait
        core1_done = False
        core1_ready = True
        while not core1_done:
            pass
        
        # Render (Core 0 only)
        render_particles()
        draw_status()
        
        # Display
        display_blit()
        
        # FPS calculation
        frame_count += 1
        now = utime.ticks_ms()
        elapsed = utime.ticks_diff(now, last_fps_time)
        if elapsed >= 1000:
            current_fps = frame_count * 1000.0 / elapsed
            frame_count = 0
            last_fps_time = now
            print(f"FPS: {current_fps:.1f} | Particles: {particle_count}")
        
        # Frame timing (~60 FPS target)
        #frame_time = utime.ticks_diff(utime.ticks_ms(), frame_start)
        #if frame_time < 16:
        #    time.sleep_ms(16 - frame_time)

# Run
main()

