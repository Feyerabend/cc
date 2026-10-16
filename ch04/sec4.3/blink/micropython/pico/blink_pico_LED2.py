import machine
import rp2

# Run two blink patterns at the same time, one on each state machine.
# Both run the same program; only the clock frequency differs.
#
# Each half period takes 1 + 7 + 32 * (30 + 1) = 1000 cycles, so the
# LED blinks at freq / 2000 Hz. Even the slowest PIO clock is far too
# fast to see a blink, which is why the program counts in a loop.
# (The lowest PIO frequency is about 1.9 kHz on a Pico and 2.3 kHz on
# a Pico 2.)
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink():
    wrap_target()
    set(pins, 1)
    set(x, 31)              [6]
    label("high")
    nop()                   [29]
    jmp(x_dec, "high")
    set(pins, 0)
    set(x, 31)              [6]
    label("low")
    nop()                   [29]
    jmp(x_dec, "low")
    wrap()

# Start both state machines
sm0 = rp2.StateMachine(0, blink, freq=10000, set_base=machine.Pin(25))  # Onboard LED, 5 Hz
sm1 = rp2.StateMachine(1, blink, freq=2500, set_base=machine.Pin(16))   # External LED, 1.25 Hz

sm0.active(1)
sm1.active(1)
