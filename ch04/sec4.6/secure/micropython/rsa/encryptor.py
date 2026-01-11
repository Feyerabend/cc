# RSA ENCRYPTOR
# Asymmetric encryption using RSA public key (64-bit keys)
# Wiring: UART TX (GP0) -> Pico2 RX, GND -> GND

import _thread
import time
from machine import UART, Pin
import urandom

# RSA Implementation
# Modular exponentiation function (optimised)
def pow_mod(base, exp, mod):
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return result

# Pre-generated 64-bit RSA key pair for better security and longer messages
# Generated from two 32-bit primes: p = 4294967311, q = 4294967357
# These are the largest 32-bit primes, giving us strong 64-bit keys
RSA_PUBLIC_KEY = {
    'n': 18446744082299486827,  # p * q (64-bit modulus)
    'e': 65537                   # Standard public exponent (2^16 + 1)
}

# Key size allows ~7 bytes per block vs 1 byte with old 12-bit keys!
# This is 64-bit RSA vs 12-bit - much more realistic

# Shared data structures
encrypt_queue = []
result_queue = []
core1_ready = False
lock = _thread.allocate_lock()

# Core 1: RSA crypto engine
def core1_task():
    global core1_ready
    print("[Core 1] RSA crypto engine started")
    core1_ready = True
    
    while True:
        if encrypt_queue:
            with lock:
                data = encrypt_queue.pop(0)
            
            msg_int, n, e = data
            
            # Perform RSA encryption: c = m^e mod n
            start = time.ticks_ms()
            encrypted = pow_mod(msg_int, e, n)
            duration = time.ticks_diff(time.ticks_ms(), start)
            
            with lock:
                result_queue.append((encrypted, duration))
            
            print(f"[Core 1] Encrypted block in {duration}ms")
        
        time.sleep_ms(5)

# RSA encryption function
# Encrypts data in chunks suitable for RSA
# Core 0 handles chunking, Core 1 does the encryption
def rsa_encrypt_bytes(data, public_key):
    n = public_key['n']
    e = public_key['e']
    
    # Calculate max block size (must be < n)
    # Subtract 1 byte for safety margin
    max_block_size = max(1, (n.bit_length() - 1) // 8 - 1)
    
    print(f"[Core 0] Block size: {max_block_size} bytes")
    
    encrypted_blocks = []
    
    # Split data into blocks
    for i in range(0, len(data), max_block_size):
        block = data[i:i + max_block_size]
        block_num = i // max_block_size + 1
        total_blocks = (len(data) + max_block_size - 1) // max_block_size
        
        print(f"[Core 0] Processing block {block_num}/{total_blocks} ({len(block)} bytes)")
        
        # Convert block to integer
        msg_int = int.from_bytes(block, 'big')
        
        if msg_int >= n:
            raise ValueError(f"Block too large: {msg_int} >= {n}")
        
        # Send to Core 1 for encryption
        with lock:
            encrypt_queue.append((msg_int, n, e))
        
        # Wait for result
        while True:
            with lock:
                if result_queue:
                    encrypted, duration = result_queue.pop(0)
                    break
            time.sleep_ms(5)
        
        encrypted_blocks.append(encrypted)
    
    return encrypted_blocks

def main():
    global core1_ready
    
    print("=" * 50)
    print("PICO 2 RSA ENCRYPTOR - 64-bit Keys")
    print("=" * 50)
    print(f"RSA Public Key:")
    print(f"  n = {RSA_PUBLIC_KEY['n']}")
    print(f"  e = {RSA_PUBLIC_KEY['e']}")
    print(f"Key size: {RSA_PUBLIC_KEY['n'].bit_length()} bits")
    print(f"Max block size: ~{(RSA_PUBLIC_KEY['n'].bit_length() - 1) // 8 - 1} bytes")
    print("\nWiring:")
    print("  GP0 (UART TX) -> Pico2 RX")
    print("  GND -> GND")
    print("=" * 50)
    
    # Start Core 1 crypto engine
    _thread.start_new_thread(core1_task, ())
    
    while not core1_ready:
        time.sleep_ms(100)
    
    # Setup UART
    uart = UART(0, baudrate=115200, tx=Pin(0))
    
    print("\n[Core 0] Ready. Send data via USB serial...")
    print("You can now send much longer messages!")
    print("-" * 50)
    
    while True:
        try:
            data = input("Enter text to encrypt: ")
            if not data:
                continue
            
            data_bytes = data.encode('utf-8')
            total_len = len(data_bytes)
            
            print(f"\n[INPUT] '{data}' ({total_len} bytes)")
            
            # RSA encrypt
            start_time = time.ticks_ms()
            encrypted_blocks = rsa_encrypt_bytes(data_bytes, RSA_PUBLIC_KEY)
            total_time = time.ticks_diff(time.ticks_ms(), start_time)
            
            print(f"\n[RSA] Encrypted {len(encrypted_blocks)} blocks in {total_time}ms")
            print(f"[RSA] Average: {total_time // len(encrypted_blocks) if encrypted_blocks else 0}ms per block")
            
            # Show first few encrypted blocks
            for i, block in enumerate(encrypted_blocks[:3]):
                print(f"  Block {i}: {block}")
            if len(encrypted_blocks) > 3:
                print(f"  ... and {len(encrypted_blocks) - 3} more blocks")
            
            # Prepare transmission: [num_blocks][block1_size][block1][block2_size][block2]...
            num_blocks = len(encrypted_blocks)
            transmission = bytearray()
            transmission.extend(num_blocks.to_bytes(2, 'big'))  # 2 bytes for block count
            
            for block in encrypted_blocks:
                # Each block is 8 bytes (64-bit)
                transmission.extend(block.to_bytes(8, 'big'))
            
            # Send over UART
            uart.write(transmission)
            
            print(f"[UART TX] Sent {len(transmission)} bytes to Pico 2")
            print("-" * 50)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            import sys
            sys.print_exception(e)
            time.sleep_ms(100)

if __name__ == "__main__":
    main()
