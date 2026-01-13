#!/usr/bin/env python3

def bytes_to_int(b):
    return int.from_bytes(b, "big")


def int_to_bytes(i, size):
    return i.to_bytes(size, "big")


def rsa_block_size(n):
    # Maximum number of bytes that fit into n
    return (n.bit_length() - 1) // 8


def rsa_encrypt_message(msg, e, n):
    data = msg.encode("ascii")
    k = rsa_block_size(n)

    blocks = []
    for i in range(0, len(data), k):
        block = data[i:i + k]
        m = bytes_to_int(block)
        if m >= n:
            raise ValueError("Message block too large for modulus")
        c = pow(m, e, n)
        blocks.append(c)

    return blocks


if __name__ == "__main__":
    # Example RSA parameters (toy values, not secure)
    n = 3233
    e = 17

    plaintext = "hello world"

    cipher_blocks = rsa_encrypt_message(plaintext, e, n)

    print("Plaintext:")
    print(plaintext)
    print()
    print("Cipher blocks:")
    print(cipher_blocks)
