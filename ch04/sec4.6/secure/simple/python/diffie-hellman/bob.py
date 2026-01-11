#!/usr/bin/env python3
import secrets

# same public parameters
p = 467
g = 2

# Bob private key
b = secrets.randbelow(p-2) + 1

# Bob public key
B = pow(g, b, p)

print("Public parameters:")
print(f"p = {p}")
print(f"g = {g}")
print()
print("Bob public value (send to Alice):")
print(B)

# Paste Alice's public value here after Alice runs her script
A = int(input("\nPaste Alice's public value: "))

# Shared secret
shared_secret = pow(A, b, p)

print("\nBob shared secret:")
print(shared_secret)
