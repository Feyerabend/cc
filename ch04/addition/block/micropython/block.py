"""
Blockchain-Based Secure IoT Messaging for Raspberry Pi Pico
- HMAC implementation
- Timestamp validation (prevents replay attacks)
- Nonce support (prevents duplicate messages)
- Better error handling
- Configurable as sender or receiver
- Chain validation on receipt
"""

import machine
import utime
import uhashlib
import ubinascii
import urandom

# Configuration
SECRET_KEY = b"change_this_secret_key_256bit!!"  # Must be same on both devices
DEVICE_ID = "PICO_A"  # Change to "PICO_B" on second device
MAX_CHAIN_LENGTH = 50  # Prevent memory overflow
MESSAGE_TIMEOUT = 30  # Seconds - reject messages older than this

# UART Setup (TX=GP0, RX=GP1, GND must be connected)
uart = machine.UART(0, baudrate=115200, tx=machine.Pin(0), rx=machine.Pin(1))
uart.init(bits=8, parity=None, stop=1)

# LED for status indication
led = machine.Pin(25, machine.Pin.OUT)

# check HMAC-SHA1 implementation
def hmac_sha1(key, message):
    block_size = 64
    if len(key) > block_size:
        key = uhashlib.sha1(key).digest()
    if len(key) < block_size:
        key = key + b'\x00' * (block_size - len(key))
    
    o_key_pad = bytes([k ^ 0x5C for k in key])
    i_key_pad = bytes([k ^ 0x36 for k in key])
    
    inner_hash = uhashlib.sha1(i_key_pad + message).digest()
    return uhashlib.sha1(o_key_pad + inner_hash).digest()

def get_timestamp():
    return utime.time()


class Block:
    def __init__(self, index, previous_hash, message, timestamp=None, nonce=None):
        self.index = index
        self.previous_hash = previous_hash
        self.message = message
        self.timestamp = timestamp or get_timestamp()
        self.nonce = nonce or ubinascii.hexlify(urandom.getrandbits(32).to_bytes(4, 'big')).decode()
        self.hash = self.calculate_hash()
        self.signature = self.sign_block()

    # Calculate SHA1 hash of block contents
    def calculate_hash(self):
        data = f"{self.index}|{self.previous_hash}|{self.message}|{self.timestamp}|{self.nonce}".encode()
        return ubinascii.hexlify(uhashlib.sha1(data).digest()).decode()

    # Sign block with HMAC-SHA1
    def sign_block(self):
        signature_data = self.hash.encode()
        return ubinascii.hexlify(hmac_sha1(SECRET_KEY, signature_data)).decode()

    # Verify block signature
    def verify_signature(self):
        expected = ubinascii.hexlify(hmac_sha1(SECRET_KEY, self.hash.encode())).decode()
        return self.signature == expected
    
    # Check if timestamp is within acceptable range
    def is_timestamp_valid(self, current_time):
        time_diff = abs(current_time - self.timestamp)
        return time_diff < MESSAGE_TIMEOUT

    # Serialize block for transmission
    def serialize(self):
        return f"{self.index}|{self.previous_hash}|{self.message}|{self.timestamp}|{self.nonce}|{self.hash}|{self.signature}"


class SecureBlockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_messages = []

    # Create genesis block
    def create_genesis_block(self):
        return Block(0, "0" * 40, f"Genesis-{DEVICE_ID}", timestamp=0, nonce="0000")

    # Get latest block
    def get_latest_block(self):
        return self.chain[-1]

    # Add new block
    def add_block(self, message):
        if len(self.chain) >= MAX_CHAIN_LENGTH:
            print(f"WARNING: Chain length limit reached ({MAX_CHAIN_LENGTH})")
            # In production, implement chain pruning or persistence to flash
            return None
        
        last_block = self.get_latest_block()
        new_block = Block(len(self.chain), last_block.hash, message)
        self.chain.append(new_block)
        return new_block

    # Verify entire chain integrity
    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # Verify hash
            if current.hash != current.calculate_hash():
                print(f"Hash mismatch at block {i}")
                return False
            
            # Verify chain linkage
            if current.previous_hash != previous.hash:
                print(f"Chain broken at block {i}")
                return False
            
            # Verify signature
            if not current.verify_signature():
                print(f"Invalid signature at block {i}")
                return False
        
        return True

    # Verify and add received block
    def verify_and_add_received_block(self, block):
        current_time = get_timestamp()
        
        # Check timestamp
        if not block.is_timestamp_valid(current_time):
            print("Block rejected: Timestamp out of range")
            return False
        
        # Verify signature
        if not block.verify_signature():
            print("Block rejected: Invalid signature (possible tampering)")
            return False
        
        # Check if it links to our chain
        last_block = self.get_latest_block()
        if block.previous_hash != last_block.hash:
            print(f"Block rejected: Chain mismatch (expected {last_block.hash[:8]}..., got {block.previous_hash[:8]}...)")
            return False
        
        # Check index
        if block.index != len(self.chain):
            print(f"Block rejected: Index mismatch (expected {len(self.chain)}, got {block.index})")
            return False
        
        # Add to chain
        self.chain.append(block)
        print(f"✓ Block {block.index} added: '{block.message}' (hash: {block.hash[:8]}...)")
        return True

# Init blockchain
blockchain = SecureBlockchain()
message_counter = 0

def blink_led(times=1, delay=100):
    for _ in range(times):
        led.on()
        utime.sleep_ms(delay)
        led.off()
        utime.sleep_ms(delay)

def send_message(message):
    global message_counter
    new_block = blockchain.add_block(message)
    
    if new_block is None:
        print("Failed to create block")
        return False
    
    data = new_block.serialize() + "\n"
    try:
        uart.write(data.encode())
        print(f"→ Sent block {new_block.index}: '{message}'")
        blink_led(1)
        message_counter += 1
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False

def receive_message():
    if uart.any():
        try:
            data = uart.readline()
            if data:
                line = data.decode().strip()
                parts = line.split("|")
                
                if len(parts) != 7:
                    print(f"Invalid message format (expected 7 parts, got {len(parts)})")
                    return False
                
                index, prev_hash, message, timestamp, nonce, hash_, signature = parts
                
                # Reconstruct block
                received_block = Block(
                    int(index),
                    prev_hash,
                    message,
                    timestamp=int(timestamp),
                    nonce=nonce
                )
                
                # Override with received values for verification
                received_block.hash = hash_
                received_block.signature = signature
                
                # Verify and add
                if blockchain.verify_and_add_received_block(received_block):
                    blink_led(2, 50)
                    return True
                else:
                    blink_led(3, 200)  # Error indication
                    return False
                    
        except Exception as e:
            print(f"Receive error: {e}")
            return False
    return None


def print_chain_info():
    print("\n" + "="*50)
    print(f"Device: {DEVICE_ID}")
    print(f"Chain length: {len(blockchain.chain)}")
    print(f"Chain valid: {blockchain.verify_chain()}")
    print(f"Latest block: {blockchain.get_latest_block().hash[:16]}...")
    print("="*50 + "\n")


# Main loop
print(f"\nSecure IoT Blockchain - Device: {DEVICE_ID}")
print(f"Chain initialised with genesis block")
print(f"Waiting for communication..\n")


# Example: Configure *one* device as primary sender
IS_SENDER = (DEVICE_ID == "PICO_A")

loop_count = 0
while True:
    try:
        # Receive messages (both devices should always listen)
        receive_message()
        
        # Send messages periodically (configure based on device role)
        if IS_SENDER and loop_count % 50 == 0:  # Every ~5 seconds
            msg = f"Data_{message_counter}_from_{DEVICE_ID}"
            send_message(msg)
        
        # Print status periodically
        if loop_count % 200 == 0:  # Every ~20 seconds
            print_chain_info()
        
        loop_count += 1
        utime.sleep_ms(100)  # 100ms loop
        
    except KeyboardInterrupt:
        print("\nShutting down..")
        print_chain_info()
        break
    except Exception as e:
        print(f"Error in main loop: {e}")
        utime.sleep(1)
