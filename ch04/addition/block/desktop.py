#!/usr/bin/env python3

"""
Desktop Version of Pico Blockchain Messaging
- Pure Python
- Console-based messaging (copy-paste to simulate UART)
- HMAC-SHA1 signing
- Timestamp validation
- Nonce + replay protection
"""

import time
import hashlib
import hmac
import secrets
import sys

# Configuration
SECRET_KEY = b"change_this_secret_key_256bit!!"
DEVICE_ID = "PICO_A"  # Change to PICO_B on the second process
MAX_CHAIN_LENGTH = 50
MESSAGE_TIMEOUT = 30

def get_timestamp():
    return int(time.time())

def hmac_sha1(key, message: bytes) -> bytes:
    return hmac.new(key, message, hashlib.sha1).digest()


class Block:
    def __init__(self, index, previous_hash, message, timestamp=None, nonce=None):
        self.index = index
        self.previous_hash = previous_hash
        self.message = message
        self.timestamp = timestamp or get_timestamp()
        self.nonce = nonce or secrets.token_hex(4)
        self.hash = self.calculate_hash()
        self.signature = self.sign_block()

    def calculate_hash(self):
        data = f"{self.index}|{self.previous_hash}|{self.message}|{self.timestamp}|{self.nonce}".encode()
        return hashlib.sha1(data).hexdigest()

    def sign_block(self):
        signature_data = self.hash.encode()
        return hmac_sha1(SECRET_KEY, signature_data).hex()

    def verify_signature(self):
        expected = hmac_sha1(SECRET_KEY, self.hash.encode()).hex()
        return self.signature == expected

    def is_timestamp_valid(self, current_time):
        return abs(current_time - self.timestamp) < MESSAGE_TIMEOUT

    def serialize(self):
        return f"{self.index}|{self.previous_hash}|{self.message}|{self.timestamp}|{self.nonce}|{self.hash}|{self.signature}"


class SecureBlockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    @staticmethod
    def create_genesis_block():
        return Block(0, "0" * 40, "Genesis", timestamp=0, nonce="0000")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, message):
        if len(self.chain) >= MAX_CHAIN_LENGTH:
            print("Chain limit reached.")
            return None
        last_block = self.get_latest_block()
        block = Block(len(self.chain), last_block.hash, message)
        self.chain.append(block)
        return block

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
            if not current.verify_signature():
                return False
        return True

    def verify_and_add_received_block(self, block):
        now = get_timestamp()

        if not block.is_timestamp_valid(now):
            print("Rejected: timestamp invalid")
            return False

        if not block.verify_signature():
            print("Rejected: bad signature")
            return False

        expected_index = len(self.chain)
        if block.index != expected_index:
            print("Index mismatch")
            return False

        if block.previous_hash != self.get_latest_block().hash:
            print("Rejected: chain mismatch")
            return False

        self.chain.append(block)
        print(f"Accepted block {block.index}: {block.message}")
        return True


# Communication
# Sender writes outgoing messages to stdout.
# Receiver pastes incoming lines into stdin.

def send_block(chain, message):
    block = chain.add_block(message)
    if not block:
        print("Send failed.")
        return
    line = block.serialize()
    print("\n=== OUTGOING BLOCK ===")
    print(line)
    print("======================\n")

def parse_received(line):
    parts = line.strip().split("|")
    if len(parts) != 7:
        print("Invalid message format")
        return None

    i, prev, msg, ts, nonce, h, sig = parts
    block = Block(int(i), prev, msg, timestamp=int(ts), nonce=nonce)
    block.hash = h
    block.signature = sig
    return block


# Main loop
if __name__ == "__main__":
    chain = SecureBlockchain()
    counter = 0
    print(f"Device: {DEVICE_ID}")
    print("Enter text to send or paste an incoming block.")
    print("Type :chain to inspect chain.")
    print("Type :quit to exit.")
    print()

    while True:
        try:
            line = input("> ").strip()

            if line == ":quit":
                break

            if line == ":chain":
                print(f"Chain valid: {chain.verify_chain()}")
                for b in chain.chain:
                    print(f"{b.index}: {b.message} [{b.hash[:8]}...]")
                continue

            if "|" in line:
                block = parse_received(line)
                if block:
                    chain.verify_and_add_received_block(block)

            else:
                message = f"{DEVICE_ID}_{counter}:{line}"
                send_block(chain, message)
                counter += 1

        except KeyboardInterrupt:
            break
        except EOFError:
            break

    print("Shutting down..")

