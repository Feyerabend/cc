
## Secure Boot Chain

A hands-on demonstration that runs on Raspberry Pi Pico 2 +
Pimoroni Display Pack 2.0, teaching secure boot concepts
through interactive scenarios.


### What You'll Learn

This demo shows how modern devices protect themselves from malicious code:

| Security Concept | What It Does | Real-World Example |
|------------------|--------------|--------------------|
| *Root of Trust* | The first thing that runs, built into hardware | iPhone's boot ROM |
| *Chain of Trust* | Each stage verifies the next before running it | UEFI Secure Boot on PCs |
| *Digital Signatures* | Proves code came from the right developer | App Store code signing |
| *Hash Checking* | Detects if code was modified | Android verified boot |
| *Version Protection* | Prevents downgrading to vulnerable versions | iOS won't let you install old versions |


### Six Interactive Scenarios

Use the buttons to explore different security situations:

1. *Successful Boot* - Everything verifies correctly
2. *Tampered Code* - Someone modified the binary -> Detected!
3. *Rollback Attack* - Attacker tries to install old vulnerable version -> Blocked!
4. *Wrong Signature* - Code signed with wrong key -> Rejected!
5. *Chain of Trust* - Visual explanation of who verifies whom
6. *Attack Detection* - Multiple failed attempts -> System locks down

#### Button Controls
- *A* -> Next scenario
- *B* -> Previous scenario  
- *X* -> Run selected scenario
- *Y* -> Toggle auto-advance through all scenarios


### What's Real vs. Simplified

#### Real Production Practices

The code demonstrates genuine secure coding techniques:
- Constant-time comparisons (prevents timing attacks)
- Secure memory wiping (prevents key leakage)
- Bounds checking on all operations
- Multiple verification layers
- Proper error handling
- Attack detection and rate limiting

#### Educational Simplifications

To keep things understandable, some parts are simplified:

*Cryptography*: Uses simple XOR operations instead of:
- Real signatures: Ed25519, ECDSA, RSA
- Real hashing: SHA-256, SHA-512

*Storage*: Everything is in RAM (disappears on reset). Real systems use:
- Hardware eFuses (permanent, one-time programmable)
- Protected flash memory
- Secure elements

*Enforcement*: Shows verification results on screen. Real systems:
- Actually refuse to run unverified code
- Use hardware memory protection
- Enforce with CPU privilege levels

Every device you trust--your phone, laptop, car, medical device--uses
these exact concepts to prevent attackers from installing malicious code.
This demo lets you see how it works without needing specialised equipment
or risking bricking a device.

### Requirements

- *Raspberry Pi Pico 2* (RP2350 microcontroller)
- *Pimoroni Display Pack 2.0* (320×240 screen with buttons)

The Pico 2's RP2350 chip actually has real secure boot features
(OTP memory, signature verification, TrustZone). This demo runs
in software to show the concepts clearly, but you could implement
real secure boot using the RP2350's hardware features afterward.

This is your project!


### Building this Project

```bash
## Install Pico SDK if you haven't already
## See: https://github.com/raspberrypi/pico-sdk

mkdir build
cd build
cmake ..
make

## Flash to Pico 2 (hold BOOTSEL button, plug in USB)
cp secure_boot_demo.uf2 /Volumes/RPI-RP2/  ## macOS
## or
cp secure_boot_demo.uf2 /media/RPI-RP2/    ## Linux
```

### Learning Path

1. *Start with Scenario 1* (Successful Boot) - See how verification works
2. *Try Scenario 5* (Chain of Trust) - Understand the big picture
3. *Explore the attacks* (Scenarios 2-4) - See how defenses catch them
4. *Enable auto-advance* (Button Y) - Watch all scenarios in sequence

After understanding these concepts, you can explore:
- RP2350 datasheet (Chapter on Secure Boot)
- Pico SDK secure boot libraries
- MCUboot (widely used bootloader)
- U-Boot verified boot documentation

The coding patterns here are production-grade—the cryptography and
hardware integration are simplified for learning.


### Common Questions You Might Have?

*Q: Is this actually secure?*  
A: No, but it is educational. The crypto is toy-level,
   and everything runs in unprivileged software.
   But the *concepts* and *coding practices* are real.
   (As discussed in chapter 7, security is a fuzzy
   concept in the way that nothing really is secure ..)

*Q: Why not use real crypto?*  
A: To keep the code readable and focus on the overall
   structure. Adding real Ed25519 would add thousands
   of lines of library code.

*Q: Can I use this in a product?*  
A: __No!__ Use established libraries (Mbed TLS, wolfSSL)
   and the RP2350's hardware features. This is a teaching tool.
   Nothing more.

*Q: What's the point then?*  
A: Understanding the *why* and *how* of secure boot before
   diving into complex production implementations. It's like
   learning physics with frictionless planes before dealing
   with real-world engineering.
