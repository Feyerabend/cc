from machine import Pin, SPI
import time

# BME280 SPI setup
CS_PIN = Pin(8, Pin.OUT, value=1)  # GPIO 8 (Physical Pin 11)
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB,
          sck=Pin(10), mosi=Pin(11), miso=Pin(12))  # SPI1: Pins 14, 15, 16

# BME280 register addresses
REG_DIG_T1 = 0x88
REG_CTRL_MEAS = 0xF4
REG_TEMP = 0xFA

# SPI read/write functions
def read_reg(reg, num_bytes):
    CS_PIN.value(0)  # Select chip
    spi.write(bytes([reg | 0x80]))  # Read mode (MSB=1)
    data = spi.read(num_bytes)
    CS_PIN.value(1)  # Deselect chip
    return data

def write_reg(reg, data):
    CS_PIN.value(0)  # Select chip
    spi.write(bytes([reg & 0x7F]))  # Write mode (MSB=0)
    spi.write(bytes([data]))
    CS_PIN.value(1)  # Deselect chip

# Read an unsigned short (little endian)
def read_u16(reg):
    d = read_reg(reg, 2)
    return d[0] | (d[1] << 8)

# Read a signed short
def read_s16(reg):
    val = read_u16(reg)
    return val if val < 32768 else val - 65536

# Get calibration data for temperature
dig_T1 = read_u16(REG_DIG_T1)
dig_T2 = read_s16(REG_DIG_T1 + 2)
dig_T3 = read_s16(REG_DIG_T1 + 4)

# Configure sensor: oversampling x1, normal mode
write_reg(REG_CTRL_MEAS, 0x27)

def read_temperature():
    data = read_reg(REG_TEMP, 3)
    raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    # Compensation formula from datasheet
    var1 = (((raw >> 3) - (dig_T1 << 1)) * dig_T2) >> 11
    var2 = (((((raw >> 4) - dig_T1) * ((raw >> 4) - dig_T1)) >> 12) * dig_T3) >> 14
    t_fine = var1 + var2
    T = (t_fine * 5 + 128) >> 8
    return T / 100.0

# Main loop
while True:
    temp = read_temperature()
    print("Temperature:", temp, "°C")
    time.sleep(1)
