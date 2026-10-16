import machine
import rp2

# Run two different blink patterns simultaneously
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW)
def blink_fast():
    wrap_target()
    nop().side(1) [3]
    nop().side(0) [3]
    wrap()

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW)
def blink_slow():
    wrap_target()
    nop().side(1) [31]
    nop().side(0) [31]
    wrap()

# Start both state machines
sm0 = rp2.StateMachine(0, blink_fast, freq=31000000, sideset_base=machine.Pin(25))  # Onboard LED
sm1 = rp2.StateMachine(1, blink_slow, freq=31000000, sideset_base=machine.Pin(16))  # External LED

sm0.active(1)
sm1.active(1)
