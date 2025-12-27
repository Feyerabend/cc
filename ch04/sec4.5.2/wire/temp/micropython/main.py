from machine import Pin, UART, ADC
import time

uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

temp_sensor = ADC(4)

led = Pin(25, Pin.OUT)  # onboard LED

def read_temperature():
    reading = temp_sensor.read_u16()
    voltage = reading * 3.3 / 65535
    temperature = 27 - (voltage - 0.706) / 0.001721
    
    return round(temperature, 1)

def send_uart_message(message):
    start_char = '#'
    end_char = '*'
    full_message = f"{start_char}{message}{end_char}"
    uart.write(full_message.encode('utf-8'))

def blink_led():
    led.on()
    time.sleep(0.1)
    led.off()

print("Temperature UART Transmitter Starting ..")
print("Connect UART pins (TX=GP4, RX=GP5) to logic analyser or another device")
print("Messages sent every 2 seconds")

counter = 0

while True:
    try:
        temp_c = read_temperature()
        temp_f = (temp_c * 9/5) + 32
        
        message = f"TEMP:{temp_c}C,{temp_f:.1f}F,COUNT:{counter}"
        
        send_uart_message(message)
        blink_led()
        
        print(f"Transmitted: {message}")
        
        counter += 1
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\nTransmission stopped")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)
