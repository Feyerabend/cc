
import ucryptolib
import os
import hmac
import hashlib

# Shared secret (16 bytes for AES-128, also used for HMAC)
SECRET = b'secretkey1234567'   # CHANGE THIS! Use 32 bytes for stronger HMAC

def pad(data):
    pad_len = 16 - (len(data) % 16)
    return data + bytes([pad_len] * pad_len)

def unpad(data):
    return data[:-data[-1]]

def encrypt_and_sign(message):
    """Encrypt + append HMAC-SHA256"""
    iv = os.urandom(16)
    cipher = ucryptolib.aes(SECRET, 2, iv)           # CBC mode
    padded = pad(message.encode('utf-8'))
    ciphertext = cipher.encrypt(padded)
    
    # What we authenticate: IV + ciphertext
    to_auth = iv + ciphertext
    
    # HMAC-SHA256
    mac = hmac.new(SECRET, to_auth, hashlib.sha256).digest()   # 32 bytes
    
    # Final packet: MAC + IV + ciphertext
    return mac + to_auth

def verify_and_decrypt(packet):
    """Verify HMAC then decrypt"""
    if len(packet) < 32 + 16:  # MAC(32) + IV(16) minimum
        raise ValueError("Packet too short")
    
    mac_received = packet[:32]
    iv = packet[32:48]
    ciphertext = packet[48:]
    
    to_auth = iv + ciphertext
    mac_calculated = hmac.new(SECRET, to_auth, hashlib.sha256).digest()
    
    # Constant-time comparison (important against timing attacks)
    if not hmac.compare_digest(mac_received, mac_calculated):
        raise ValueError("HMAC verification failed - message tampered!")
    
    cipher = ucryptolib.aes(SECRET, 2, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    return unpad(decrypted_padded).decode('utf-8')

# ------------------

# WiFi setup as station
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect('PicoNet', 'strongpass123')  # Match AP credentials

while not sta.isconnected():
    pass
print('Connected to AP')

# Socket setup
SERVER_IP = '192.168.4.1'  # AP's IP
addr = socket.getaddrinfo(SERVER_IP, 8080)[0][-1]
s = socket.socket()
s.connect(addr)

# add time/nonce
#import time
#message = f"{int(time.time())}|Hello from client!"

# Send authenticated & encrypted message
message = 'Hello from client - this is protected!'
signed_packet = encrypt_and_sign(message)
s.send(signed_packet)

# Receive & verify response
packet = s.recv(1024)
if packet:
    try:
        decrypted = verify_and_decrypt(packet)
        print('Server response (verified & decrypted):', decrypted)
    except Exception as e:
        print('Security error:', e)

s.close()


