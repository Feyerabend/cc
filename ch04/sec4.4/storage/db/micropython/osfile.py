import machine, sdcard
import utime, uos

# chip select (CS) pin (start high)
cs = machine.Pin(1, machine.Pin.OUT)

# init SPI peripheral (start with 1 MHz)
spi = machine.SPI(0,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(2),
                  mosi=machine.Pin(3),
                  miso=machine.Pin(4))

# init SD card
sd = sdcard.SDCard(spi, cs)

# mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")



# -- file operations which can be done on the SD card--

import os

# list files and directories
os.listdir("/sd")

# check if a file or directory exists (returns stat info)
os.stat("/sd/temp_log.csv")

# remove a file
os.remove("/sd/temp_log.csv")

# create a directory
os.mkdir("/sd/mydir")

# remove a directory (must be empty)
os.rmdir("/sd/mydir")

# get the current working directory
os.getcwd()

# change current directory
os.chdir("/sd")

# rename or move a file
os.rename("/sd/old.csv", "/sd/new.csv")

# get filesystem info (total, used, free)
os.statvfs("/sd")
