from machine import Pin, UART
import time

# init UART
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))  # adjust pins as needed

def read_message():
    if uart.any():
        message = uart.read().decode('utf-8')  # read incoming
        if message.startswith('#') and message.endswith('*'):
            return message[1:-1]  # strip start and end characters
    return None

while True:
    received_message = read_message()
    if received_message:
        print(f"Received: {received_message}")
    time.sleep(0.1)  # delay to prevent busy waiting
