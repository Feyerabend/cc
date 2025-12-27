from machine import Pin, I2C
import time
import math

BMP390_ADDR = 0x77
REG_CHIP_ID = 0x00
REG_STATUS = 0x03
REG_CALIB_DATA = 0x31
REG_CMD = 0x7E
REG_PWR_CTRL = 0x1B
REG_OSR = 0x1C
REG_ODR = 0x1D
REG_CONFIG = 0x1F
REG_PRESS_MSB = 0x04
REG_ERR_REG = 0x02
REG_IF_CONF = 0x1A

BMP390_ID = 0x60

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

def read_reg(addr, nbytes=1):
    try:
        return i2c.readfrom_mem(BMP390_ADDR, addr, nbytes)
    except Exception as e:
        print(f"I2C read error at addr 0x{addr:02x}: {e}")
        return None

def write_reg(addr, data):
    try:
        i2c.writeto_mem(BMP390_ADDR, addr, bytes([data]))
    except Exception as e:
        print(f"I2C write error at addr 0x{addr:02x}: {e}")

# Initialize
try:
    print(f"I2C scan: {i2c.scan()}")
    chip_id = read_reg(REG_CHIP_ID)
    if chip_id is None or chip_id[0] != BMP390_ID:
        raise Exception(f"BMP390 not found! Chip ID: {chip_id}")
    print(f"Chip ID: 0x{chip_id[0]:02x}")
except Exception as e:
    print(f"Error initializing sensor: {e}")
    raise

# Soft reset
write_reg(REG_CMD, 0xB6)
time.sleep(0.05)  # Initial delay after reset

# Poll for cmd_rdy after reset
def wait_for_cmd_ready(timeout=2.0):
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = read_reg(REG_STATUS, 1)
        if status and (status[0] & 0x10):  # Check cmd_rdy (bit 4)
            return True
        time.sleep(0.01)
    print(f"Status after reset wait: 0x{status[0]:02x} if status else 'None'")
    return False

if not wait_for_cmd_ready():
    print("Command not ready after reset timeout")
    raise Exception("Sensor reset failed")

# Disable I2C watchdog to prevent timeouts
write_reg(REG_IF_CONF, 0x00)  # spi3=0, i2c_wdt_en=0

# Configure sensor - Use lower oversampling to avoid potential config errors
write_reg(REG_OSR, 0x00)  # Temp x1 (0b000), Press x1 (0b000) - ultra low power
write_reg(REG_ODR, 0x03)  # 25 Hz to give more time
write_reg(REG_CONFIG, 0x00)  # IIR filter bypass (0b000)
time.sleep(0.1)

# Check for errors after configuration
err = read_reg(REG_ERR_REG, 1)
if err:
    print(f"Error register: 0x{err[0]:02x}")
    if err[0] & 0x04:
        print("Configuration error detected!")
    if err[0] & 0x02:
        print("Command error detected!")
    if err[0] & 0x01:
        print("Fatal error detected!")

# Function to trigger forced mode measurement
def trigger_forced_mode():
    write_reg(REG_PWR_CTRL, 0x13)  # Forced mode (0b01), temp + press enabled (0b00010011)

# Wait for data ready
def wait_for_data_ready(timeout=1.0):
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = read_reg(REG_STATUS, 1)
        if status and (status[0] & 0x60):  # Check drdy_press (bit 5) and drdy_temp (bit 6)
            return True
        time.sleep(0.005)  # Shorter poll interval
    print(f"Status after data wait: 0x{status[0]:02x} if status else 'None'")
    return False

# Calibration
calib = read_reg(REG_CALIB_DATA, 21)
if calib is None or len(calib) != 21:
    raise Exception("Failed to read calibration data")

def to_signed_16(val):
    if val > 32767:
        val -= 65536
    return val

def to_signed_8(val):
    if val > 127:
        val -= 256
    return val

par_t1 = int.from_bytes(calib[0:2], 'little') / 2**-8
par_t2 = int.from_bytes(calib[2:4], 'little') / 2**30
par_t3 = to_signed_8(calib[4]) / 2**48
par_p1 = (to_signed_16(int.from_bytes(calib[5:7], 'little')) - 2**14) / 2**20
par_p2 = (to_signed_16(int.from_bytes(calib[7:9], 'little')) - 2**14) / 2**29
par_p3 = to_signed_8(calib[9]) / 2**32
par_p4 = to_signed_8(calib[10]) / 2**37
par_p5 = int.from_bytes(calib[11:13], 'little') / 2**-3
par_p6 = int.from_bytes(calib[13:15], 'little') / 2**6
par_p7 = to_signed_8(calib[15]) / 2**8
par_p8 = to_signed_8(calib[16]) / 2**15
par_p9 = to_signed_16(int.from_bytes(calib[17:19], 'little')) / 2**48
par_p10 = to_signed_8(calib[19]) / 2**48
par_p11 = to_signed_8(calib[20]) / 2**65

print("Scaled calibration coefficients:")
print(f"par_t1: {par_t1}, par_t2: {par_t2}, par_t3: {par_t3}")
print(f"par_p1: {par_p1}, par_p2: {par_p2}, par_p3: {par_p3}, par_p4: {par_p4}")
print(f"par_p5: {par_p5}, par_p6: {par_p6}, par_p7: {par_p7}, par_p8: {par_p8}")
print(f"par_p9: {par_p9}, par_p10: {par_p10}, par_p11: {par_p11}")

t_lin = 0.0

def compensate_temp(adc_t):
    global t_lin
    partial_data1 = adc_t - par_t1
    partial_data2 = partial_data1 * par_t2
    t_lin = partial_data2 + (partial_data1 * partial_data1) * par_t3
    return t_lin  # °C (no /100 per datasheet)

def compensate_press(adc_p):
    partial_data1 = par_p6 * t_lin
    partial_data2 = par_p7 * (t_lin ** 2)
    partial_data3 = par_p8 * (t_lin ** 3)
    partial_out1 = par_p5 + partial_data1 + partial_data2 + partial_data3

    partial_data1 = par_p2 * t_lin
    partial_data2 = par_p3 * (t_lin ** 2)
    partial_data3 = par_p4 * (t_lin ** 3)
    partial_out2 = adc_p * (par_p1 + partial_data1 + partial_data2 + partial_data3)

    partial_data1 = adc_p ** 2
    partial_data2 = par_p9 + par_p10 * t_lin
    partial_data3 = partial_data1 * partial_data2
    partial_data4 = partial_data3 + (adc_p ** 3) * par_p11

    return partial_out1 + partial_out2 + partial_data4  # Pa

def read_raw():
    data = read_reg(REG_PRESS_MSB, 6)
    if data is None or len(data) != 6:
        print("Failed to read sensor data")
        return None, None
    adc_p = data[0] | (data[1] << 8) | (data[2] << 16)
    adc_t = data[3] | (data[4] << 8) | (data[5] << 16)
    return adc_t, adc_p

def calculate_altitude(pressure_pa, sea_level_hpa=1013.25):
    pressure_hpa = pressure_pa / 100
    return 44330.77 * (1 - math.pow(pressure_hpa / sea_level_hpa, 0.190295))

# Main loop using forced mode
while True:
    try:
        trigger_forced_mode()
        if not wait_for_data_ready():
            print("Data not ready after timeout in forced mode")
            time.sleep(1)
            continue

        adc_t, adc_p = read_raw()
        if adc_t is None or adc_p is None:
            print("Skipping invalid reading")
            time.sleep(1)
            continue

        print(f"Raw ADC: Temp={adc_t}, Press={adc_p}")
        temp = compensate_temp(adc_t)
        press_pa = compensate_press(adc_p)
        press_hpa = press_pa / 100

        altitude = calculate_altitude(press_pa, sea_level_hpa=1033)  # Adjust based on local data
        print(f"Temperature: {temp:.2f} °C, Pressure: {press_hpa:.2f} hPa, Altitude: {altitude:.2f} m")
    except Exception as e:
        print(f"Error in main loop: {e}")
    time.sleep(1)