"""
Illustrative Blockchain over UART with Recovery
-----------------------------------------------
Illustrates:

- Hash-chained blocks
- Authenticated history (HMAC)
- Loss detection
- Explicit resynchronisation
- Deterministic convergence

This is NOT a cryptocurrency.
This IS a correct illustration of a blockchain.
"""

import machine
import utime
import uhashlib
import ubinascii


# Config

DEVICE_ID = "PICO_B"
IS_SENDER = (DEVICE_ID == "PICO_A")

SECRET_KEY = b"shared_secret"
MAX_CHAIN = 32

UART_ID = 1
TX_PIN = 4
RX_PIN = 5
BAUDRATE = 115200


# UART

uart = machine.UART(
    UART_ID,
    baudrate=BAUDRATE,
    tx=machine.Pin(TX_PIN),
    rx=machine.Pin(RX_PIN),
    timeout=100,
)


# Cryptographic primitives

def sha1(data: bytes) -> str:
    return ubinascii.hexlify(
        uhashlib.sha1(data).digest()
    ).decode()

def hmac_sha1(key: bytes, msg: bytes) -> str:
    block = 64
    if len(key) > block:
        key = uhashlib.sha1(key).digest()
    key = key + b"\x00" * (block - len(key))

    o = bytes(b ^ 0x5C for b in key)
    i = bytes(b ^ 0x36 for b in key)

    return sha1(o + uhashlib.sha1(i + msg).digest())


# Block

class Block:
    def __init__(self, index, prev_hash, payload):
        self.index = index
        self.prev_hash = prev_hash
        self.payload = payload
        self.hash = self.compute_hash()
        self.hmac = self.compute_hmac()

    def compute_hash(self):
        data = f"{self.index}|{self.prev_hash}|{self.payload}".encode()
        return sha1(data)

    def compute_hmac(self):
        return hmac_sha1(SECRET_KEY, self.hash.encode())

    def serialize(self):
        return (
            f"BLK|{self.index}|{self.prev_hash}|"
            f"{self.payload}|{self.hash}|{self.hmac}\n"
        )

    @staticmethod
    def parse(parts):
        if len(parts) < 6:
            raise ValueError(f"Invalid block format: expected 6 parts, got {len(parts)}")
        
        index = int(parts[1])
        prev_hash = parts[2]
        payload = parts[3]
        hash_ = parts[4]
        hmac_ = parts[5]

        b = Block(index, prev_hash, payload)
        b.hash = hash_
        b.hmac = hmac_
        return b


# Blockchain

class Blockchain:
    def __init__(self):
        self.chain = [self.genesis()]
        self.cache = {}    # sender-side resend cache
        # Cache genesis for resending
        self.cache[0] = self.chain[0]

    def genesis(self):
        return Block(0, "0" * 40, f"GENESIS-{DEVICE_ID}")

    def tip(self):
        return self.chain[-1]

    def height(self):
        return len(self.chain)

    def add_local(self, payload):
        if self.height() >= MAX_CHAIN:
            return None

        b = Block(self.height(), self.tip().hash, payload)
        self.chain.append(b)
        self.cache[b.index] = b
        return b

    def verify_block(self, b):
        if b.compute_hash() != b.hash:
            print(f"REJECT: hash mismatch")
            return False
        if b.compute_hmac() != b.hmac:
            print(f"REJECT: HMAC mismatch")
            return False
        return True

    def try_add_remote(self, b):
        expected = self.height()

        if b.index < expected:
            print(f"SKIP: already have block {b.index}")
            return True   # already have it

        if b.index > expected:
            print(f"GAP: got {b.index}, expected {expected}")
            self.request_block(expected)
            return False

        if b.prev_hash != self.tip().hash:
            print(f"REJECT: prev_hash mismatch at {b.index}")
            self.request_block(expected)
            return False

        if not self.verify_block(b):
            return False

        self.chain.append(b)
        print(f"ACCEPTED block {b.index}: {b.payload}")
        return True

    def request_block(self, index):
        msg = f"REQ|{index}\n"
        uart.write(msg.encode())
        print(f"REQUEST block {index}")

    def resend_block(self, index):
        b = self.cache.get(index)
        if b:
            uart.write(b.serialize().encode())
            print(f"RESENT block {index}")
        else:
            print(f"RESEND FAILED: block {index} not in cache")


# Application

bc = Blockchain()
counter = 0
send_interval = 0
last_request_time = {}

print("=" * 40)
print(f"Device: {DEVICE_ID}")
print(f"Role: {'SENDER' if IS_SENDER else 'RECEIVER'}")
print(f"Genesis hash: {bc.tip().hash}")
print("=" * 40)

while True:

    # RECEIVE
    if uart.any():
        try:
            line = uart.readline()
            if not line:
                utime.sleep_ms(10)
                continue

            line_str = line.decode().strip()
            if not line_str:
                continue

            parts = line_str.split("|")
            kind = parts[0]

            if kind == "BLK":
                block = Block.parse(parts)
                bc.try_add_remote(block)

            elif kind == "REQ":
                if len(parts) < 2:
                    print("MALFORMED REQ")
                    continue
                idx = int(parts[1])
                bc.resend_block(idx)

            else:
                print(f"UNKNOWN: {kind}")

        except Exception as e:
            print(f"RX error: {e}")
            import sys
            sys.print_exception(e)

    # SEND (sender only)
    if IS_SENDER:
        send_interval += 1
        if send_interval >= 40 and counter < 10:  # ~2 seconds at 50ms sleep
            send_interval = 0
            payload = f"msg-{counter}-from-{DEVICE_ID}"
            block = bc.add_local(payload)
            if block:
                uart.write(block.serialize().encode())
                print(f"SENT block {block.index}: {payload}")
                counter += 1

    utime.sleep_ms(50)