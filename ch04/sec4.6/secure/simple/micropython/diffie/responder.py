# DIFFIE-HELLMAN RESPONDER
# Demonstrates key exchange then symmetric decryption
# CHANGE! Wiring: UART RX (GP1) -> Pico1 TX, UART TX (GP0) -> Pico1 RX, GND -> GND

import _thread
import time
from machine import UART, Pin
import urandom

# Simple modular exponentiation function
def pow_mod(base, exp, mod):
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return result

# Diffie-Hellman public parameters (same as initiator)
DH_PRIME = 23
DH_GENERATOR = 5

# Shared state
dh_shared_secret = None
decrypt_queue = []
result_queue = []
core1_ready = False
lock = _thread.allocate_lock()

# Simple XOR-based "encryption" for demonstration
# Using XOR as a symmetric cipher for simplicity
def decrypt_with_key(data, key):
    result = bytearray()
    key_bytes = key.to_bytes(8, 'big')
    for i, byte in enumerate(data):
        result.append(byte ^ key_bytes[i % len(key_bytes)])
    return bytes(result)

# Core 1: Crypto engine
def core1_task():
    global core1_ready
    print("[Core 1] Crypto engine started")
    core1_ready = True
    
    while True:
        if decrypt_queue:
            with lock:
                task = decrypt_queue.pop(0)
            
            task_type = task['type']
            
            if task_type == 'dh_compute':
                # Compute g^private mod p
                g, private, p = task['g'], task['private'], task['p']
                start = time.ticks_ms()
                public = pow_mod(g, private, p)
                duration = time.ticks_diff(time.ticks_ms(), start)
                
                with lock:
                    result_queue.append({'type': 'dh_public', 'value': public, 'time': duration})
                print(f"[Core 1] DH public computed in {duration}ms")
                
            elif task_type == 'dh_shared':
                # Compute other_public^private mod p
                other_pub, private, p = task['other_public'], task['private'], task['p']
                start = time.ticks_ms()
                shared = pow_mod(other_pub, private, p)
                duration = time.ticks_diff(time.ticks_ms(), start)
                
                with lock:
                    result_queue.append({'type': 'dh_shared', 'value': shared, 'time': duration})
                print(f"[Core 1] DH shared secret computed in {duration}ms")
                
            elif task_type == 'decrypt':
                # Decrypt data with shared secret
                data, key = task['data'], task['key']
                start = time.ticks_ms()
                decrypted = decrypt_with_key(data, key)
                duration = time.ticks_diff(time.ticks_ms(), start)
                
                with lock:
                    result_queue.append({'type': 'decrypted', 'value': decrypted, 'time': duration})
                print(f"[Core 1] Decrypted {len(data)} bytes in {duration}ms")
        
        time.sleep_ms(5)

# Wait for a specific result type from Core 1
def wait_for_result(expected_type):
    while True:
        with lock:
            if result_queue:
                result = result_queue.pop(0)
                if result['type'] == expected_type:
                    return result
                else:
                    result_queue.append(result)  # Put it back
        time.sleep_ms(5)

def main():
    global core1_ready, dh_shared_secret
    
    print("=" * 50)
    print("PICO 2 - DIFFIE-HELLMAN RESPONDER")
    print("=" * 50)
    print("DH Parameters:")
    print(f"  Prime (p) = {DH_PRIME}")
    print(f"  Generator (g) = {DH_GENERATOR}")
    print("\nWiring:")
    print("  GP1 (RX) -> Pico1 TX, GP0 (TX) -> Pico1 RX")
    print("  GND -> GND")
    print("=" * 50)
    
    # Start Core 1
    _thread.start_new_thread(core1_task, ())
    while not core1_ready:
        time.sleep_ms(100)
    
    # Setup UART (both RX and TX)
    #uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
    uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

    print("\n[Core 0] Ready. Waiting for DH key exchange...")
    print("-" * 50)
    
    # Step 1: Generate private key
    private_key = urandom.randint(2, DH_PRIME - 2)
    print(f"[STEP 1] Generated private key: {private_key} (secret!)")
    
    # Step 2: Compute public key using Core 1
    print(f"[STEP 2] Computing public key: {DH_GENERATOR}^{private_key} mod {DH_PRIME}")
    with lock:
        decrypt_queue.append({
            'type': 'dh_compute',
            'g': DH_GENERATOR,
            'private': private_key,
            'p': DH_PRIME
        })
    
    result = wait_for_result('dh_public')
    public_key = result['value']
    print(f"[STEP 2] Our public key: {public_key}")
    
    # Step 3: Wait for other Pico's public key
    print(f"[STEP 3] Waiting for Pico 1's public key...")
    other_public_key = None
    buffer = bytearray()
    
    timeout = time.ticks_ms()
    while other_public_key is None:
        if uart.any():
            buffer.extend(uart.read())
            if len(buffer) >= 2:
                other_public_key = int.from_bytes(buffer[:2], 'big')
                buffer = buffer[2:]
                print(f"[STEP 3] Received public key: {other_public_key}")
                break
        
        if time.ticks_diff(time.ticks_ms(), timeout) > 10000:
            print("[ERROR] Timeout waiting for other public key")
            return
        
        time.sleep_ms(10)
    
    # Step 4: Send our public key
    print(f"[STEP 4] Sending our public key to Pico 1...")
    uart.write(public_key.to_bytes(2, 'big'))
    
    # Step 5: Compute shared secret using Core 1
    print(f"[STEP 5] Computing shared secret: {other_public_key}^{private_key} mod {DH_PRIME}")
    with lock:
        decrypt_queue.append({
            'type': 'dh_shared',
            'other_public': other_public_key,
            'private': private_key,
            'p': DH_PRIME
        })
    
    result = wait_for_result('dh_shared')
    dh_shared_secret = result['value']
    print(f"[STEP 5] ✓ Shared secret established: {dh_shared_secret}")
    print("\n" + "=" * 50)
    print("KEY EXCHANGE COMPLETE!")
    print("=" * 50)
    print("\nListening for encrypted messages...")
    print("-" * 50)
    
    # Main decryption loop
    expected_len = None
    
    while True:
        if uart.any():
            buffer.extend(uart.read())
            
            while len(buffer) >= 2:
                # Read length header
                if expected_len is None:
                    expected_len = int.from_bytes(buffer[:2], 'big')
                    buffer = buffer[2:]
                    print(f"\n[UART RX] Expecting {expected_len} bytes")
                
                # Check if we have full message
                if len(buffer) >= expected_len:
                    encrypted_data = bytes(buffer[:expected_len])
                    buffer = buffer[expected_len:]
                    
                    print(f"[ENCRYPTED] {encrypted_data.hex()}")
                    
                    # Decrypt using shared secret
                    print(f"[DECRYPT] Using shared secret: {dh_shared_secret}")
                    with lock:
                        decrypt_queue.append({
                            'type': 'decrypt',
                            'data': encrypted_data,
                            'key': dh_shared_secret
                        })
                    
                    result = wait_for_result('decrypted')
                    decrypted = result['value']
                    
                    # Display result
                    try:
                        plaintext = decrypted.decode('utf-8')
                        print(f"[DECRYPTED] '{plaintext}'")
                        print("[STATUS] ✓ Decryption successful!")
                    except:
                        print(f"[DECRYPTED] {decrypted.hex()}")
                        print("[STATUS] ✗ Not valid UTF-8")
                    
                    print("-" * 50)
                    expected_len = None
                else:
                    break
        
        time.sleep_ms(10)

if __name__ == "__main__":
    main()
