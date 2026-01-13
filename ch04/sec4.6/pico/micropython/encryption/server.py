

import ucryptolib
import os  # For random IV generation
import socket
import network

# Shared secret key (16 bytes for AES-128; change this in production!)
KEY = b'secretkey1234567'  # Must be exactly 16, 24, or 32 bytes

def pad(data):
    """PKCS#7 padding to make data multiple of 16 bytes."""
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len] * pad_len)

def unpad(data):
    """Remove PKCS#7 padding."""
    pad_len = data[-1]
    return data[:-pad_len]

def encrypt(message):
    """Encrypt a message with AES-CBC."""
    iv = os.urandom(16)  # Random IV for each encryption
    cipher = ucryptolib.aes(KEY, 2, iv)  # Mode 2 = CBC
    padded = pad(message.encode('utf-8'))
    encrypted = cipher.encrypt(padded)
    return iv + encrypted  # Prefix IV for decryption

def decrypt(encrypted_data):
    """Decrypt a message with AES-CBC."""
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    cipher = ucryptolib.aes(KEY, 2, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    return unpad(decrypted_padded).decode('utf-8')

# ------------------

# WiFi setup as AP
ap = network.WLAN(network.AP_IF)
ap.config(essid='PicoNet', password='strongpass123')  # Change password
ap.active(True)
print('AP IP:', ap.ifconfig()[0])  # Usually 192.168.4.1

# Socket setup
addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print('Listening on', addr)

while True:
    conn, addr = s.accept()
    print('Client connected from', addr)
    
    # Receive encrypted data
    encrypted = conn.recv(1024)
    if encrypted:
        try:
            decrypted = decrypt(encrypted)
            print('Received decrypted:', decrypted)
            
            # Send encrypted response
            response = 'Hello from server!'
            encrypted_response = encrypt(response)
            conn.send(encrypted_response)
        except Exception as e:
            print('Error:', e)
    
    conn.close()


