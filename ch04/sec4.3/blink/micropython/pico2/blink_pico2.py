import machine
import time

# Set up the onboard LED - Pico 2 specific approaches
try:
    # Method 1: Use "LED" identifier (preferred for Pico 2)
    led = machine.Pin("LED", machine.Pin.OUT)
    print("Using LED identifier")
except ValueError as e:
    print(f"LED identifier failed: {e}")

if led:
    print("Starting GPIO blink..")
    for i in range(10):  # Blink 10 times for testing
        led.on()
        print("LED ON")
        time.sleep(0.5)
        led.off()
        print("LED OFF")
        time.sleep(0.5)
else:
    print("LED init failed - cannot blink")
