from machine import Pin, UART
import time

# init UART, adjust pins if needed
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

def send_message(message):
    start_char = '#'
    end_char = '*'
    full_message = f"{start_char}{message}{end_char}"
    uart.write(full_message)

while True:
    message = "Hello, World!"
    send_message(message)
    print(f"Sent: {message}")
    time.sleep(2)  # send a message every 2 seconds

