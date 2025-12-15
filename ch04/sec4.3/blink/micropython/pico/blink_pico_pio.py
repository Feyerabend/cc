import rp2
from machine import Pin

# PIO assembly program
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink():
    wrap_target()
    nop()  # nothing for one cycle
    set(pins, 1) # set pin high
    nop() [31]  # wait 32 cycles
    set(pins, 0) # set pin low
    nop() [31]  # wait 32 cycles
    wrap()

# init PIO state machine
sm = rp2.StateMachine(0, blink, freq=2000, set_base=Pin(25))

# start state machine
sm.active(1)
