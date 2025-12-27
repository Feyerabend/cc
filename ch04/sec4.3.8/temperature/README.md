
## Temperature Sensors

This folder explores temperature and pressure sensing using the BMP280 and BMP390 sensors
interfaced with the Raspberry Pi Pico, alongside the Pico's onboard temperature sensor.
The provided code and documentation demonstrate how to interface these sensors using
MicroPython and C, focusing on low-level, library-free implementations to understand the
underlying principles of sensor operation.


* BMP280: A compact sensor for measuring temperature and pressure, interfaced via SPI or I2C.
  The provided MicroPython and C code read calibration data, raw temperature values, and apply
  Bosch’s compensation formulas to calculate accurate temperature readings in Celsius.

* BMP390: A more advanced sensor offering precise temperature and pressure measurements,
  interfaced via I2C. The MicroPython code includes calibration, compensation, and altitude
  calculations using the barometric formula, tailored for accuracy in specific locations
  (e.g., Uppsala, Sweden).

* Raspberry Pi Pico Onboard Sensor: The Pico’s built-in temperature sensor is accessed via
  its ADC, with code in C and MicroPython to convert raw readings to Celsius and Fahrenheit.
  The MicroPython implementation also incorporates a button to toggle between temperature
  scales and LEDs to indicate temperature ranges using fuzzy logic.


### Features

- Low-Level Control: Both BMP280 and BMP390 implementations avoid external libraries,
  directly handling register reads/writes and compensation formulas as per Bosch’s datasheets.

- Altitude Calculation: The BMP390 code calculates altitude using the international barometric
  formula, with adjustments for local sea-level pressure (e.g., 1033 hPa for Uppsala).

- Interactive Feedback: The Pico’s onboard sensor code (in MicroPython) uses LEDs to visually
  indicate temperature ranges and a button to switch between Celsius and Fahrenheit.

- Historical Context: The documentation draws parallels between modern digital sensors and
  early analog computing devices (e.g., mechanical aneroid barometers),
  highlighting the evolution of measurement technology.


This project serves as an educational resource for understanding sensor interfacing,
digital signal processing, and embedded programming. By working directly with raw
sensor data and calibration, users gain insight into the intricacies of sensor design
and the practical application of mathematical formulas in real-world scenarios.


