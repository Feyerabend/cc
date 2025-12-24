
## How the RP2040/RP2350 Uses Flash Memory

The Raspberry Pi Pico (and Pico 2) has an interesting storage
architecture that's worth understanding in detail.


### Flash Memory Architecture

The Pico boards use external QSPI flash memory (typically 2-16MB)
connected to the RP2040/RP2350 chip. This flash is divided into
several logical sections:


*1. Bootloader (ROM)*
- The RP2040/RP2350 has a built-in ROM bootloader that cannot be erased
- When you hold BOOTSEL and plug in the Pico, this bootloader runs and
  presents the device as a USB mass storage device
- This bootloader understands UF2 (USB Flashing Format) files

*2. Application Code Area*
- Your MicroPython firmware or other programs live here
- Starts at flash address 0x10000000
- Takes up whatever space it needs (MicroPython is typically 600KB-1.5MB)

*3. Filesystem Area*
- The remaining flash is used for file storage
- MicroPython creates a simple filesystem here called "littlefs"


### How UF2 Flashing Works

When you drag a `.uf2` file onto the Pico in BOOTSEL mode:

1. The ROM bootloader receives the UF2 file
2. It extracts the binary data and writes it directly to flash memory at specified addresses
3. The UF2 format includes metadata about where each block should go
4. Once complete, the bootloader automatically reboots and runs your new firmware

This is why UF2 flashing is so reliable: it's handled by unchangeable ROM code.


### MicroPython's Approach to Storage

MicroPython does create a *real filesystem* on the Pico's flash,
but it's not like a traditional PC filesystem:


#### The LittleFS Filesystem

MicroPython uses *littlefs*, a filesystem designed specifically for microcontrollers:

- *Power-loss resilient*: Designed to handle sudden power loss gracefully
- *Wear leveling*: Spreads writes across flash to extend lifetime
- *Small overhead*: Minimal RAM and code size requirements
- *Block-based*: Works with the flash memory's erase block constraints


#### How It Works in Practice

```python
# When you write to a file in MicroPython:
with open('data.txt', 'w') as f:
    f.write('Hello, World!')

# This actually:
# 1. Goes through the littlefs driver
# 2. Manages flash erase blocks (typically 4KB sectors)
# 3. Updates filesystem metadata
# 4. Writes your data to flash
```


#### Memory Layout

When MicroPython boots on a Pico:

```
Flash Memory (2MB typical):
├─ 0x000000 - 0x0FFFFF: MicroPython firmware (~1MB)
└─ 0x100000 - 0x1FFFFF: littlefs filesystem (~1MB)
```

You can check available space:
```python
import os
stats = os.statvfs('/')
free_space = stats[0] * stats[3]  # block size × free blocks
print(f"Free space: {free_space / 1024:.1f} KB")
```


### Flash Memory Constraints

There are important limitations:

- *Erase Block Size*: Flash must be erased in 4KB blocks before writing.
  You can't just overwrite single bytes.
- *Write Cycles*: Flash has limited write endurance (typically 10,000-100,000
  cycles per block). This is why wear leveling is important.
- *No Direct Byte Access*: Unlike RAM, you can't directly modify flash,
  you must erase and rewrite entire blocks.
- *Speed*: Flash writes are slower than RAM (milliseconds vs nanoseconds).


### Comparing to "No Filesystem" Approaches

Some bare-metal applications skip the filesystem entirely and:
- Store data at fixed flash addresses
- Manually manage erase/write operations
- Use the flash like a large EEPROM

MicroPython's filesystem approach is much more convenient for most use cases,
as it handles all the complexity of flash management while providing familiar file operations.


### Practical Considerations

*Preserving the Filesystem*: When you flash a new UF2 file, it typically only
overwrites the firmware area, leaving your files intact (though backups are wise).

*RAM vs Flash*: Your Python code runs from flash, but variables live in RAM
(264KB on Pico). Large data structures need careful memory management.

*Persistence*: Files in the littlefs filesystem survive reboots and power cycles,
making it perfect for configuration files, data logging, etc.



### Direct Flash Memory Access in MicroPython on Pico

By working directly with the flash memory, you can bypass the filesystem when needed.
MicroPython on the Pico provides a `_rp2` module with flash access functions:

```python
import _rp2

# Read flash memory
def read_flash(address, length):
    """Read raw bytes from flash at given address"""
    buffer = bytearray(length)
    _rp2.Flash().readblocks(address // 4096, buffer)
    return buffer

# Write flash memory (more complex - requires erase first)
def write_flash(address, data):
    """Write data to flash (must be on 4KB boundary)"""
    flash = _rp2.Flash()
    # Flash operations work in 4KB blocks
    flash.writeblocks(address // 4096, data)
```

#### Using the `machine` Module for Flash

A more practical approach uses the `machine.Flash` class:

```python
import machine

# Create a Flash object
flash = machine.Flash()

# Flash appears as a block device
# Block size is typically 4096 bytes (4KB)
block_size = 4096

# Read a block (block numbers, not byte addresses)
block_num = 256  # This would be at byte address 256 * 4096
data = bytearray(block_size)
flash.readblocks(block_num, data)
print(f"Read {len(data)} bytes from block {block_num}")

# Write a block (must erase first!)
new_data = bytearray(b'Hello Flash!' + b'\xff' * (block_size - 12))
flash.writeblocks(block_num, new_data)
```


### Important: Flash Memory Constraints

__1. *Sector/Block Alignment*__

Flash operations must happen on 4KB (4096 byte) boundaries:

```python
# WRONG - will fail or behave unexpectedly
address = 1234  # Random address

# RIGHT - aligned to 4KB
address = 4096 * n  # where n is an integer
```

__2. *Erase Before Write*__

Flash memory bits can only be changed from 1 to 0 when writing.
To change 0 to 1, you must erase (which sets all bits to 1):

```python
import _rp2

def erase_and_write_flash(block_num, data):
    """Properly erase then write flash"""
    flash = _rp2.Flash()
    
    # Erase the block (sets all bytes to 0xFF)
    flash.ioctl(6, block_num)  # 6 is the ERASE_BLOCK command
    
    # Now write the data
    flash.writeblocks(block_num, data)
```


__3. *Safe Flash Regions*__

You must be extremely careful about WHERE you write.
Writing to the wrong address can brick your device:

```python
import os

# Find out where the filesystem ends
# This tells you safe areas for custom flash storage
def find_flash_layout():
    # MicroPython firmware typically uses first ~1-1.5MB
    # Filesystem uses remaining space
    
    # Get filesystem info
    statvfs = os.statvfs('/')
    block_size = statvfs[0]
    total_blocks = statvfs[2]
    
    # Flash typically starts at 2MB - filesystem_size
    # So end of filesystem is safe to use after
    print(f"Filesystem block size: {block_size}")
    print(f"Filesystem total blocks: {total_blocks}")
    print(f"Filesystem size: {block_size * total_blocks} bytes")
```


### Practical Example: Custom Configuration Storage

Here's a safe way to store configuration data in a dedicated flash area:

```python
import struct
import machine

class FlashConfig:
    """Store configuration in a dedicated flash sector"""
    
    # Use a high block number (near end of flash, after filesystem)
    # For 2MB flash: blocks 0-511, let's use block 500
    CONFIG_BLOCK = 500
    BLOCK_SIZE = 4096
    MAGIC = 0xC0FFEE  # Magic number to verify valid config
    
    def __init__(self):
        self.flash = machine.Flash()
    
    def save_config(self, config_dict):
        """Save configuration dictionary to flash"""
        # Serialize config to bytes
        import json
        config_json = json.dumps(config_dict)
        config_bytes = config_json.encode('utf-8')
        
        if len(config_bytes) > self.BLOCK_SIZE - 8:
            raise ValueError("Config too large!")
        
        # Create block with magic number and data
        block = bytearray(self.BLOCK_SIZE)
        struct.pack_into('<I', block, 0, self.MAGIC)  # Magic at start
        struct.pack_into('<I', block, 4, len(config_bytes))  # Length
        block[8:8+len(config_bytes)] = config_bytes
        
        # Erase and write
        try:
            # Erase the block first
            self.flash.ioctl(6, self.CONFIG_BLOCK)
            # Write new data
            self.flash.writeblocks(self.CONFIG_BLOCK, block)
            print("Config saved successfully")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load_config(self):
        """Load configuration from flash"""
        block = bytearray(self.BLOCK_SIZE)
        
        try:
            self.flash.readblocks(self.CONFIG_BLOCK, block)
            
            # Check magic number
            magic = struct.unpack_from('<I', block, 0)[0]
            if magic != self.MAGIC:
                print("No valid config found")
                return None
            
            # Read length and data
            length = struct.unpack_from('<I', block, 4)[0]
            config_bytes = bytes(block[8:8+length])
            
            # Deserialize
            import json
            config_dict = json.loads(config_bytes.decode('utf-8'))
            print("Config loaded successfully")
            return config_dict
            
        except Exception as e:
            print(f"Error loading config: {e}")
            return None

# Usage
config = FlashConfig()

# Save some settings
settings = {
    'wifi_ssid': 'MyNetwork',
    'sensor_interval': 60,
    'debug_mode': True
}
config.save_config(settings)

# Later, load them back
loaded = config.load_config()
print(loaded)
```


### Memory-Mapped Flash Access

For reading (not writing), you can access flash as memory-mapped:

```python
import uctypes

# Flash is mapped starting at 0x10000000 on RP2040/RP2350
FLASH_BASE = 0x10000000

def read_flash_direct(offset, length):
    """Read flash using memory-mapped access (read-only!)"""
    address = FLASH_BASE + offset
    # Create a byte array view of the memory
    return bytes(uctypes.bytearray_at(address, length))

# Example: read first 256 bytes of flash (where firmware starts)
firmware_header = read_flash_direct(0, 256)
print(f"First bytes: {firmware_header[:16].hex()}")
```


### Wear Leveling Considerations

Flash has limited write cycles. Here's a simple wear-leveling strategy:

```python
class WearLeveledStorage:
    """Rotate writes across multiple flash blocks"""
    
    def __init__(self, start_block, num_blocks):
        self.start_block = start_block
        self.num_blocks = num_blocks
        self.flash = machine.Flash()
        self.current_block = 0
    
    def write_data(self, data):
        """Write data to next block in rotation"""
        block_num = self.start_block + self.current_block
        
        # Prepare block
        block = bytearray(4096)
        block[:len(data)] = data
        
        # Erase and write
        self.flash.ioctl(6, block_num)
        self.flash.writeblocks(block_num, block)
        
        # Move to next block (circular)
        self.current_block = (self.current_block + 1) % self.num_blocks
        
        return block_num
    
    def find_latest_data(self):
        """Find the most recently written block"""
        # Implementation would check timestamps or sequence numbers
        # stored in each block
        pass
```


### Accessing Flash Via ioctl Commands

The flash device supports various 'ioctl' operations:

```python
import machine

flash = machine.Flash()

# Common ioctl commands:
# 4 - Get block count
# 5 - Get block size  
# 6 - Erase block

block_count = flash.ioctl(4, 0)
block_size = flash.ioctl(5, 0)

print(f"Flash has {block_count} blocks of {block_size} bytes")
print(f"Total flash size: {block_count * block_size / 1024 / 1024:.2f} MB")

# Erase a specific block (DANGEROUS!)
# flash.ioctl(6, block_number)  # Uncomment to actually erase
```


### Safety Tips

1. *Never write to blocks 0-255* - This is where MicroPython firmware lives
2. *Avoid the filesystem area* - Check where littlefs is located
3. *Always erase before writing* - Flash can't flip bits from 0→1 without erasing
4. *Keep backups* - Flash writes can fail, especially with power loss
5. *Use high block numbers* - Store custom data at the end of flash
6. *Test on a spare Pico* - Flash corruption can brick your device


### Debugging Flash Contents

```python
def dump_flash_block(block_num):
    """Dump contents of a flash block in hex"""
    flash = machine.Flash()
    data = bytearray(4096)
    flash.readblocks(block_num, data)
    
    # Print in hex format
    for i in range(0, len(data), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"{i:04x}: {hex_str:<48} {ascii_str}")

# Example usage
dump_flash_block(500)  # Dump block 500
```

This gives you full control over flash storage, but remember:
*One wrong write and you could corrupt your filesystem or firmware*.

