import hashlib
import hmac
import secrets

SECRET_KEY = secrets.token_bytes(32)
message    = b"transfer:alice:bob:100"

# Bad: a plain hash provides integrity but NOT authenticity.
# Anyone who knows the message can recompute the same digest. An attacker
# can also extend the message without knowing the key (length-extension
# attack on SHA-256/SHA-1/MD5 applied to hash(key || msg) constructions).
bad_mac = hashlib.sha256(SECRET_KEY + message).digest()

# Safe: HMAC binds the key into both the inner and outer hash, closing the
# length-extension attack and proving that whoever produced the tag knew
# the key. Comparison must still be constant-time.
good_mac = hmac.new(SECRET_KEY, message, hashlib.sha256).digest()

def verify(received_mac: bytes, message: bytes) -> bool:
    expected = hmac.new(SECRET_KEY, message, hashlib.sha256).digest()
    return hmac.compare_digest(expected, received_mac)  # constant-time
