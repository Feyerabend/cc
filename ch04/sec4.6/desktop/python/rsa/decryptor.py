#!/usr/bin/env python3

def bytes_to_int(b):
    return int.from_bytes(b, "big")


def int_to_bytes(i, size):
    return i.to_bytes(size, "big")


def rsa_block_size(n):
    return (n.bit_length() - 1) // 8


def rsa_decrypt_message(blocks, d, n):
    k = rsa_block_size(n)
    out = bytearray()

    for c in blocks:
        m = pow(c, d, n)
        block = int_to_bytes(m, k)
        out.extend(block)

    # Remove padding zero bytes added by fixed-size blocks
    return out.rstrip(b"\x00").decode("ascii")


if __name__ == "__main__":
    # Same toy RSA parameters
    n = 3233
    d = 2753

    # Example: copy output from encryptor.py here
    cipher_blocks = [2170, 1313, 745, 745, 2185, 1992, 1107, 2185, 2412, 745, 1773]

    plaintext = rsa_decrypt_message(cipher_blocks, d, n)

    print("Cipher blocks:")
    print(cipher_blocks)
    print()
    print("Decrypted plaintext:")
    print(plaintext)
