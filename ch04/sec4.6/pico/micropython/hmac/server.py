
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
    
    packet = conn.recv(1024)
    if packet:
        try:
            decrypted = verify_and_decrypt(packet)
            print('Received (verified & decrypted):', decrypted)
            
            response = 'Hello from server! Time is secure.'
            signed_response = encrypt_and_sign(response)
            conn.send(signed_response)
        except Exception as e:
            print('Security error or bad packet:', e)
            conn.send(b'ERROR: Invalid message')
    
    conn.close()


