#!/usr/bin/env python3
"""
vgtp_image.py — PNG → VGTP sender / converter / previewer

Two send modes:
  BITMAP mode (default) — uses DRAW/BITMAP packets + FRAME_END.
    Max ~64 tiles per frame (scene buffer limit). Good for small images.

  Canvas mode (--canvas) — uses CANVAS packet type (0x05).
    Writes directly into a persistent 320x240 framebuffer on the Pico.
    No frame limit — any image size works, tiles appear progressively.
    Existing scene animations still render on top of the canvas.

Usage:
    python3 vgtp_image.py input.png --preview [options]
    python3 vgtp_image.py input.png <pico-ip>  [options]
    python3 vgtp_image.py input.png --save out.vti [options]

Options:
    --pos X Y         top-left corner on display  (default: 0 0)
    --size W H        scale PNG to WxH source pixels before tiling
    --display W H     destination display area (default: same as source)
    --tile TW TH      tile dimensions  (BITMAP max=115, CANVAS max=116, default 10x11)
    --center          centre the display area on the screen (overrides --pos)
    --canvas          use CANVAS mode for unlimited image sizes
    --preview         show simulated 320x240 display and exit
    --save FILE       write pre-built packets to a .vti file
    --no-grid         hide tile grid in preview
    --delay MS        inter-packet delay in ms (default: 1 BITMAP, 2 CANVAS)
    --clear COLOR     send CLEAR/CANVAS_CLEAR before image (hex RGB888, e.g. 0x000000)

Canvas size guide (default 10x11 tile):
    64x64 px   →   42 packets  (< 0.1 s)
    160x120    →  176 packets  (0.4 s at 2 ms/pkt)
    320x240    →  672 packets  (1.4 s at 2 ms/pkt)

Speed tip — full-screen stretch in 1 packet (canvas mode):
    python3 vgtp_image.py photo.png <ip> --canvas --size 10 8 --display 320 240
"""

import sys
import struct
import socket
import time
import math
import argparse
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow required:  pip install Pillow")
    sys.exit(1)

# -- Constants

PICO_PORT            = 1234
VERSION              = 0x01
TYPE_DRAW            = 0x01
TYPE_FRAME_END       = 0x03
TYPE_CANVAS          = 0x05   # VGTP_TYPE_CANVAS — persistent canvas tile
TYPE_CANVAS_CLEAR    = 0x06   # VGTP_TYPE_CANVAS_CLEAR — fill canvas with color
PRIM_BITMAP          = 0x04
MAX_TILE_PIXELS      = 115    # BITMAP_MAX_PIXELS on Pico (DRAW mode)
CANVAS_MAX_PIXELS    = 116    # CANVAS_MAX_PIXELS on Pico (canvas mode)

DISPLAY_W = 320
DISPLAY_H = 240

VTI_MAGIC = b'VGTI'    # file magic for .vti packet-list files

# -- VGTP packet builder (standalone, no vgtp_send.py dependency)

_seq = 0

def _crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _make_packet(pkt_type: int, payload: bytes, frame_id: int) -> bytes:
    global _seq
    seq = _seq & 0xFFFF
    _seq += 1
    ts = int(time.monotonic() * 1000) & 0xFFFFFFFF
    hdr = struct.pack('<BBHHHI H', VERSION, pkt_type, seq, frame_id,
                     len(payload), ts, 0)
    pkt = hdr + payload
    crc = _crc16(pkt)
    return pkt[:12] + struct.pack('<H', crc) + pkt[14:]


def _rgb888_to_565(r: int, g: int, b: int) -> int:
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

# -- Image → packet list

def image_to_packets(img: Image.Image,
                     x0: int, y0: int,
                     frame_id: int,
                     tile_w: int, tile_h: int,
                     display_w: int, display_h: int) -> list:
    """
    Tile img into VGTP BITMAP packets.

    x0, y0       : top-left display position
    tile_w/h     : source tile dimensions (product must be ≤ MAX_TILE_PIXELS)
    display_w/h  : total destination display area for the image
                   (each tile gets a proportional slice of it)
    """
    img = img.convert('RGB')
    iw, ih = img.size

    # Per-pixel scale factors from source to display area
    scale_x = display_w / iw
    scale_y = display_h / ih

    packets = []
    for ty in range(0, ih, tile_h):
        for tx in range(0, iw, tile_w):
            tw = min(tile_w, iw - tx)
            th = min(tile_h, ih - ty)

            # Destination rectangle for this tile on the display
            dx = x0 + round(tx * scale_x)
            dy = y0 + round(ty * scale_y)
            dw = round(tw * scale_x)
            dh = round(th * scale_y)
            if dw < 1: dw = 1
            if dh < 1: dh = 1

            # Extract and convert pixels
            pixels = []
            for py in range(th):
                for px in range(tw):
                    r, g, b = img.getpixel((tx + px, ty + py))
                    pixels.append(_rgb888_to_565(r, g, b))

            # Wire: prim_type(1) x(2) y(2) w(1) h(1) dw(2) dh(2) pixels
            payload = struct.pack('<BhhBBHH', PRIM_BITMAP,
                                  dx, dy, tw, th, dw, dh)
            for p in pixels:
                payload += struct.pack('<H', p)

            packets.append(_make_packet(TYPE_DRAW, payload, frame_id))

    return packets

# --Image → canvas packet list

def image_to_canvas_packets(img: Image.Image,
                            x0: int, y0: int,
                            tile_w: int, tile_h: int,
                            display_w: int, display_h: int) -> list:
    """
    Tile img into VGTP CANVAS packets (TYPE_CANVAS = 0x05).

    Canvas tiles bypass the scene buffer and write directly into the Pico's
    persistent canvas_buf.  No FRAME_END is required; tiles appear as they arrive.

    Tile wire format (no prim_type prefix):
        int16 x, int16 y, uint8 w, uint8 h, uint16 dw, uint16 dh, uint16 pixels[w*h]
        = 10-byte header  (vs BITMAP's 11-byte header with prim_type)
    """
    img = img.convert('RGB')
    iw, ih = img.size

    scale_x = display_w / iw
    scale_y = display_h / ih

    packets = []
    for ty in range(0, ih, tile_h):
        for tx in range(0, iw, tile_w):
            tw = min(tile_w, iw - tx)
            th = min(tile_h, ih - ty)

            dx = x0 + round(tx * scale_x)
            dy = y0 + round(ty * scale_y)
            dw = round(tw * scale_x)
            dh = round(th * scale_y)
            if dw < 1: dw = 1
            if dh < 1: dh = 1

            pixels = []
            for py in range(th):
                for px in range(tw):
                    r, g, b = img.getpixel((tx + px, ty + py))
                    pixels.append(_rgb888_to_565(r, g, b))

            # Canvas tile header: x(2) y(2) w(1) h(1) dw(2) dh(2) — no prim_type byte
            payload = struct.pack('<hhBBHH', dx, dy, tw, th, dw, dh)
            for p in pixels:
                payload += struct.pack('<H', p)

            # frame_id is unused for canvas tiles; use 0
            packets.append(_make_packet(TYPE_CANVAS, payload, 0))

    return packets

# -- RGB565 quantisation preview

def quantize_rgb565(img: Image.Image) -> Image.Image:
    """Round-trip through RGB565 to show the colour fidelity on display."""
    img = img.convert('RGB')
    r, g, b = img.split()
    r = r.point(lambda v: (v >> 3) << 3)
    g = g.point(lambda v: (v >> 2) << 2)
    b = b.point(lambda v: (v >> 3) << 3)
    return Image.merge('RGB', (r, g, b))


def make_preview(img: Image.Image,
                 x0: int, y0: int,
                 tile_w: int, tile_h: int,
                 display_w: int, display_h: int,
                 show_grid: bool = True) -> Image.Image:
    """
    Render a simulated 320x240 display with the image pasted at (x0, y0).
    The image is shown at display_w x display_h with RGB565 quantisation.
    Tile grid lines are overlaid if show_grid is True.
    """
    iw, ih = img.size

    # Simulated display canvas — dark background matching demo clear colour
    canvas = Image.new('RGB', (DISPLAY_W, DISPLAY_H), (17, 17, 17))
    draw   = ImageDraw.Draw(canvas)

    # Scale quantised image to destination display area and paste
    display_img = quantize_rgb565(img).resize(
        (display_w, display_h), Image.LANCZOS)
    canvas.paste(display_img, (x0, y0))

    # Tile grid — in source-pixel coordinates, mapped to display coords
    if show_grid:
        scale_x = display_w / iw
        scale_y = display_h / ih
        grid_col = (60, 60, 60)
        for tx in range(0, iw + 1, tile_w):
            gx = x0 + round(tx * scale_x)
            if 0 <= gx < DISPLAY_W:
                draw.line([(gx, y0), (gx, min(y0 + display_h, DISPLAY_H - 1))],
                          fill=grid_col)
        for ty in range(0, ih + 1, tile_h):
            gy = y0 + round(ty * scale_y)
            if 0 <= gy < DISPLAY_H:
                draw.line([(x0, gy), (min(x0 + display_w, DISPLAY_W - 1), gy)],
                          fill=grid_col)

    # Status overlay — mimic the firmware's header bar
    draw.rectangle([(0, 0), (DISPLAY_W - 1, 13)], fill=(0, 0, 15))
    n_tiles = math.ceil(iw / tile_w) * math.ceil(ih / tile_h)
    info = (f"src {iw}x{ih}  tile {tile_w}x{tile_h}  "
            f"dst {display_w}x{display_h}  {n_tiles} pkts  pos ({x0},{y0})")
    draw.text((4, 3), info, fill=(160, 160, 160))

    # Display border
    draw.rectangle([(0, 0), (DISPLAY_W - 1, DISPLAY_H - 1)],
                   outline=(100, 100, 100))

    return canvas

# -- .vti file (list of pre-built VGTP DATA packets)
# Format: magic(4) + count(uint32 LE) + [length(uint16 LE) + bytes] x count

def save_vti(packets: list, path: str):
    with open(path, 'wb') as f:
        f.write(VTI_MAGIC)
        f.write(struct.pack('<I', len(packets)))
        for pkt in packets:
            f.write(struct.pack('<H', len(pkt)))
            f.write(pkt)
    size_kb = sum(len(p) for p in packets) / 1024
    print(f"Saved {len(packets)} packets  ({size_kb:.1f} KB)  → {path}")


def load_vti(path: str) -> list:
    with open(path, 'rb') as f:
        magic = f.read(4)
        if magic != VTI_MAGIC:
            raise ValueError(f"Not a .vti file (magic={magic!r})")
        count, = struct.unpack('<I', f.read(4))
        packets = []
        for _ in range(count):
            n, = struct.unpack('<H', f.read(2))
            packets.append(f.read(n))
    return packets

# -- Send

def send_packets(ip: str, packets: list, frame_id: int = 0,
                 inter_pkt_ms: float = 4, clear_color: int = None):
    """
    Send all image packets then FRAME_END.

    inter_pkt_ms : delay between DATA packets in milliseconds.
                   4 ms gives protocol_task (runs every 2 ms) time to drain the
                   ring buffer between packets, preventing queue overflow.
    clear_color  : if set, sends a CLEAR packet with this RGB888 colour first.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Optional clear before image
    if clear_color is not None:
        r = (clear_color >> 16) & 0xFF
        g = (clear_color >>  8) & 0xFF
        b =  clear_color        & 0xFF
        c565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        clear_pkt = _make_packet(0x02, struct.pack('<H', c565), frame_id)
        sock.sendto(clear_pkt, (ip, PICO_PORT))
        time.sleep(inter_pkt_ms / 1000)

    frame_end = _make_packet(TYPE_FRAME_END, b'', frame_id)
    t0 = time.monotonic()
    n = len(packets)
    for i, pkt in enumerate(packets):
        sock.sendto(pkt, (ip, PICO_PORT))
        if inter_pkt_ms > 0:
            time.sleep(inter_pkt_ms / 1000)
        if (i + 1) % 20 == 0 or i == n - 1:
            pct = (i + 1) / n * 100
            elapsed_ms = (time.monotonic() - t0) * 1000
            print(f"  → {i+1:4d}/{n}  ({pct:.0f}%)  {elapsed_ms:.0f} ms", end='\r')
    sock.sendto(frame_end, (ip, PICO_PORT))
    elapsed = time.monotonic() - t0
    print(f"\n  ✓ {n} packets  FRAME_END  total={elapsed*1000:.0f} ms"
          f"  ({n / elapsed:.0f} pkt/s)")
    sock.close()

# -- Send (canvas mode)

def send_canvas_packets(ip: str, packets: list,
                        inter_pkt_ms: float = 2, clear_color: int = None):
    """
    Send canvas tiles (TYPE_CANVAS).  No FRAME_END — tiles appear as they arrive.

    inter_pkt_ms : delay between tiles.  2 ms gives protocol_task (runs every
                   2 ms) time to write each tile to canvas_buf before the next
                   arrives.  Increase for very large images if tiles are dropped.
    clear_color  : if set, sends a CANVAS_CLEAR packet first (RGB888 int).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if clear_color is not None:
        r = (clear_color >> 16) & 0xFF
        g = (clear_color >>  8) & 0xFF
        b =  clear_color        & 0xFF
        c565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        clear_pkt = _make_packet(TYPE_CANVAS_CLEAR, struct.pack('<H', c565), 0)
        sock.sendto(clear_pkt, (ip, PICO_PORT))
        time.sleep(inter_pkt_ms / 1000)

    t0 = time.monotonic()
    n = len(packets)
    for i, pkt in enumerate(packets):
        sock.sendto(pkt, (ip, PICO_PORT))
        if inter_pkt_ms > 0:
            time.sleep(inter_pkt_ms / 1000)
        if (i + 1) % 20 == 0 or i == n - 1:
            pct = (i + 1) / n * 100
            elapsed_ms = (time.monotonic() - t0) * 1000
            print(f"  → {i+1:4d}/{n}  ({pct:.0f}%)  {elapsed_ms:.0f} ms", end='\r')

    elapsed = time.monotonic() - t0
    print(f"\n  ✓ {n} canvas tiles  total={elapsed*1000:.0f} ms"
          f"  ({n / elapsed:.0f} pkt/s)")
    sock.close()

# -- CLI

def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('image',        help='Input PNG (or other Pillow-readable) file')
    p.add_argument('target', nargs='?', help='Pico IP address to send to (omit for --preview / --save only)')
    p.add_argument('--pos',     nargs=2, type=int,   metavar=('X', 'Y'), default=[0, 0],   help='Top-left on display  (default: 0 0)')
    p.add_argument('--size',    nargs=2, type=int,   metavar=('W', 'H'), help='Scale PNG source to WxH pixels before tiling')
    p.add_argument('--display', nargs=2, type=int,   metavar=('W', 'H'), help='Destination display area in pixels  (default: same as --size)')
    p.add_argument('--tile',    nargs=2, type=int,   metavar=('TW', 'TH'), help=f'Tile size  (BITMAP max={MAX_TILE_PIXELS}, CANVAS max={CANVAS_MAX_PIXELS}, default: 10 11)')
    p.add_argument('--center',  action='store_true', help='Centre the display area on the screen (overrides --pos)')
    p.add_argument('--canvas',  action='store_true', help='Use CANVAS mode: tiles write into persistent canvas_buf on Pico (any image size)')
    p.add_argument('--preview', action='store_true', help='Show simulated 320x240 display preview')
    p.add_argument('--save',    metavar='FILE', help='Save packet list to .vti file for later use with vgtp_send.py')
    p.add_argument('--no-grid', action='store_true', help='Hide tile grid in preview')
    p.add_argument('--delay', type=float, default=None, metavar='MS', help='Inter-packet delay in ms (default: 1 BITMAP, 2 CANVAS)')
    p.add_argument('--clear', type=str, default=None, metavar='COLOR', help='Send CLEAR/CANVAS_CLEAR before image (hex RGB888, e.g. 0x000000)')
    return p.parse_args()


def main():
    args = parse_args()
    canvas_mode = args.canvas

    # --Load & optionally scale source
    img = Image.open(args.image)
    orig_w, orig_h = img.size
    mode_label = "CANVAS" if canvas_mode else "BITMAP"
    print(f"Loaded : {args.image}  ({orig_w}x{orig_h}  {img.mode})  [{mode_label} mode]")

    if args.size:
        img = img.resize(args.size, Image.LANCZOS)
        print(f"Source : scaled to {img.size[0]}x{img.size[1]}")

    iw, ih = img.size

    # -- Tile size
    max_px = CANVAS_MAX_PIXELS if canvas_mode else MAX_TILE_PIXELS
    if args.tile:
        tw, th = args.tile
        if tw * th > max_px:
            print(f"ERROR: tile {tw}x{th}={tw*th} exceeds limit {max_px} in {mode_label} mode")
            sys.exit(1)
    else:
        tw = int(math.sqrt(max_px))   # 10
        th = max_px // tw             # 11
    print(f"Tile   : {tw}x{th} = {tw*th} px/packet  (limit {max_px})")

    # -- Display area
    if args.display:
        disp_w, disp_h = args.display
    else:
        disp_w, disp_h = iw, ih   # 1:1

    # -- Position
    if args.center:
        x0 = (DISPLAY_W - disp_w) // 2
        y0 = (DISPLAY_H - disp_h) // 2
    else:
        x0, y0 = args.pos

    # -- Stats
    n_tiles = math.ceil(iw / tw) * math.ceil(ih / th)
    hdr_bytes = 10 if canvas_mode else 11
    total_bytes = n_tiles * (14 + hdr_bytes + tw * th * 2)
    default_delay = 2.0 if canvas_mode else 1.0
    delay_ms = args.delay if args.delay is not None else default_delay
    print(f"Display: {disp_w}x{disp_h}  at ({x0},{y0})")
    print(f"Packets: {n_tiles}  (~{total_bytes/1024:.1f} KB on wire)  "
          f"delay={delay_ms:.0f} ms/pkt  (~{n_tiles*delay_ms/1000:.1f} s total)")

    # -- Build packets
    if canvas_mode:
        packets = image_to_canvas_packets(img, x0, y0,
                                          tile_w=tw, tile_h=th,
                                          display_w=disp_w, display_h=disp_h)
    else:
        packets = image_to_packets(img, x0, y0, frame_id=0,
                                   tile_w=tw, tile_h=th,
                                   display_w=disp_w, display_h=disp_h)

    # -- Save
    if args.save:
        save_vti(packets, args.save)

    # -- Preview
    if args.preview:
        preview = make_preview(img, x0, y0, tw, th, disp_w, disp_h,
                               show_grid=not args.no_grid)
        prev_path = Path(args.image).with_suffix('.preview.png')
        preview.save(str(prev_path))
        print(f"Preview: saved → {prev_path}")
        preview.show(title=f"VGTP {mode_label} — {n_tiles} packets  "
                           f"src {iw}x{ih}  dst {disp_w}x{disp_h}")

    # -- Send
    if args.target:
        clear_rgb = int(args.clear, 16) if args.clear else None
        print(f"Sending to {args.target}:{PICO_PORT} ...")
        if canvas_mode:
            send_canvas_packets(args.target, packets,
                                inter_pkt_ms=delay_ms, clear_color=clear_rgb)
        else:
            send_packets(args.target, packets,
                         inter_pkt_ms=delay_ms, clear_color=clear_rgb)

    if not args.target and not args.preview and not args.save:
        print("\nNothing to do — specify a target IP, --preview, or --save FILE")
        print(__doc__)


if __name__ == '__main__':
    main()
