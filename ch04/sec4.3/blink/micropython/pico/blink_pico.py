import machine
import time

# init GPIO pin 25 (onboard LED)
led = machine.Pin(25, machine.Pin.OUT)

# blink LED
while True:
    led.value(1)  # on
    time.sleep(1) # delay 1 second
    led.value(0)  # off
    time.sleep(1) # delay 1 second
