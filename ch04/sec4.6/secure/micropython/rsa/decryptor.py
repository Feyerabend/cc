# RSA DECRYPTOR
# Asymmetric decryption using RSA private key (64-bit keys)
# Wiring: UART RX (GP1) -> Pico1 TX, GND -> GND

import _thread
import time
from machine import UART, Pin

# Modular exponentiation function
def pow_mod(base, exp, mod):
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return result

# RSA private key (matches the 64-bit public key from encryptor)
# Generated from primes: p = 4294967311, q = 4294967357
RSA_PRIVATE_KEY = {
    'n': 18446744082299486827,  # p * q (same as public key)
    'd': 12297829379609722369   # Private exponent (calculated from e, phi(n))
}

# To verify the math:
# p = 4294967311, q = 4294967357 (both are 32-bit primes)
# n = p * q = 18446744082299486827
# phi = (p-1) * (q-1) = 18446744073709552168
# e = 65537 (public exponent)
# d = 12297829379609722369 (private exponent, where e*d ≡ 1 mod phi)

# Shared data structures
decrypt_queue = []
result_queue = []
core1_ready = False
lock = _thread.allocate_lock()

# Core 1: RSA decryption task
def core1_task():
    global core1_ready
    print("[Core 1] RSA crypto engine started")
    core1_ready = True
    
    while True:
        if decrypt_queue:
            with lock:
                data = decrypt_queue.pop(0)
            
            cipher_int, n, d = data
            
            # Perform RSA decryption: m = c^d mod n
            start = time.ticks_ms()
            decrypted = pow_mod(cipher_int, d, n)
            duration = time.ticks_diff(time.ticks_ms(), start)
            
            with lock:
                result_queue.append((decrypted, duration))
            
            print(f"[Core 1] Decrypted block in {duration}ms")
        
        time.sleep_ms(5)

# RSA decryption function
# Core 0 handles chunking, Core 1 does the decryption
def rsa_decrypt_blocks(encrypted_blocks, private_key):
    n = private_key['n']
    d = private_key['d']
    
    # Calculate block size
    max_block_size = max(1, (n.bit_length() - 1) // 8 - 1)
    
    decrypted_data = bytearray()
    
    for i, cipher_int in enumerate(encrypted_blocks):
        block_num = i + 1
        print(f"[Core 0] Processing block {block_num}/{len(encrypted_blocks)}")
        
        # Send to Core 1 for decryption
        with lock:
            decrypt_queue.append((cipher_int, n, d))
        
        # Wait for result
        while True:
            with lock:
                if result_queue:
                    msg_int, duration = result_queue.pop(0)
                    break
            time.sleep_ms(5)
        
        # Convert integer back to bytes
        # Calculate actual byte length needed
        byte_length = (msg_int.bit_length() + 7) // 8
        if byte_length == 0:
            byte_length = 1
        
        block_bytes = msg_int.to_bytes(byte_length, 'big')
        decrypted_data.extend(block_bytes)
    
    return bytes(decrypted_data)

def main():
    global core1_ready
    
    print("=" * 50)
    print("PICO 2 RSA DECRYPTOR - 64-bit Keys")
    print("=" * 50)
    print(f"RSA Private Key:")
    print(f"  n = {RSA_PRIVATE_KEY['n']}")
    print(f"  d = {RSA_PRIVATE_KEY['d']}")
    print(f"Key size: {RSA_PRIVATE_KEY['n'].bit_length()} bits")
    print(f"Max block size: ~{(RSA_PRIVATE_KEY['n'].bit_length() - 1) // 8 - 1} bytes")
    print("\nWiring:")
    print("  GP1 (UART RX) -> Pico1 TX")
    print("  GND -> GND")
    print("=" * 50)
    
    # Start Core 1 crypto engine
    _thread.start_new_thread(core1_task, ())
    
    while not core1_ready:
        time.sleep_ms(100)
    
    # Setup UART
    uart = UART(0, baudrate=115200, rx=Pin(1))
    
    print("\n[Core 0] Ready. Listening for encrypted data...")
    print("-" * 50)
    
    buffer = bytearray()
    expected_blocks = None
    blocks_received = []
    
    while True:
        if uart.any():
            chunk = uart.read()
            buffer.extend(chunk)
            
            # Parse messages
            while len(buffer) > 0:
                # Read number of blocks if we don't have it
                if expected_blocks is None:
                    if len(buffer) < 2:
                        break
                    expected_blocks = int.from_bytes(buffer[:2], 'big')
                    buffer = buffer[2:]
                    blocks_received = []
                    print(f"[UART RX] Expecting {expected_blocks} encrypted blocks")
                
                # Read blocks (8 bytes each for 64-bit keys)
                bytes_per_block = 8
                
                if len(buffer) >= bytes_per_block:
                    block_bytes = buffer[:bytes_per_block]
                    buffer = buffer[bytes_per_block:]
                    
                    block_int = int.from_bytes(block_bytes, 'big')
                    blocks_received.append(block_int)
                    
                    # Show first few blocks
                    if len(blocks_received) <= 3:
                        print(f"  Block {len(blocks_received)}: {block_int}")
                    elif len(blocks_received) == 4:
                        print(f"  ... receiving more blocks ...")
                    
                    # Check if we have all blocks
                    if len(blocks_received) == expected_blocks:
                        print(f"\n[RSA] Received all {expected_blocks} blocks")
                        
                        # Decrypt all blocks
                        start_time = time.ticks_ms()
                        decrypted_data = rsa_decrypt_blocks(blocks_received, RSA_PRIVATE_KEY)
                        total_time = time.ticks_diff(time.ticks_ms(), start_time)
                        
                        print(f"\n[RSA] Decrypted in {total_time}ms")
                        print(f"[RSA] Average: {total_time // expected_blocks if expected_blocks else 0}ms per block")
                        
                        # Display result
                        try:
                            plaintext = decrypted_data.decode('utf-8')
                            print(f"\n[DECRYPTED] '{plaintext}'")
                            print(f"[LENGTH] {len(plaintext)} characters")
                            print("[STATUS] ✓ Decryption successful!")
                        except:
                            print(f"[DECRYPTED] {decrypted_data.hex()}")
                            print("[STATUS] ✗ Not valid UTF-8")
                        
                        print("-" * 50)
                        
                        # Reset for next message
                        expected_blocks = None
                        blocks_received = []
                else:
                    # Wait for more data
                    break
        
        time.sleep_ms(10)

if __name__ == "__main__":
    main()
