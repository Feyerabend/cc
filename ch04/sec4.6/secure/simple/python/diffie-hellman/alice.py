#!/usr/bin/env python3
import secrets

# public parameters (must be same on both sides)
p = 467      # prime
g = 2        # generator

# Alice private key
a = secrets.randbelow(p-2) + 1

# Alice public key
A = pow(g, a, p)

print("Public parameters:")
print(f"p = {p}")
print(f"g = {g}")
print()
print("Alice public value (send to Bob):")
print(A)

# Paste Bob's public value here after Bob runs his script
B = int(input("\nPaste Bob's public value: "))

# Shared secret
shared_secret = pow(B, a, p)

print("\nAlice shared secret:")
print(shared_secret)
