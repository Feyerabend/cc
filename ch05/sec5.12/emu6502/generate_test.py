#!/usr/bin/env python3
"""
Simple 6502 test program generator
Creates a binary that writes "HELLO" to the console and loops
"""

# Simple program:
# LDA #'H'
# STA $F001  (console out)
# LDA #'E'
# STA $F001
# LDA #'L'
# STA $F001
# STA $F001  (write L twice)
# LDA #'O'
# STA $F001
# LDA #10    (newline)
# STA $F001
# JMP $0800  (loop forever, or could BRK to stop)

code = [
    0xA9, ord('H'),    # $0800: LDA #'H'
    0x8D, 0x01, 0xF0,  # $0802: STA $F001
    0xA9, ord('E'),    # $0805: LDA #'E'
    0x8D, 0x01, 0xF0,  # $0807: STA $F001
    0xA9, ord('L'),    # $080A: LDA #'L'
    0x8D, 0x01, 0xF0,  # $080C: STA $F001
    0x8D, 0x01, 0xF0,  # $080F: STA $F001
    0xA9, ord('O'),    # $0812: LDA #'O'
    0x8D, 0x01, 0xF0,  # $0814: STA $F001
    0xA9, 0x0A,        # $0817: LDA #10
    0x8D, 0x01, 0xF0,  # $0819: STA $F001
    0x00,              # $081C: BRK
]

# Write binary file
with open('test.bin', 'wb') as f:
    f.write(bytes(code))

print(f"Generated test.bin ({len(code)} bytes)")
print("This program writes 'HELLO' to console and stops")
print("\nTo run:")
print("  ./emu6502 test.bin")
print("\nExample monitor commands:")
print("  d           - Disassemble from PC")
print("  b 805       - Set breakpoint at $0805")
print("  s           - Step one instruction")
print("  c           - Continue to breakpoint")
