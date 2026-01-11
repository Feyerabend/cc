# DIFFIE-HELLMAN INITIATOR
# Demonstrates key exchange then symmetric encryption
# Wiring: UART TX (GP0) -> Pico2 RX, UART RX (GP1) -> Pico2 TX, GND -> GND

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

# Diffie-Hellman public parameters (known to both parties)
# Using safe prime and generator
DH_PRIME = 23  # p (small for demo - in production use 2048+ bit prime)
DH_GENERATOR = 5  # g (primitive root modulo p)

# Shared state
dh_shared_secret = None
encrypt_queue = []
result_queue = []
core1_ready = False
lock = _thread.allocate_lock()

# Simple XOR-based encryption for demonstration
# Not secure, just for illustration
def encrypt_with_key(data, key):
    result = bytearray()
    key_bytes = key.to_bytes(8, 'big')
    for i, byte in enumerate(data):
        result.append(byte ^ key_bytes[i % len(key_bytes)])
    return bytes(result)

# Core 1 task: handles DH computations and encryption
def core1_task():
    global core1_ready
    print("[Core 1] Crypto engine started")
    core1_ready = True
    
    while True:
        if encrypt_queue:
            with lock:
                task = encrypt_queue.pop(0)
            
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
                
            elif task_type == 'encrypt':
                # Encrypt data with shared secret
                data, key = task['data'], task['key']
                start = time.ticks_ms()
                encrypted = encrypt_with_key(data, key)
                duration = time.ticks_diff(time.ticks_ms(), start)
                
                with lock:
                    result_queue.append({'type': 'encrypted', 'value': encrypted, 'time': duration})
                print(f"[Core 1] Encrypted {len(data)} bytes in {duration}ms")
        
        time.sleep_ms(5)

# Helper to wait for a specific result type
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

# 
def main():
    global core1_ready, dh_shared_secret
    
    print("=" * 50)
    print("PICO 2 - DIFFIE-HELLMAN INITIATOR")
    print("=" * 50)
    print("DH Parameters:")
    print(f"  Prime (p) = {DH_PRIME}")
    print(f"  Generator (g) = {DH_GENERATOR}")
    print("\nWiring:")
    print("  GP0 (TX) -> Pico2 RX, GP1 (RX) -> Pico2 TX")
    print("  GND -> GND")
    print("=" * 50)
    
    # Start Core 1
    _thread.start_new_thread(core1_task, ())
    while not core1_ready:
        time.sleep_ms(100)
    
    # Setup UART (both TX and RX)
    #uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
    uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
    
    #define UART_ID uart1
    #define BAUD_RATE 9600
    #define UART_TX_PIN 4
    #define UART_RX_PIN 5

    print("\n[Core 0] Ready. Starting DH key exchange...")
    print("-" * 50)
    
    # Step 1: Generate private key
    private_key = urandom.randint(2, DH_PRIME - 2)
    print(f"[STEP 1] Generated private key: {private_key} (secret!)")
    
    # Step 2: Compute public key using Core 1
    print(f"[STEP 2] Computing public key: {DH_GENERATOR}^{private_key} mod {DH_PRIME}")
    with lock:
        encrypt_queue.append({
            'type': 'dh_compute',
            'g': DH_GENERATOR,
            'private': private_key,
            'p': DH_PRIME
        })
    
    result = wait_for_result('dh_public')
    public_key = result['value']
    print(f"[STEP 2] Our public key: {public_key}")
    
    # Step 3: Send public key to other Pico
    print(f"[STEP 3] Sending public key to Pico 2...")
    uart.write(public_key.to_bytes(2, 'big'))
    
    # Step 4: Receive other Pico's public key
    print(f"[STEP 4] Waiting for Pico 2's public key...")
    other_public_key = None
    buffer = bytearray()
    
    timeout = time.ticks_ms()
    while other_public_key is None:
        if uart.any():
            buffer.extend(uart.read())
            if len(buffer) >= 2:
                other_public_key = int.from_bytes(buffer[:2], 'big')
                buffer = buffer[2:]
                print(f"[STEP 4] Received public key: {other_public_key}")
                break
        
        if time.ticks_diff(time.ticks_ms(), timeout) > 10000:
            print("[ERROR] Timeout waiting for other public key")
            return
        
        time.sleep_ms(10)
    
    # Step 5: Compute shared secret using Core 1
    print(f"[STEP 5] Computing shared secret: {other_public_key}^{private_key} mod {DH_PRIME}")
    with lock:
        encrypt_queue.append({
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
    print("\nNow you can send encrypted messages...")
    print("-" * 50)
    
    # Main encryption loop
    while True:
        try:
            data = input("\nEnter text to encrypt: ")
            if not data:
                continue
            
            data_bytes = data.encode('utf-8')
            print(f"\n[INPUT] '{data}' ({len(data_bytes)} bytes)")
            
            # Encrypt using shared secret
            print(f"[ENCRYPT] Using shared secret: {dh_shared_secret}")
            with lock:
                encrypt_queue.append({
                    'type': 'encrypt',
                    'data': data_bytes,
                    'key': dh_shared_secret
                })
            
            result = wait_for_result('encrypted')
            encrypted = result['value']
            
            print(f"[ENCRYPTED] {encrypted.hex()}")
            
            # Send: length + encrypted data
            transmission = len(encrypted).to_bytes(2, 'big') + encrypted
            uart.write(transmission)
            
            print(f"[UART TX] Sent {len(transmission)} bytes")
            print("-" * 50)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            import sys
            sys.print_exception(e)

if __name__ == "__main__":
    main()
