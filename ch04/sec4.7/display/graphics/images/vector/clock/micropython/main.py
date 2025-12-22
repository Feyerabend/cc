import time
import math
import ntptime
import network
from machine import Pin, RTC
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from pimoroni import Button

WIFI_SSID = "SSID"
WIFI_PASS = "PASSWORD"
NTP_HOST = "pool.ntp.org"  # Reliable global pool


# Display setup
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2
RADIUS = 100

# Colors (RGB)
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED   = display.create_pen(255, 0, 0)
CYAN  = display.create_pen(0, 255, 255)
GREEN = display.create_pen(0, 255, 0)

# Buttons
button_a = Button(12)  # A = start/stop stopwatch
button_b = Button(13)  # B = reset

# Stopwatch state
stopwatch_running = False
stopwatch_start = 0

# RTC
rtc = RTC()


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    print("Connecting to WiFi ..", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nConnected:", wlan.ifconfig()[0])
    
    print("Syncing NTP ..")
    ntptime.host = NTP_HOST
    ntptime.settime()
    print("NTP synced (UTC)")


def draw_line(x0, y0, x1, y1, pen):
    display.set_pen(pen)
    display.line(int(x0), int(y0), int(x1), int(y1))

def draw_circle(x, y, r, pen):
    display.set_pen(pen)
    display.circle(int(x), int(y), int(r))

def draw_hand(length, angle_deg, pen, thickness=2):
    angle_rad = math.radians(angle_deg - 90)  # -90 to align 12 o'clock
    x = CENTER_X + length * math.cos(angle_rad)
    y = CENTER_Y + length * math.sin(angle_rad)
    draw_line(CENTER_X, CENTER_Y, x, y, pen)
    if thickness > 1:
        # Thicker hand via multiple lines
        for offset in range(-thickness//2, thickness//2 + 1):
            ox = offset * math.sin(angle_rad)
            oy = -offset * math.cos(angle_rad)
            draw_line(CENTER_X + ox, CENTER_Y + oy, x + ox, y + oy, pen)

def draw_clock_face():
    # Hour marks
    for i in range(12):
        angle = i * 30
        inner = RADIUS - 20 if i % 3 == 0 else RADIUS - 10
        x1 = CENTER_X + inner * math.cos(math.radians(angle - 90))
        y1 = CENTER_Y + inner * math.sin(math.radians(angle - 90))
        x2 = CENTER_X + RADIUS * math.cos(math.radians(angle - 90))
        y2 = CENTER_Y + RADIUS * math.sin(math.radians(angle - 90))
        draw_line(x1, y1, x2, y2, WHITE)

    # Center dot
    draw_circle(CENTER_X, CENTER_Y, 4, WHITE)


connect_wifi()
draw_clock_face()

last_second = -1
last_mode = None

while True:
    # Button handling
    if button_a.raw():
        while button_a.raw(): time.sleep(0.01)
        stopwatch_running = not stopwatch_running
        if stopwatch_running:
            stopwatch_start = time.ticks_ms()
        print("Stopwatch:", "RUNNING" if stopwatch_running else "STOPPED")

    if button_b.raw():
        while button_b.raw(): time.sleep(0.01)
        stopwatch_running = False
        print("Stopwatch reset")

    # Get time
    if stopwatch_running:
        elapsed_ms = time.ticks_diff(time.ticks_ms(), stopwatch_start)
        total_seconds = elapsed_ms // 1000
        h = (total_seconds // 3600) % 12
        m = (total_seconds // 60) % 60
        s = total_seconds % 60
        subsec = (elapsed_ms % 1000) / 1000.0
    else:
        tm = time.localtime()
        h, m, s = tm[3] % 12, tm[4], tm[5]
        subsec = 0

    current_mode = "STOPWATCH" if stopwatch_running else "CLOCK (NTP)"

    # Redraw only if needed
    if s != last_second or current_mode != last_mode:
        display.set_pen(BLACK)
        display.clear()
        draw_clock_face()

        # Hour hand (short, thick)
        hour_angle = h * 30 + m * 0.5
        draw_hand(50, hour_angle, CYAN, thickness=5)

        # Minute hand
        minute_angle = m * 6 + s * 0.1
        draw_hand(75, minute_angle, WHITE, thickness=3)

        # Second hand (smooth)
        second_angle = s * 6 + subsec * 6
        draw_hand(90, second_angle, RED, thickness=1)

        # Mode text
        display.set_pen(GREEN)
        display.text(current_mode, 10, 10, scale=2)

        # Digital time
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        if stopwatch_running:
            ms = int(elapsed_ms % 1000)
            time_str += f".{ms:03d}"
        display.set_pen(WHITE)
        display.text(time_str, CENTER_X - 50, HEIGHT - 30, scale=2)

        display.update()
        last_second = s
        last_mode = current_mode

    time.sleep(0.05)  # ~20 FPS
