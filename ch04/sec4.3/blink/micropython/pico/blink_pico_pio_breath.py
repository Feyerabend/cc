from machine import Pin, Timer
import rp2
from time import sleep

# PIO PWM program (fixed)
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW)
def pwm_prog():
    wrap_target()
    pull(noblock) .side(0)  # Get duty cycle, set pin low
    mov(x, osr)             # Store duty cycle in X
    mov(y, isr)             # ISR holds max count
    label("pwmloop")
    jmp(x_dec, "skip")      # Decrement X, jump if not zero
    nop()         .side(1)  # Set pin high if X is zero
    label("skip")
    jmp(y_dec, "pwmloop")   # Decrement Y, loop until zero
    wrap()

# PIO PWM class
class PIOPWM:
    def __init__(self, sm_id, pin, max_count, count_freq):
        self._sm = rp2.StateMachine(sm_id, pwm_prog, freq=2 * count_freq, sideset_base=Pin(pin))
        # Load max count into ISR
        self._sm.put(max_count)
        self._sm.exec("pull()")
        self._sm.exec("mov(isr, osr)")
        self._sm.active(1)
        self._max_count = max_count

    def set(self, value):
        value = max(value, -1)
        value = min(value, self._max_count)
        self._sm.put(value)

# Setup PIO PWM on Pin 25
pwm = PIOPWM(0, 25, max_count=(256 ** 2) - 1, count_freq=10_000_000)

# Global variables for breathing
current = 0
direction = 1  # 1 for increasing, -1 for decreasing

def update_duty(timer):
    global current, direction
    pwm.set(current ** 2)  # Square for smoother brightness curve
    current += direction
    if current >= 255:
        current = 255
        direction = -1
    elif current <= 0:
        current = 0
        direction = 1
    # Optional: Uncomment for debugging
    # print("Update duty:", current)

# Set up timer to update duty every 20ms for ~5s cycle
timer = Timer(-1)
timer.init(period=20, mode=Timer.PERIODIC, callback=update_duty)

# Keep the program running
while True:
    print("PIO running, CPU free")
    sleep(1)
