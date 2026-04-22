import hashlib
import secrets

# Bad: fast hash, no salt. Two users with the same password produce the same
# digest, enabling precomputed rainbow-table lookups.
def store_bad(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Better but still wrong: salted SHA-256 is unique per user but remains
# fast — an attacker with a leaked database can still try billions of
# candidate passwords per second on a GPU.
def store_mediocre(password: str) -> tuple[bytes, str]:
    salt = secrets.token_bytes(16)
    digest = hashlib.sha256(salt + password.encode()).hexdigest()
    return salt, digest

# Correct: hashlib.scrypt is memory-hard and CPU-hard by design.
# n (work factor), r (block size), p (parallelism) control cost.
# Tune n so that a single hash takes ~100 ms on your server hardware;
# an attacker running the same function pays the same per guess.
def store_good(password: str) -> tuple[bytes, bytes]:
    salt = secrets.token_bytes(16)
    dk   = hashlib.scrypt(
        password.encode(), salt=salt,
        n=2**15, r=8, p=1,          # adjust n upward as hardware improves
        dklen=32
    )
    return salt, dk

def verify_good(password: str, salt: bytes, stored_dk: bytes) -> bool:
    candidate = hashlib.scrypt(
        password.encode(), salt=salt,
        n=2**15, r=8, p=1, dklen=32
    )
    return secrets.compare_digest(candidate, stored_dk)  # constant-time
