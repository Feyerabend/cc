import time
import math
import ntptime
import network
from machine import RTC
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from pimoroni import Button


WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASSWORD"
NTP_HOST = "pool.ntp.org"

# Timezone: offset from UTC in MINUTES
TIMEZONE_OFFSET_MINUTES = 120 # Example: +2 hours (UTC+2)
ENABLE_DST = True # Set False if you don't want DST


display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)
WIDTH, HEIGHT = display.get_bounds()
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
RADIUS = 100


BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
RED   = display.create_pen(255, 0, 0)
CYAN  = display.create_pen(0, 255, 255)
GREEN = display.create_pen(0, 255, 0)
YELLOW = display.create_pen(255, 255, 0)


button_a = Button(12)  # A = toggle stopwatch
button_b = Button(13)  # B = reset


stopwatch_running = False
stopwatch_start = 0


rtc = RTC()

# DST Helper (Europe: last Sun Mar --> last Sun Oct)
def is_dst_europe(year, month, day):
    if month < 3 or month > 10:
        return False
    if month > 3 and month < 10:
        return True
    # March: last Sunday >= 25
    if month == 3:
        last_sunday = 31 - ((time.mktime((year, 3, 31, 0, 0, 0, 0, 0, 0) + 6) % 7)
        return day >= last_sunday
    # October: last Sunday >= 25
    if month == 10:
        last_sunday = 31 - ((time.mktime((year, 10, 31, 0, 0, 0, 0, 0, 0) + 6) % 7)
        return day < last_sunday
    return False

# Get Local Time with Timezone & DST
def get_local_time():
    utc = time.localtime()
    year, month, day = utc[0], utc[1], utc[2]
    
    offset = TIMEZONE_OFFSET_MINUTES
    if ENABLE_DST and is_dst_europe(year, month, day):
        offset += 60  # +1 hour during DST

    # Convert UTC to local
    local_timestamp = time.mktime(utc) + offset * 60
    return time.localtime(local_timestamp)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    print("WiFi..", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nConnected:", wlan.ifconfig()[0])
    
    print("NTP sync..")
    ntptime.host = NTP_HOST
    ntptime.settime()
    print("NTP synced (UTC)")


def draw_line(x0, y0, x1, y1, pen):
    display.set_pen(pen)
    display.line(int(x0), int(y0), int(x1), int(y1))

def draw_hand(length, angle_deg, pen, thickness=1):
    angle_rad = math.radians(angle_deg - 90)
    x = CENTER_X + length * math.cos(angle_rad)
    y = CENTER_Y + length * math.sin(angle_rad)
    if thickness == 1:
        draw_line(CENTER_X, CENTER_Y, x, y, pen)
    else:
        for off in range(-thickness//2, thickness//2 + 1):
            ox = off * math.sin(angle_rad)
            oy = -off * math.cos(angle_rad)
            draw_line(CENTER_X + ox, CENTER_Y + oy, x + ox, y + oy, pen)

def draw_clock_face():
    for i in range(12):
        angle = i * 30
        inner = RADIUS - 20 if i % 3 == 0 else RADIUS - 10
        x1 = CENTER_X + inner * math.cos(math.radians(angle - 90))
        y1 = CENTER_Y + inner * math.sin(math.radians(angle - 90))
        x2 = CENTER_X + RADIUS * math.cos(math.radians(angle - 90))
        y2 = CENTER_Y + RADIUS * math.sin(math.radians(angle - 90))
        draw_line(x1, y1, x2, y2, WHITE)
    display.set_pen(WHITE)
    display.circle(CENTER_X, CENTER_Y, 4)


def get_timezone_str():
    offset = TIMEZONE_OFFSET_MINUTES
    if ENABLE_DST:
        utc = time.localtime()
        if is_dst_europe(utc[0], utc[1], utc[2]):
            offset += 60
    hours = offset // 60
    mins = abs(offset) % 60
    sign = "+" if offset >= 0 else "-"
    return f"UTC{sign}{abs(hours):02d}:{mins:02d}"


connect_wifi()
draw_clock_face()

last_second = -1
last_mode = None
last_tz = None

while True:
    # Button A: toggle stopwatch
    if button_a.raw():
        while button_a.raw(): time.sleep(0.01)
        stopwatch_running = not stopwatch_running
        if stopwatch_running:
            stopwatch_start = time.ticks_ms()

    # Button B: reset
    if button_b.raw():
        while button_b.raw(): time.sleep(0.01)
        stopwatch_running = False

    # Get time
    if stopwatch_running:
        elapsed_ms = time.ticks_diff(time.ticks_ms(), stopwatch_start)
        total_sec = elapsed_ms // 1000
        h = (total_sec // 3600) % 12
        m = (total_sec // 60) % 60
        s = total_sec % 60
        subsec = (elapsed_ms % 1000) / 1000.0
        mode = "STOPWATCH"
    else:
        t = get_local_time()
        h, m, s = t[3] % 12, t[4], t[5]
        subsec = 0
        mode = "CLOCK"

    tz_str = get_timezone_str()

    # Redraw only when needed
    if s != last_second or mode != last_mode or tz_str != last_tz:
        display.set_pen(BLACK)
        display.clear()
        draw_clock_face()

        # Hands
        draw_hand(50, h * 30 + m * 0.5, CYAN, thickness=5)   # Hour
        draw_hand(75, m * 6 + s * 0.1, WHITE, thickness=3)   # Minute
        draw_hand(90, s * 6 + subsec * 6, RED, thickness=1)  # Second

        # Mode + Timezone
        display.set_pen(YELLOW)
        display.text(f"{mode} {tz_str}", 10, 10, scale=1)

        # Digital time
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        if stopwatch_running:
            ms = int(elapsed_ms % 1000)
            time_str += f".{ms:03d}"
        display.set_pen(WHITE)
        display.text(time_str, CENTER_X - 60, HEIGHT - 30, scale=2)

        display.update()

        last_second = s
        last_mode = mode
        last_tz = tz_str

    time.sleep(0.05)

