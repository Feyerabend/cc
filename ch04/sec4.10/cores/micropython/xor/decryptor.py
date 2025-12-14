# DECRYPTOR
# Wiring: UART described in the book
# USB for output monitoring

import _thread
import time
from machine import UART, Pin

# Same decryption function (XOR is symmetric)
# Decrypts data chunk using XOR cipher with key rotation
def decrypt_chunk(data, key, offset=0):
    result = bytearray()
    key_len = len(key)
    for i, byte in enumerate(data):
        key_byte = key[(i + offset) % key_len]
        result.append(byte ^ key_byte)
    return bytes(result)

# Shared data structures
core0_input = []
core1_input = []
core0_output = []
core1_output = []
core1_ready = False
lock = _thread.allocate_lock()

# Decryption key (must match encryptor)
DECRYPTION_KEY = b"SecretKey123!@#$"

# Core 1 function: handles second half decryption
def core1_task():
    global core1_ready, core1_output
    print("[Core 1] Started")
    core1_ready = True
    
    while True:
        if core1_input:
            with lock:
                data = core1_input.pop(0)
            
            # Decrypt with offset for second half
            decrypted = decrypt_chunk(data, DECRYPTION_KEY, offset=len(data))
            
            with lock:
                core1_output.append(decrypted)
            
            print(f"[Core 1] Decrypted {len(data)} bytes")
        time.sleep_ms(10)


def main():
    global core1_ready
    
    print("-" * 50)
    print("PICO 2 DECRYPTOR - Dual Core Demo")
    print("-" * 50)
    print(f"Decryption Key: {DECRYPTION_KEY.decode()}")
    print("\nWiring:")
    print("  GP1 (UART RX) -> Pico1 TX")
    print("  GND -> GND")
    print("-" * 50)
    
    # Start Core 1
    _thread.start_new_thread(core1_task, ())
    
    # Wait for Core 1 to be ready
    while not core1_ready:
        time.sleep_ms(100)
    
    # Setup UART (RX on GP1, no TX needed)
    uart = UART(1, baudrate=115200, rx=Pin(5))
    
    print("\n[Core 0] Ready. Listening for encrypted data..")
    print("-" * 50)
    
    buffer = bytearray()
    expected_len = None
    
    while True:
        if uart.any():
            # Read available data
            chunk = uart.read()
            buffer.extend(chunk)
            
            # Try to parse message
            while len(buffer) >= 2:
                # Read length header if we don't have one
                if expected_len is None:
                    expected_len = int.from_bytes(buffer[:2], 'big')
                    buffer = buffer[2:]
                    print(f"[UART RX] Expecting {expected_len} bytes")
                
                # Check if we have full message
                if len(buffer) >= expected_len:
                    encrypted_data = bytes(buffer[:expected_len])
                    buffer = buffer[expected_len:]
                    
                    # Show received data
                    hex_str = encrypted_data.hex()
                    print(f"\n[ENCRYPTED] {hex_str}")
                    print(f"[LENGTH] {len(encrypted_data)} bytes")
                    
                    # Split data between cores
                    mid = len(encrypted_data) // 2
                    chunk0 = encrypted_data[:mid]
                    chunk1 = encrypted_data[mid:]
                    
                    print(f"[Core 0] Processing {len(chunk0)} bytes")
                    print(f"[Core 1] Processing {len(chunk1)} bytes")
                    
                    # Core 0 decrypts first half
                    decrypted0 = decrypt_chunk(chunk0, DECRYPTION_KEY, offset=0)
                    
                    # Core 1 decrypts second half
                    with lock:
                        core1_input.append(chunk1)
                    
                    # Wait for Core 1 to finish
                    while True:
                        with lock:
                            if core1_output:
                                decrypted1 = core1_output.pop(0)
                                break
                        time.sleep_ms(10)
                    
                    # Combine decrypted chunks
                    full_decrypted = decrypted0 + decrypted1
                    
                    # Show decryption result
                    try:
                        plaintext = full_decrypted.decode('utf-8')
                        print(f"\n[DECRYPTED] '{plaintext}'")
                        print("[STATUS] Decryption successful!")
                    except:
                        print(f"[DECRYPTED] {full_decrypted.hex()}")
                        print("[STATUS] Not valid UTF-8")
                    
                    print("-" * 50)
                    
                    # Reset for next message
                    expected_len = None
                else:
                    # Wait for more data
                    break
        
        time.sleep_ms(10)

# Start main program on Core 0
if __name__ == "__main__":
    main()
