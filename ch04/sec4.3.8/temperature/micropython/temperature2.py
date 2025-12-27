import time
from machine import Pin

# LED pins
green_led = Pin(2, Pin.OUT)
yellow_led = Pin(1, Pin.OUT)
red_led = Pin(0, Pin.OUT)

# read temperature sensor
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

# button for switching scales C or F
button = Pin(15, Pin.IN, Pin.PULL_DOWN)
button_pressed = False
flip = False

# depending on button, set flag it is pressed
def switch_pressed(pin):
    global button_pressed
    button_pressed = True

# interrupt set for button
button.irq(trigger=Pin.IRQ_RISING, handler=switch_pressed)

# convert sensor reading to celsius
def read_temperature_celsius():
    reading = sensor_temp.read_u16() * conversion_factor
    temperature_c = 27 - (reading - 0.706) / 0.001721
    return temperature_c

# alternative in fahrenheit
def to_farenheit(celsius):
    return celsius * 9 / 5 + 32

# fuzzy logic to set LED accordingly
def apply_fuzzy_logic_celsius(temp):
    low_threshold = 20.0
    high_threshold = 21.0
    
    # fuzzy logic: control LEDs based on temperature
    if temp < low_threshold:
        # low temperature: Green LED on, others off
        green_led.value(1)
        yellow_led.value(0)
        red_led.value(0)
    elif low_threshold <= temp < high_threshold:
        # medium temperature: Yellow LED on, others off
        green_led.value(0)
        yellow_led.value(1)
        red_led.value(0)
    else:
        # high temperature: Red LED on, others off
        green_led.value(0)
        yellow_led.value(0)
        red_led.value(1)

# main loop reading, setting LEDs, and check for button press
def temperature_led_control():
    global button_pressed, flip

    while True:
        temp_c = read_temperature_celsius()

        # switch to F or C depending on button presses
        if button_pressed == True:
            if flip == True:
                flip = False
            else:
                flip = True
            button_pressed = False

        # print in either C or F
        if flip == True:
            temp_f = to_farenheit(temp_c)
            print("Temperature: {:.2f} F".format(temp_f))
        else:
            print("Temperature: {:.2f} C".format(temp_c))

        # set how the LEDs would light up      
        apply_fuzzy_logic_celsius(temp_c)

        # wait before taking the next reading
        time.sleep(2)

# start the temperature LED control loop
temperature_led_control()
