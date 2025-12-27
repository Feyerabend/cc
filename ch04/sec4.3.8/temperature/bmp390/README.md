
## BMP390

1. Read the calibration coefficients from the NVM registers.
2. Parse them into signed/unsigned integers as defined in the datasheet.
3. Apply Bosch's equations for temperature and pressure compensation.

This also examplifies a I2C connection.

### MicroPython

```python
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

# Init
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

        altitude = calculate_altitude(press_pa, sea_level_hpa=1033)  # Adjust based on local data!
        print(f"Temperature: {temp:.2f} °C, Pressure: {press_hpa:.2f} hPa, Altitude: {altitude:.2f} m")
    except Exception as e:
        print(f"Error in main loop: {e}")
    time.sleep(1)
```

Sample Output:

```
MPY: soft reboot
I2C scan: [119]
Chip ID: 0x60
Error register: 0x00
Scaled calibration coefficients:
par_t1: 7277824.0, par_t2: 1.84457768e-05, par_t3: -2.4868996e-14
par_p1: -0.008878708, par_p2: -2.00402e-05, par_p3: 1.3969838e-09, par_p4: 7.275958e-12
par_p5: 152528.0, par_p6: 370.21876, par_p7: 0.01171875, par_p8: -0.000183105468
par_p9: 1.3734792e-11, par_p10: 1.77635692e-14, par_p11: -2.981556e-19
Raw ADC: Temp=8385024, Press=6193152
Temperature: 20.39 °C, Pressure: 1030.37 hPa, Altitude: 21.52 m
Raw ADC: Temp=8385024, Press=6192896
Temperature: 20.39 °C, Pressure: 1030.39 hPa, Altitude: 21.33 m
Raw ADC: Temp=8384512, Press=6192896
Temperature: 20.38 °C, Pressure: 1030.37 hPa, Altitude: 21.52 m
Raw ADC: Temp=8384256, Press=6193152
Temperature: 20.38 °C, Pressure: 1030.33 hPa, Altitude: 21.81 m
Raw ADC: Temp=8384256, Press=6193152
Temperature: 20.38 °C, Pressure: 1030.33 hPa, Altitude: 21.81 m
Raw ADC: Temp=8384512, Press=6192640
Temperature: 20.38 °C, Pressure: 1030.39 hPa, Altitude: 21.33 m
..
```



### Barometric altitude — formula and notes

A common and practical approximation for altitude from pressure
is the international barometric formula:
```
h = 44330.77 * (1.0 - (P / P0) ** 0.190295)
```
where:
- `h` is altitude in metres,
- `P` is measured pressure in hPa,
- `P0` is reference sea-level pressure in hPa (default 1013.25 hPa).

Notes:
- Using the local current sea-level pressure (P0) gives far better altitude
  accuracy than the default 1013.25 hPa.
- This formula assumes a standard atmosphere and is suitable for typical
  hobbyist/weather uses. For precise elevation measurements you need local
  meteorological corrections.


*Notes*:
- Using the local current sea-level pressure (`P0`) significantly improves altitude accuracy.
  For the location of test in Uppsala, Sweden, on September 28, 2025, at 05:35 PM CEST,
  the sea-level pressure was approximately *1033 hPa* (based on Uppsala University station
  data at 4:00 PM, adjusted for minor diurnal variation).
- This formula assumes a standard atmosphere and is suitable for typical hobbyist or weather uses.
  For precise elevation measurements however, apply local meteorological corrections
  (e.g., temperature variations or weather fronts).
- At low altitudes (e.g., 0-100 m), pressure drops approximately *0.12 hPa per meter*,
  but this rate varies with temperature and weather conditions.


### MicroPython: Altitude Function

Returns altitude in meters from pressure (hPa).
- `p_hpa`: Measured pressure in hPa (e.g., value returned by `compensate_press` divided by 100).
- `p0_hpa`: Reference sea-level pressure in hPa (default 1013.25; set to 1033 for Uppsala accuracy).

```python
def altitude_from_pressure(p_hpa, p0_hpa=1013.25):
    # Avoid division by zero or negative pressures
    if p_hpa <= 0 or p0_hpa <= 0:
        return None
    return 44330.77 * (1.0 - (p_hpa / p0_hpa) ** 0.190295)
```

*Example Usage in the Main Loop* (after computing `press_hpa` in hPa):
```python
p0 = 1033.0  # Local sea-level pressure for Uppsala, September 28, 2025
alt = altitude_from_pressure(press_hpa, p0)
print("Altitude: {:.2f} m".format(alt))
```

__You have to calibrate these values to get even an approximate reading. Dig deeper!__

*Recommendation*: For your location, use the linear approximation or calibrate `p0_hpa` with a known elevation
(e.g., river level at 20 m ASL) to fine-tune results.



### Early aviation and "analog computers"

Before digital electronics, aircraft often relied on mechanical or analog computing
devices to derive altitude, airspeed, bombing trajectories, or firing solutions.

Barometric altitude (like the BMP390) was originally measured using a
*mechanical aneroid barometer*:
- A sealed metal capsule would expand/contract with changes in air pressure.
- That mechanical movement would drive gears and dials--giving a direct altitude readout.
- In principle, it was performing the same function as our formula:
  mapping air pressure to height, assuming a standard atmosphere.


#### Military applications (WWI-WWII era and after)

1. Altimeters:
- Standard aircraft altimeters were essentially analog computers for pressure.
- They assumed sea-level pressure = 1013.25 hPa unless the pilot adjusted the
  "Kollsman window" for local barometric pressure.
- Errors occurred if weather changed or if pressure wasn't set correctly.

2. Airspeed indicators:
- These also used pressure, comparing pitot tube (dynamic pressure) with
  static pressure from a port.
- The difference was mechanically converted into speed.

3. Bombsights & fire-control computers:
- Devices like the Norden bombsight in WWII combined barometric altitude,
  airspeed, wind correction, and ballistics in a purely analog way.
- Inside, there were gears, cams, and mechanical integrators that solved
  differential equations in real time--all based on continuous mechanical movement.

4. Naval and artillery fire-control computers:
- Similar technology but more elaborate: large electro-mechanical devices that
  continuously computed shell trajectories given bearing, range, wind, and ship motion.


#### Parallel with the BMP390 project

Reading pressure and turning it into altitude with an equation is exactly what those
early instruments did with springs, gears, and cams.
- The BMP390's silicon diaphragm is the equivalent of the old aneroid capsule.
- THe compensation math is what used to be embodied in carefully designed mechanical linkages.
- The difference is that now you can run it in digital code at kilohertz speeds and with
  much greater precision.


![BMP390](./../../../assets/image/temperature/bmp390.png)

