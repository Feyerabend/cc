
![SD Card install](./../../../assets/image/storage/install-sdcard.png)

The most common and simple way is to use the classic `sdcard.py` driver (a small MicroPython library here included).

### Quick steps
1. Format your microSD card as *FAT32* on your computer (most cards ≤32GB work best).
2. In *Thonny* (with Pico connected + MicroPython installed):
   - Download or copy the *`sdcard.py`* code from here:  
     https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py
   - Save it directly to your Pico (preferably in a `/lib` folder -> right-click -> New folder -> name it "lib"),
   OR through the installation of external libraries as you can see from the image.

3. Typical basic usage in your main program looks like this:

```python
import machine
import sdcard
import os

# Example using SPI1 (very common pinout)
spi = machine.SPI(1,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=machine.Pin(10),
    mosi=machine.Pin(11),
    miso=machine.Pin(8))

cs = machine.Pin(9, machine.Pin.OUT)  # Chip Select pin (can be almost any free GPIO)
sd = sdcard.SDCard(spi, cs)           # Create SD card object
os.mount(sd, "/sd")                   # Mount it -> appears as folder /sd

# Now you can use normal file operations ..
with open("/sd/log.txt", "w") as f:
    f.write("Hello from Pico!\n")

print(os.listdir("/sd"))              # See what's on the card
```
