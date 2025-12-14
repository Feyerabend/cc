# ENCRYPTOR
# Wiring: UART as described in the wiring in the book
# USB for input/output monitoring
# Note: This is a simplified example for educational purposes ONLY.

import _thread
import time
from machine import UART, Pin

# Simple XOR encryption function, with key rotation
def encrypt_chunk(data, key, offset=0):
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

# Encryption key (shared secret)
ENCRYPTION_KEY = b"SecretKey123!@#$"

# Core 1 function: handles second half encryption
def core1_task():
    global core1_ready, core1_output
    print("[Core 1] Started")
    core1_ready = True
    
    while True:
        if core1_input:
            with lock:
                data = core1_input.pop(0)
            
            # Encrypt with offset for second half
            encrypted = encrypt_chunk(data, ENCRYPTION_KEY, offset=len(data))
            
            with lock:
                core1_output.append(encrypted)
            
            print(f"[Core 1] Encrypted {len(data)} bytes")
        time.sleep_ms(10)


def main():
    global core1_ready
    
    print("-" * 50)
    print("PICO 2 ENCRYPTOR - Dual Core Demo")
    print("-" * 50)
    print(f"Encryption Key: {ENCRYPTION_KEY.decode()}")
    print("\nWiring:")
    print("  GP0 (UART TX) -> Pico2 RX")
    print("  GND -> GND")
    print("-" * 50)
    
    # Start Core 1
    _thread.start_new_thread(core1_task, ())
    
    # Wait for Core 1 to be ready
    while not core1_ready:
        time.sleep_ms(100)
    
    # Setup UART (TX on GP0, no RX needed)
    uart = UART(1, baudrate=115200, tx=Pin(4))
    
    print("\n[Core 0] Ready. Send data via USB serial..")
    print("Format: Just type your message and press Enter")
    print("-" * 50)
    
    while True:
        # Read from USB serial (stdin)
        try:
            data = input("Enter text to encrypt: ")
            if not data:
                continue
                
            data_bytes = data.encode('utf-8')
            total_len = len(data_bytes)
            
            print(f"\n[INPUT] '{data}' ({total_len} bytes)")
            
            # Split data between cores
            mid = total_len // 2
            chunk0 = data_bytes[:mid]
            chunk1 = data_bytes[mid:]
            
            print(f"[Core 0] Processing {len(chunk0)} bytes")
            print(f"[Core 1] Processing {len(chunk1)} bytes")
            
            # Core 0 encrypts first half
            encrypted0 = encrypt_chunk(chunk0, ENCRYPTION_KEY, offset=0)
            
            # Core 1 encrypts second half
            with lock:
                core1_input.append(chunk1)
            
            # Wait for Core 1 to finish
            while True:
                with lock:
                    if core1_output:
                        encrypted1 = core1_output.pop(0)
                        break
                time.sleep_ms(10)
            
            # Combine encrypted chunks
            full_encrypted = encrypted0 + encrypted1
            
            # Show encryption result
            hex_str = full_encrypted.hex()
            print(f"\n[ENCRYPTED] {hex_str}")
            print(f"[LENGTH] {len(full_encrypted)} bytes")
            
            # Send over UART: length header + encrypted data
            header = len(full_encrypted).to_bytes(2, 'big')
            uart.write(header + full_encrypted)
            
            print(f"[UART TX] Sent to Pico 2")
            print("-" * 50)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep_ms(100)

# Start main program on Core 0
if __name__ == "__main__":
    main()
