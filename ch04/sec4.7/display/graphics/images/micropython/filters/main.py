# Raspberry Pi Pico 2W (RP2350)
import machine, framebuf, time, _thread


spi = machine.SPI(0, baudrate=62_000_000,
                  sck=machine.Pin(18), mosi=machine.Pin(19))
cs  = machine.Pin(17, machine.Pin.OUT, value=1)
dc  = machine.Pin(16, machine.Pin.OUT)
rst = machine.Pin(20, machine.Pin.OUT)
bl  = machine.Pin(21, machine.Pin.OUT)
bl.value(1)

btn_a = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
btn_b = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
btn_x = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
btn_y = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

WIDTH, HEIGHT = 240, 360
PROGRESS_BAR_Y = HEIGHT - 1


def write_cmd(cmd, data=None):
    cs.value(0); dc.value(0); spi.write(bytearray([cmd]))
    if data: dc.value(1); spi.write(data)
    cs.value(1)

def set_window(x0=0, y0=0, x1=WIDTH-1, y1=HEIGHT-1):
    write_cmd(0x2A, bytearray([x0>>8, x0&0xFF, x1>>8, x1&0xFF]))
    write_cmd(0x2B, bytearray([y0>>8, y0&0xFF, y1>>8, y1&0xFF]))
    write_cmd(0x2C)

def st7789_init():
    rst.value(0); time.sleep_ms(100); rst.value(1); time.sleep_ms(100)
    write_cmd(0x11); time.sleep_ms(120)
    write_cmd(0x36, b'\x00')
    write_cmd(0x3A, b'\x05')
    write_cmd(0x21)
    write_cmd(0x29); time.sleep_ms(120)

st7789_init()
print("Display init OK")


def rgb565_to_rgb888(col):
    r = ((col >> 11) & 0x1F) << 3
    g = ((col >> 5)  & 0x3F) << 2
    b = (col & 0x1F) << 3
    return r | (r>>5), g | (g>>6), b | (b>>5)

def rgb888_to_rgb565(r,g,b):
    return ((r&0xF8)<<8) | ((g&0xFC)<<3) | (b>>3)


def make_test_pattern():
    fb = framebuf.FrameBuffer(bytearray(WIDTH*HEIGHT*2), WIDTH, HEIGHT, framebuf.RGB565)
    colors = [(255,0,0),(255,127,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(127,0,255),(255,255,255)]
    w = WIDTH // len(colors)
    for i, (r,g,b) in enumerate(colors):
        col = rgb888_to_rgb565(r,g,b)
        x0 = i * w
        x1 = x0 + w if i < len(colors)-1 else WIDTH
        for x in range(x0, x1):
            fb.vline(x, 0, HEIGHT, col)
    grid = rgb888_to_rgb565(255,255,255)
    for x in range(0, WIDTH, 30):  fb.vline(x, 0, HEIGHT, grid)
    for y in range(0, HEIGHT, 30): fb.hline(0, y, WIDTH, grid)
    return fb


KERNELS = {
    0: ('original', [0,0,0, 0,1,0, 0,0,0], 3),
    1: ('blur', [
        1, 4, 6, 4, 1,
        4,16,24,16, 4,
        6,24,36,24, 6,
        4,16,24,16, 4,
        1, 4, 6, 4, 1
    ], 5),
    2: ('edge',     [-1,-1,-1, -1,8,-1, -1,-1,-1], 3),
    3: ('emboss',   [-2,-1,0, -1,1,1, 0,1,2], 3),
}


state = {
    'fb': None,
    'filter_active': False,
    'filter_idx': 0,
    'filter_done': True,
    'progress_y': 0,
    'lock': _thread.allocate_lock()
}


def worker_thread(state):
    while True:
        if state['filter_active'] and not state['filter_done']:
            with state['lock']:
                name, kern, size = KERNELS[state['filter_idx']]
                radius = size // 2
                state['progress_y'] = 0
                y = 0
                row_cache = [None] * size

                while y < HEIGHT:
                    state['progress_y'] = y

                    # Shift cache
                    for i in range(size - 1):
                        row_cache[i] = row_cache[i + 1]

                    # Load new row
                    new_y = y + radius
                    if new_y < HEIGHT:
                        row_cache[size - 1] = [state['fb'].pixel(x, new_y) for x in range(WIDTH)]
                    else:
                        row_cache[size - 1] = row_cache[size - 2]

                    # Initialize first rows
                    if y == 0:
                        for i in range(size):
                            py = min(i, HEIGHT - 1)
                            row_cache[i] = [state['fb'].pixel(x, py) for x in range(WIDTH)]

                    # Process current row
                    for x in range(WIDTH):
                        r_acc = g_acc = b_acc = 0
                        div = 0
                        for ky in range(-radius, radius + 1):
                            for kx in range(-radius, radius + 1):
                                py = y + ky
                                px = max(0, min(x + kx, WIDTH - 1))
                                row_idx = ky + radius
                                row = row_cache[row_idx]
                                if row is None:
                                    row = row_cache[radius]
                                col = row[px]
                                r, g, b = rgb565_to_rgb888(col)
                                k_idx = (ky + radius) * size + (kx + radius)
                                k = kern[k_idx]
                                r_acc += r * k
                                g_acc += g * k
                                b_acc += b * k
                                div += k
                        if div == 0: div = 1
                        r_out = max(0, min(255, r_acc // div))
                        g_out = max(0, min(255, g_acc // div))
                        b_out = max(0, min(255, b_acc // div))
                        state['fb'].pixel(x, y, rgb888_to_rgb565(r_out, g_out, b_out))
                    y += 1

                state['filter_done'] = True
                print(f"Core 1: {name} DONE!")


_thread.start_new_thread(worker_thread, (state,))


def show_fb():
    set_window()
    cs.value(0); dc.value(1); spi.write(state['fb']); cs.value(1)


def draw_progress():
    filled = int((state['progress_y'] / HEIGHT) * WIDTH)
    bg = rgb888_to_rgb565(30, 30, 30)
    fg = rgb888_to_rgb565(0, 255, 255)
    for x in range(WIDTH):
        state['fb'].pixel(x, PROGRESS_BAR_Y, fg if x < filled else bg)


state['fb'] = make_test_pattern()
show_fb()
print("Test pattern shown")
print("A=orig B=blur X=edge Y=emboss")
print("Core 1 + progress bar ready!")

current = -1
prev = [1,1,1,1]
last_progress = -1

while True:
    cur = [btn_a.value(), btn_b.value(), btn_x.value(), btn_y.value()]
    for i in range(4):
        if prev[i] == 1 and cur[i] == 0:
            if i != current:
                current = i
                if i == 0:
                    with state['lock']:
                        state['fb'] = make_test_pattern()
                        show_fb()
                        state['progress_y'] = 0
                        draw_progress()
                        show_fb()
                    print("→ original")
                    state['filter_active'] = False
                    state['filter_done'] = True
                else:
                    state['filter_active'] = True
                    state['filter_done'] = False
                    state['filter_idx'] = i
                    state['progress_y'] = 0
                    print(f"→ {KERNELS[i][0]} (Core 1 working...)")
    prev = cur

    if state['filter_active'] and state['progress_y'] != last_progress:
        draw_progress()
        show_fb()
        last_progress = state['progress_y']

    if state['filter_active'] and state['filter_done']:
        show_fb()
        state['filter_active'] = False
        last_progress = -1

    time.sleep_ms(30)
