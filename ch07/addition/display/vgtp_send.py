#!/usr/bin/env python3
"""
vgtp_send.py — VGTP DATA channel sender for Pico 2W

Usage:
    python3 vgtp_send.py <pico-ip> demo                      # looping demo scene
    python3 vgtp_send.py <pico-ip> rect  X Y W H COLOR       # single rect (COLOR=0xRRGGBB)
    python3 vgtp_send.py <pico-ip> line   X0 Y0 X1 Y1 COLOR  # single line
    python3 vgtp_send.py <pico-ip> circle CX CY R COLOR      # single circle
    python3 vgtp_send.py <pico-ip> text   X Y "message"      # single text (white on black)
    python3 vgtp_send.py <pico-ip> clear COLOR               # clear screen
    python3 vgtp_send.py <pico-ip> image  FILE.vti           # send pre-built image packets
    python3 vgtp_send.py <pico-ip> flush                     # send FRAME_END only

Port: 1234
"""

import socket
import struct
import sys
import time
import math
import threading
import atexit

PICO_PORT = 1234
CTRL_PORT = 1235   # CONTROL channel — Pico sends ACKs here

# Packet types
TYPE_DRAW      = 0x01
TYPE_CLEAR     = 0x02
TYPE_FRAME_END = 0x03
TYPE_HEARTBEAT = 0x04

# Primitive types
PRIM_RECT   = 0x01
PRIM_TEXT   = 0x02
PRIM_LINE   = 0x03
PRIM_BITMAP = 0x04
PRIM_CIRCLE = 0x05

VERSION = 0x01


# -- CRC16-CCITT

def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


# -- Packet builder

_seq     = 0
_frame   = 0

def _next_seq() -> int:
    global _seq
    v = _seq & 0xFFFF
    _seq += 1
    return v


def _make_packet(pkt_type: int, payload: bytes, frame_id: int) -> bytes:
    ts = int(time.monotonic() * 1000) & 0xFFFFFFFF
    # header with crc=0
    hdr = struct.pack('<BBHHHI H',
                      VERSION, pkt_type,
                      _next_seq(), frame_id,
                      len(payload),
                      ts,
                      0)          # crc placeholder
    packet = hdr + payload
    # patch in real CRC
    crc = crc16(packet)
    packet = packet[:12] + struct.pack('<H', crc) + packet[14:]
    return packet


# -- RGB888 → RGB565

def rgb888_to_565(rgb: int) -> int:
    r = (rgb >> 16) & 0xFF
    g = (rgb >>  8) & 0xFF
    b =  rgb        & 0xFF
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


# -- High-level helpers

def pkt_clear(frame_id: int, color_rgb888: int = 0x000000) -> bytes:
    color565 = rgb888_to_565(color_rgb888)
    payload = struct.pack('<H', color565)
    return _make_packet(TYPE_CLEAR, payload, frame_id)


def pkt_rect(frame_id: int, x: int, y: int, w: int, h: int, color_rgb888: int) -> bytes:
    color565 = rgb888_to_565(color_rgb888)
    payload = struct.pack('<BhhHHH', PRIM_RECT, x, y, w, h, color565)
    return _make_packet(TYPE_DRAW, payload, frame_id)


def pkt_text(frame_id: int, x: int, y: int, text: str,
             fg_rgb888: int = 0xFFFFFF, bg_rgb888: int = 0x000000) -> bytes:
    fg565 = rgb888_to_565(fg_rgb888)
    bg565 = rgb888_to_565(bg_rgb888)
    encoded = text.encode('utf-8')[:47]
    payload = struct.pack('<BhhHHB', PRIM_TEXT, x, y, fg565, bg565, len(encoded))
    payload += encoded
    return _make_packet(TYPE_DRAW, payload, frame_id)


def pkt_line(frame_id: int, x0: int, y0: int, x1: int, y1: int,
             color_rgb888: int) -> bytes:
    color565 = rgb888_to_565(color_rgb888)
    payload = struct.pack('<BhhhhH', PRIM_LINE, x0, y0, x1, y1, color565)
    return _make_packet(TYPE_DRAW, payload, frame_id)


def pkt_bitmap(frame_id: int, x: int, y: int,
               w: int, h: int, pixels_rgb888: list,
               dw: int = 0, dh: int = 0) -> bytes:
    """pixels_rgb888: list of w*h RGB888 ints, row-major. Max w*h = 115.
    dw, dh: destination display size for scaling (0 = use src dimensions)."""
    npix = w * h
    assert npix <= 115, f"bitmap too large: {npix} > 115"
    if dw == 0: dw = w
    if dh == 0: dh = h
    payload = struct.pack('<BhhBBHH', PRIM_BITMAP, x, y, w, h, dw, dh)
    for px in pixels_rgb888[:npix]:
        payload += struct.pack('<H', rgb888_to_565(px))
    return _make_packet(TYPE_DRAW, payload, frame_id)


def pkt_circle(frame_id: int, cx: int, cy: int, r: int,
               color_rgb888: int) -> bytes:
    color565 = rgb888_to_565(color_rgb888)
    payload = struct.pack('<BhhHH', PRIM_CIRCLE, cx, cy, r, color565)
    return _make_packet(TYPE_DRAW, payload, frame_id)


def pkt_frame_end(frame_id: int) -> bytes:
    return _make_packet(TYPE_FRAME_END, b'', frame_id)


# -- CONTROL ACK listener

CTRL_HDR   = struct.Struct('<BBHIHb')   # version, type, ack_seq, ack_bitmap, adv_window, error_code
HELLO_PLD  = struct.Struct('<HHBH')     # mtu, window, mode, retx_timeout_ms

CTRL_TYPE_NAMES = {
    0x01: "ACK", 0x02: "FLOW", 0x03: "ERROR",
    0x04: "HEARTBEAT", 0x05: "HELLO", 0x06: "HELLO_ACK",
}

# Flow-control state (written by ctrl listener thread, read by sender thread)
_ack_count      = 0
_adv_window     = 8          # updated from HELLO_ACK and ACKs
_unacked_frames = 0
_unacked_lock   = threading.Lock()
_session_ready  = threading.Event()

# -- Reliable mode (Mode 1) retransmit buffer
# seq (int) → (packet_bytes, float timestamp_sent)
_retx_buf     = {}
_retx_lock    = threading.Lock()
RETX_TIMEOUT  = 0.100   # seconds before a packet is retransmitted
RETX_WINDOW   = 32      # max unacked packets before send() blocks


def _seq_le(a: int, b: int) -> bool:
    """True if seq a <= b (16-bit wraparound safe)."""
    return ((b - a) & 0xFFFF) < 0x8000 or a == b


def _retransmit_loop(sock, ip: str, port: int):
    """Background thread: resend packets that haven't been ACK'd in time."""
    while True:
        time.sleep(0.050)   # check every 50 ms
        now = time.monotonic()
        with _retx_lock:
            retx = [(s, p) for s, (p, t) in _retx_buf.items()
                    if now - t > RETX_TIMEOUT]
        for seq, pkt in retx:
            sock.sendto(pkt, (ip, port))
            with _retx_lock:
                if seq in _retx_buf:
                    _retx_buf[seq] = (pkt, time.monotonic())


_ctrl_sock = None   # module-level so atexit can close it


def _close_ctrl_sock():
    global _ctrl_sock
    if _ctrl_sock is not None:
        try:
            _ctrl_sock.close()
        except Exception:
            pass
        _ctrl_sock = None


atexit.register(_close_ctrl_sock)


def _ctrl_listener():
    """Background thread: receive CONTROL packets from Pico on CTRL_PORT."""
    global _ack_count, _adv_window, _unacked_frames, _ctrl_sock

    sock = None
    while sock is None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, OSError):
                pass   # not available on all platforms
            sock.bind(("", CTRL_PORT))
            sock.settimeout(1.0)
            _ctrl_sock = sock   # expose for atexit cleanup
        except OSError as e:
            print(f"  ! ctrl listener bind failed ({e})")
            print(f"    → kill any leftover process:  kill $(lsof -t -i:{CTRL_PORT})")
            try: sock.close()
            except Exception: pass
            sock = None
            time.sleep(1.0)

    while True:
        try:
            data, addr = sock.recvfrom(64)
            if len(data) < CTRL_HDR.size:
                continue
            _, pkt_type, ack_seq, ack_bitmap, adv_window, _ = CTRL_HDR.unpack(data[:CTRL_HDR.size])

            if pkt_type == 0x01:   # ACK
                _ack_count += 1
                # Print on first ACK after connect, then once per ~second
                if _ack_count == 1 or _ack_count % 30 == 0:
                    print(f"  ← ACK  seq={ack_seq}  rx={_ack_count}  sent={_frame}")
                # Clear retransmit buffer for acked packets
                with _retx_lock:
                    acked = [s for s in list(_retx_buf) if _seq_le(s, ack_seq)]
                    for s in acked:
                        del _retx_buf[s]
                    for i in range(32):
                        if ack_bitmap & (1 << i):
                            _retx_buf.pop((ack_seq + i + 1) & 0xFFFF, None)

            elif pkt_type == 0x06:   # HELLO_ACK
                if len(data) >= CTRL_HDR.size + HELLO_PLD.size:
                    mtu, window, mode, retx_ms = HELLO_PLD.unpack(
                        data[CTRL_HDR.size:CTRL_HDR.size + HELLO_PLD.size])
                    with _unacked_lock:
                        _adv_window = window
                    print(f"  ← HELLO_ACK  mtu={mtu}  win={window}  mode={mode}  retx={retx_ms}ms")
                _session_ready.set()

            else:
                name = CTRL_TYPE_NAMES.get(pkt_type, f"0x{pkt_type:02X}")
                print(f"  ← CTRL {name}  from {addr[0]}")

        except socket.timeout:
            pass


def _heartbeat_sender(ip: str, port: int):
    """Background thread: send CTRL HEARTBEAT every 500 ms."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        hdr = CTRL_HDR.pack(VERSION, 0x04, 0, 0, 0, 0)   # HEARTBEAT
        sock.sendto(hdr, (ip, port))
        time.sleep(0.5)


def start_ctrl_listener():
    t = threading.Thread(target=_ctrl_listener, daemon=True)
    t.start()


# -- Frame sender

class VGTPSender:
    def __init__(self, ip: str, reliable: bool = False):
        self.ip       = ip
        self.reliable = reliable
        self.sock     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def connect(self, timeout: float = 5.0) -> bool:
        """Send HELLO on the CONTROL channel and wait for HELLO_ACK."""
        _session_ready.clear()
        hdr = CTRL_HDR.pack(VERSION, 0x05, 0, 0, 0, 0)   # HELLO
        pld = HELLO_PLD.pack(242, 8, 0, 0)                 # mtu=242, win=8, mode=0, retx=0
        self.sock.sendto(hdr + pld, (self.ip, CTRL_PORT))
        print(f"  → HELLO sent to {self.ip}:{CTRL_PORT}")
        if _session_ready.wait(timeout):
            ok = True
        else:
            print("  ! HELLO_ACK timeout — proceeding anyway")
            ok = False
        # Start heartbeat so the Pico knows we're alive
        t = threading.Thread(target=_heartbeat_sender,
                             args=(self.ip, CTRL_PORT), daemon=True)
        t.start()
        # Start retransmit thread if reliable mode requested
        if self.reliable:
            t2 = threading.Thread(target=_retransmit_loop,
                                  args=(self.sock, self.ip, PICO_PORT), daemon=True)
            t2.start()
            print("  ✓ Reliable mode: retransmit enabled")
        return ok

    def _wait_window(self):
        """Block until there is room in the receiver's window."""
        global _unacked_frames
        while True:
            with _unacked_lock:
                if _unacked_frames < _adv_window:
                    _unacked_frames += 1
                    return
            time.sleep(0.001)

    def send(self, pkt: bytes):
        if self.reliable:
            # Window: block until there's space in the retransmit buffer
            while True:
                with _retx_lock:
                    if len(_retx_buf) < RETX_WINDOW:
                        break
                time.sleep(0.001)
            # Store in retransmit buffer keyed by seq (bytes 2-3)
            seq = struct.unpack_from('<H', pkt, 2)[0]
            with _retx_lock:
                _retx_buf[seq] = (pkt, time.monotonic())
        self.sock.sendto(pkt, (self.ip, PICO_PORT))

    def frame(self, *packets):
        """Send a list of packets then FRAME_END, all sharing one frame_id."""
        global _frame
        fid = _frame & 0xFFFF
        _frame += 1
        for pkt in packets:
            # patch the frame_id into already-built packets at offset 4
            # (easier: rebuild them with correct fid)
            self.send(pkt)
        self.send(pkt_frame_end(fid))

    def send_frame(self, pkts_fn):
        """pkts_fn(frame_id) should return a list of packets."""
        global _frame
        fid = _frame & 0xFFFF
        _frame += 1
        for pkt in pkts_fn(fid):
            self.send(pkt)
        self.send(pkt_frame_end(fid))

    def close(self):
        self.sock.close()


# The Demo Scene ..

def _make_rainbow_tile(w: int, h: int, hue_offset: float) -> list:
    """Generate a w*h list of RGB888 colours cycling hue across columns."""
    import colorsys
    pixels = []
    for row in range(h):
        for col in range(w):
            hue = (hue_offset + col / w + row / h * 0.3) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.9, 0.9)
            pixels.append((int(r * 255) << 16) | (int(g * 255) << 8) | int(b * 255))
    return pixels


def run_demo(sender: VGTPSender):
    """Looping animated demo: coloured rects + lines + bitmap tile + text."""
    global _frame
    print(f"Sending demo frames to {sender.ip}:{PICO_PORT}  (Ctrl-C to stop)")
    print(f"  → starting  frame={_frame}  acks_so_far={_ack_count}")
    colors = [0xFF4444, 0x44FF44, 0x4444FF, 0xFFFF44, 0xFF44FF, 0x44FFFF]
    cx, cy = 160, 150   # centre for lines
    count = 0
    t_start = time.monotonic()
    try:
        while True:
            t = time.monotonic()
            fid = _frame & 0xFFFF

            pkts = []
            pkts.append(pkt_clear(fid, 0x111111))

            # Animated bars
            for i, col in enumerate(colors):
                w = int(40 + 35 * math.sin(t * 1.5 + i * 1.1))
                pkts.append(pkt_rect(fid, 16, 30 + i * 30, w, 20, col))

            # Animated radiating lines from centre
            for i in range(6):
                angle = t * 0.8 + i * math.pi / 3
                x1 = int(cx + 70 * math.cos(angle))
                y1 = int(cy + 50 * math.sin(angle))
                pkts.append(pkt_line(fid, cx, cy, x1, y1, colors[i]))

            # Pulsing circles
            for i in range(3):
                r = int(20 + 15 * math.sin(t * 1.2 + i * 2.1))
                pkts.append(pkt_circle(fid, cx, cy, r, colors[i * 2]))

            # Animated rainbow bitmap tile (9x9) top-right corner
            tile_pixels = _make_rainbow_tile(9, 9, t * 0.2)
            pkts.append(pkt_bitmap(fid, 288, 18, 9, 9, tile_pixels))

            # Labels
            for i, name in enumerate(["RED", "GRN", "BLU", "YEL", "MAG", "CYN"]):
                pkts.append(pkt_text(fid, 220, 32 + i * 30, name,
                                     fg_rgb888=colors[i], bg_rgb888=0x111111))

            # Counter
            pkts.append(pkt_text(fid, 4, 215,
                                  f"frame {count:06d}  t={t:.1f}s",
                                  fg_rgb888=0x888888, bg_rgb888=0x111111))

            _frame_id_used = fid
            _frame += 1
            for p in pkts:
                sender.send(p)
            sender.send(pkt_frame_end(_frame_id_used))

            count += 1
            if count % 30 == 0:
                fps = 30 / max(time.monotonic() - t_start, 0.001)
                print(f"  → frame {count:6d}  fps={fps:4.1f}  acks={_ack_count}")
            elapsed = time.monotonic() - t
            time.sleep(max(0, 0.033 - elapsed))   # target ~30 fps

    except KeyboardInterrupt:
        fps = count / max(time.monotonic() - t_start, 0.001)
        print(f"\nStopped.  sent={count}  acks={_ack_count}  avg_fps={fps:.1f}")


# -- CLI

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    ip       = sys.argv[1]
    cmd      = sys.argv[2]
    reliable = "--reliable" in sys.argv
    print(f"--- VGTP  target={ip}  cmd={cmd}  reliable={reliable} ---")
    sender   = VGTPSender(ip, reliable=reliable)
    start_ctrl_listener()
    sender.connect()

    fid = _frame & 0xFFFF

    if cmd == "demo":
        run_demo(sender)

    elif cmd == "rect":
        if len(sys.argv) < 8:
            print("rect usage: X Y W H COLOR  (COLOR hex e.g. 0xFF0000)")
            sys.exit(1)
        x, y, w, h = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
        color = int(sys.argv[7], 16)
        sender.send(pkt_rect(fid, x, y, w, h, color))
        sender.send(pkt_frame_end(fid))
        print(f"rect ({x},{y}) {w}x{h} color=#{color:06X}")

    elif cmd == "line":
        if len(sys.argv) < 9:
            print("line usage: X0 Y0 X1 Y1 COLOR  (COLOR hex e.g. 0xFF0000)")
            sys.exit(1)
        x0, y0, x1, y1 = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
        color = int(sys.argv[7], 16)
        sender.send(pkt_line(fid, x0, y0, x1, y1, color))
        sender.send(pkt_frame_end(fid))
        print(f"line ({x0},{y0})→({x1},{y1}) color=#{color:06X}")

    elif cmd == "circle":
        if len(sys.argv) < 7:
            print("circle usage: CX CY R COLOR  (COLOR hex e.g. 0xFF0000)")
            sys.exit(1)
        cx, cy, r = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
        color = int(sys.argv[6], 16)
        sender.send(pkt_circle(fid, cx, cy, r, color))
        sender.send(pkt_frame_end(fid))
        print(f"circle ({cx},{cy}) r={r} color=#{color:06X}")

    elif cmd == "text":
        if len(sys.argv) < 6:
            print("text usage: X Y \"message\"")
            sys.exit(1)
        x, y = int(sys.argv[3]), int(sys.argv[4])
        msg  = sys.argv[5]
        sender.send(pkt_text(fid, x, y, msg))
        sender.send(pkt_frame_end(fid))
        print(f"text ({x},{y}) \"{msg}\"")

    elif cmd == "clear":
        color = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x000000
        sender.send(pkt_clear(fid, color))
        sender.send(pkt_frame_end(fid))
        print(f"clear #{color:06X}")

    elif cmd == "image":
        if len(sys.argv) < 4:
            print("image usage: FILE.vti")
            sys.exit(1)
        vti_path = sys.argv[3]
        _VTI_MAGIC = b'VGTI'
        with open(vti_path, 'rb') as _f:
            if _f.read(4) != _VTI_MAGIC:
                print(f"ERROR: {vti_path} is not a .vti file")
                sys.exit(1)
            _count, = struct.unpack('<I', _f.read(4))
            _pkts = []
            for _ in range(_count):
                _n, = struct.unpack('<H', _f.read(2))
                _pkts.append(_f.read(_n))
        print(f"Loaded {len(_pkts)} packets from {vti_path}")
        # Use frame_id=0 to match pre-built .vti packets
        # 1 ms/packet — PKT_QUEUE_LEN=64 absorbs bursts up to 64 packets cleanly
        _img_fid = 0
        for _i, _p in enumerate(_pkts):
            sender.send(_p)
            time.sleep(0.001)
            if (_i + 1) % 20 == 0:
                print(f"  → {_i+1}/{len(_pkts)}", end='\r')
        sender.send(pkt_frame_end(_img_fid))
        print(f"\n  ✓ {len(_pkts)} packets + FRAME_END")

    elif cmd == "flush":
        sender.send(pkt_frame_end(fid))
        print("FRAME_END sent")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

    sender.close()


if __name__ == "__main__":
    main()
