import rp2
from machine import Pin

# PIO program for ~1 Hz blink (0.5s on, 0.5s off)
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink_1hz():
    wrap_target()
    # ON state: 1000 cycles (~0.5s at 2000 Hz)
    set(pins, 1)
    set(x, 31)                  [6]
    label("delay_high")
    nop()                       [29]
    jmp(x_dec, "delay_high")
    # OFF state: 1000 cycles (~0.5s at 2000 Hz)
    set(pins, 0)
    set(x, 31)                  [6]
    label("delay_low")
    nop()                       [29]
    jmp(x_dec, "delay_low")
    wrap()

# Initialize PIO state machine for GPIO 25 (onboard LED)
sm = rp2.StateMachine(0, blink_1hz, freq=20000, set_base=Pin(25))

# Start the state machine
sm.active(1)

# At the time of testing .. there seems to be issues with RPI 2.
# This works at this time:
# (sysname='rp2', nodename='rp2', release='1.27.0-preview', version='v1.27.0-preview.160.g8757eb715e on 2025-09-20 (GNU 14.2.0 MinSizeRel)', machine='Raspberry Pi Pico2 with RP2350')
