import hashlib, secrets

token  = secrets.token_bytes(32)           # secure; NOT random.random()
digest = hashlib.sha256(b"example").hexdigest()
