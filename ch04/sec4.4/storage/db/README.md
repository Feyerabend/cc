
> [!WARNING]
> As these scripts may corrupt your SD card, please use a card which you can spoil in worst case.
> Usually reformatting the card after use of these scripts will be enough.
> Format the SD card for MS-DOS FAT32 before attempting to use the scripts. 



## SD Card and Raspberry Pi Pico Integration

An *SD card* (Secure Digital card) is a non-volatile flash memory card widely used
for portable storage in devices like cameras, phones, and microcontrollers. It provides
high-capacity, reliable storage in a compact form factor, typically interfaced via
the *SPI* (Serial Peripheral Interface) protocol in microcontroller applications
due to its simplicity and compatibility. SD cards support file systems like *FAT*
(File Allocation Table), enabling easy data management.

The *Raspberry Pi Pico* supports SPI communication, making it ideal for interfacing
with an SD card module to store and retrieve data, such as logs, sensor readings,
or configuration files. Using an SD card with the Pico extends its storage
capabilities beyond its limited onboard flash memory.

The provided code files (`osfile.py`, `sdcard.py`, `minidb.py`, and `sminidb.py`)
demonstrate how to use an SD card with the Raspberry Pi Pico using *MicroPython*,
a lightweight Python implementation for microcontrollers. Below is a detailed
explanation of the SD card integration, how the programs work, and their functionality.



### Hardware Setup for SD Card with Raspberry Pi Pico

To connect an SD card to the Raspberry Pi Pico, you typically use an *SD card module*
(e.g., a breakout board with a card slot) that communicates over SPI. The typical
pin connections are:

- *CS (Chip Select)*: Connected to a GPIO pin (e.g., Pin 1 in the code) to
  select the SD card for communication.
- *SCK (Serial Clock)*: Connected to the SPI clock pin (e.g., Pin 2).
- *MOSI (Master Out Slave In)*: Connected to the SPI MOSI pin (e.g., Pin 3).
- *MISO (Master In Slave Out)*: Connected to the SPI MISO pin (e.g., Pin 4).
- *VCC and GND*: Power (3.3V or 5V, depending on the module) and ground
  connections from the Pico.

The SD card module acts as an SPI slave, and the Pico acts as the SPI master,
controlling communication.



### Overview of the Provided Code Files

The four files collectively demonstrate how to initialize an SD card, mount a FAT
filesystem, perform file operations, and implement a simple database using the SD
card for persistent storage.

1. *osfile.py*: Demonstrates basic SD card initialization and filesystem operations
   using MicroPython's `uos` and `os` modules.
2. *sdcard.py*: A MicroPython driver for SD cards, providing low-level functions
   to initialise the card and read/write data blocks.
3. *minidb.py*: Implements a simple database (`MiniDB`) class that stores data
   as CSV files on the SD card, with operations like creating tables, inserting
   rows, and querying data.
4. *sminidb.py*: A slightly modified version of `minidb.py` with improved documentation
   and a different buffer flush strategy for better reliability.


### Detailed Explanation of Each File

#### 1. *osfile.py*: Basic SD Card and Filesystem Operations

*Purpose*: This file shows how to initialize an SD card, mount it as a FAT filesystem,
and perform basic file and directory operations using MicroPython’s `uos` and `os` modules.

*Key Components*:
- *SD Card Initialization*:
  - Configures the *SPI interface* (SPI0, 1 MHz, Pins 2, 3, 4 for SCK, MOSI, MISO)
    and sets the *CS pin* (Pin 1) high.
  - Initializes the SD card using the `sdcard.SDCard` class from `sdcard.py`.
  - Mounts the SD card as a FAT filesystem at `/sd` using `uos.VfsFat`.

- *File Operations*:
  - Lists files/directories with `os.listdir("/sd")`.
  - Checks file/directory existence with `os.stat("/sd/temp_log.csv")`.
  - Removes files with `os.remove("/sd/temp_log.csv")`.
  - Creates/removes directories with `os.mkdir("/sd/mydir")` and `os.rmdir("/sd/mydir")`.
  - Manages the current working directory with `os.getcwd()` and `os.chdir("/sd")`.
  - Renames/moves files with `os.rename("/sd/old.csv", "/sd/new.csv")`.
  - Retrieves filesystem info (total/used/free space) with `os.statvfs("/sd")`.

*How It Works*:
- The code initializes the SD card via SPI and mounts it to enable file operations.
- The `os` module provides a Python-like interface to interact with the filesystem,
  making it easy to manage files and directories on the SD card.
- This is a low-level utility script, useful for testing SD card connectivity and
  performing basic file operations.

*Use Case*:
- Setting up and testing SD card integration with the Pico.
- Performing simple file operations, such as logging sensor data to a
  file or reading configuration files.



#### 2. *sdcard.py*: MicroPython SD Card Driver

*Purpose*: This file is a MicroPython driver for SD cards, providing low-level functions
to initialise the card, read data blocks, and write data blocks over SPI.

*Key Components*:
- *Class `SDCard`*:
  - Initializes the SD card with an SPI interface and CS pin.
  - Supports different SD card versions (v1 for SDSC, v2 for SDHC/SDXC).
  - Calculates the card’s capacity (in 512-byte sectors) using the *CSD*
    (Card Specific Data) register.
  - Sets the block size to 512 bytes for compatibility with FAT filesystems.

- *Initialization (`init_card`)*:
  - Configures the SPI bus at a low speed (100 kHz) for initialization.
  - Sends *CMD0* to reset the card and checks for the idle state.
  - Uses *CMD8* to determine the card version (v1 or v2).
  - Initializes the card based on its version (v1 uses byte addressing,
    v2 uses block addressing).
  - Increases the SPI speed (e.g., to 1.32 MHz) after initialization.

- *Read/Write Operations*:
  - `readblocks(block_num, buf)`: Reads one or more 512-byte blocks from the SD
    card starting at `block_num` into the buffer `buf`.
  - `writeblocks(block_num, buf)`: Writes one or more 512-byte blocks from the
    buffer `buf` to the SD card starting at `block_num`.
  - Uses SPI commands like *CMD17* (single block read), *CMD18* (multiple block
    read), *CMD24* (single block write), and *CMD25* (multiple block write).

- *IO Control (`ioctl`)*:
  - Returns the number of blocks (`op=4`) or block size (`op=5`, always 512 bytes).

*How It Works*:
- The driver communicates with the SD card using SPI commands, handling
  low-level details like sending commands, reading responses, and managing data tokens.
- It abstracts the complexity of SD card protocols, allowing higher-level code
  (e.g., `osfile.py`, `minidb.py`) to treat the SD card as a block device.
- The driver is critical for mounting the SD card as a filesystem using `uos.VfsFat`.

*Use Case*:
- Provides the foundation for SD card operations in MicroPython.
- Used by `osfile.py`, `minidb.py`, and `sminidb.py` to access the SD card.



#### 3. *minidb.py*: Simple Database Implementation

*Purpose*: Implements a lightweight database (`MiniDB`) class that stores data
in CSV files on the SD card, supporting basic CRUD (Create, Read, Update, Delete) operations.

*Key Components*:
- *Class `MiniDB`*:
  - Initializes with a base directory (`/sd`) and a `flush_every` parameter
    to control when buffered data is written to the SD card.
  - Uses a dictionary (`self.buffers`) to cache rows in memory before writing to disk.

- *Methods*:
  - `create_table(name, fields)`: Creates a new CSV file with the specified fields as the header.
  - `insert(name, row)`: Adds a row to the in-memory buffer; flushes to disk if the buffer reaches `flush_every`.
  - `commit(name)`: Writes buffered rows to the CSV file and clears the buffer.
  - `all_rows(name)`: Reads all rows from a CSV file, yielding dictionaries with header-value pairs.
  - `select(name, where)`: Filters rows based on a dictionary of conditions (e.g., `{"temp": "22.5"}`).
  - `delete_table(name)`: Deletes the CSV file and its buffer.
  - `delete_rows(name, where)`: Removes rows matching the `where` condition by rewriting the CSV file.
  - `count(name, where)`: Counts rows, optionally filtered by conditions.

- *Example Usage*:
  - Creates a `temperature` table with fields `time` and `temp`.
  - Inserts rows like `[12345, 22.5]`.
  - Reads all rows or filters rows where `temp == 22.5`.

*How It Works*:
- The database stores data in CSV files (e.g., `/sd/temperature.csv`), with the first
  line as the header and subsequent lines as data rows.
- Rows are buffered in memory to reduce SD card writes, improving performance and reducing wear.
- The `select` and `delete_rows` methods parse CSV files line-by-line, converting rows
  to dictionaries for easy manipulation.
- The code relies on `sdcard.py` for SD card access and `uos`/`os` for file operations.

*Use Case*:
- Storing structured data, such as sensor logs (e.g., temperature readings) or configuration data, on the SD card.
- Suitable for simple IoT applications where a lightweight database is needed.



#### 4. *sminidb.py*: Enhanced Database Implementation

*Purpose*: A refined version of `minidb.py` with improved documentation and a
different buffer flush strategy, emphasizing reliability.

*Key Differences from `minidb.py`*:
- *Improved Documentation*: Methods have clearer docstrings, enhancing code
  readability and maintainability.
- *Buffer Flush Strategy*: Sets `flush_every=3` in the example, meaning data
  is written to the SD card after every three inserts, balancing performance and data safety.
- *Example Usage*: Includes additional operations like counting rows and deleting
  rows/tables, demonstrating more functionality.

*Key Components*:
- Identical to `minidb.py` in structure and functionality, with the same methods
  (`create_table`, `insert`, `commit`, etc.).
- Example code creates a `temperature` table, inserts three rows, commits the
  buffer, counts rows, deletes a specific row, and deletes the table.

*How It Works*:
- Operates the same way as `minidb.py`, but the example demonstrates a more
  complete workflow, including error handling and data management.
- The higher `flush_every` value reduces frequent SD card writes, which can
  extend the card’s lifespan but risks data loss if power is interrupted before a flush.

*Use Case*:
- Similar to `minidb.py`, but better suited for projects requiring clearer code
  documentation and controlled data flushing.
- Useful for applications where data integrity is balanced with performance
  (e.g., periodic sensor logging).



### How the Programs Work Together

The four files form a layered system for SD card integration with the Raspberry Pi Pico:

1. *Low-Level Layer (`sdcard.py`)*:
   - Provides the `SDCard` class to handle SPI communication and SD card initialization.
   - Abstracts SD card commands (e.g., CMD0, CMD17, CMD24) into block-level read/write operations.
   - Used by all other files to access the SD card.

2. *Filesystem Layer (`osfile.py`)*:
   - Initializes the SD card using `sdcard.py` and mounts it as a FAT filesystem.
   - Provides high-level file operations (e.g., `os.listdir`, `os.remove`) for direct filesystem access.
   - Serves as a utility for testing or performing simple file operations.

3. *Application Layer (`minidb.py`, `sminidb.py`)*:
   - Builds on `sdcard.py` and `osfile.py` to implement a simple database using CSV files.
   - Abstracts file operations into database-like functionality (create, insert, select, delete).
   - Suitable for structured data storage and retrieval in embedded applications.

*Workflow*:
- The Pico initializes the SD card via SPI (`sdcard.py`).
- The FAT filesystem is mounted (`osfile.py`, `minidb.py`, `sminidb.py`).
- The `MiniDB` class (`minidb.py` or `sminidb.py`) manages data in CSV
  files, buffering rows in memory and flushing to the SD card as needed.
- Applications can use `MiniDB` to log data (e.g., sensor readings) or query stored data.



### Practical Use Cases with Raspberry Pi Pico

1. *Data Logging*:
   - Use `minidb.py` or `sminidb.py` to log sensor data (e.g., temperature,
     humidity) to a `temperature.csv` file on the SD card.
   - Example: A weather station records temperature every minute, storing
     `[timestamp, temp]` rows.

2. *Configuration Storage*:
   - Store device settings in a CSV file, readable at startup to configure
     the Pico’s behavior.

3. *IoT Applications*:
   - Collect data from sensors and store it on the SD card for later retrieval
     or transfer to a computer.
   - Example: A soil moisture monitor logs data to the SD card, which is
     later analyzed on a PC.

4. *Testing and Debugging*:
   - Use `osfile.py` to verify SD card connectivity and perform basic file
     operations during development.



### How to Run the Programs

1. *Hardware Setup*:
   - Connect an SD card module to the Pico with the correct pin assignments
     (CS: Pin 1, SCK: Pin 2, MOSI: Pin 3, MISO: Pin 4).
   - Ensure the SD card is formatted with a FAT filesystem (FAT16 or FAT32).

2. *Software Setup*:
   - Install MicroPython on the Raspberry Pi Pico.
   - Copy `sdcard.py`, `osfile.py`, `minidb.py`, and/or `sminidb.py` to the
     Pico’s filesystem (e.g., using Thonny IDE).

3. *Running the Code*:
   - For `osfile.py`: Run the script to initialize the SD card and test file
     operations (e.g., `os.listdir("/sd")`).
   - For `minidb.py` or `sminidb.py`: Run the example code to create a table,
     insert rows, and query data. Modify the example to suit your application
     (e.g., log sensor data).
   - Ensure the SD card is properly inserted and mounted before running any code.

4. *Example Output* (from `sminidb.py`):
   ```plaintext
   Row count: 3
   {'time': '1', 'temp': '22.1'}
   {'time': '2', 'temp': '22.3'}
   {'time': '3', 'temp': '22.5'}
   Deleting one row: True
   Row count after delete: 2
   Deleting table: True
   ```



### Advantages and Limitations

*Advantages*:
- *High Storage Capacity*: SD cards provide gigabytes of storage,
  far exceeding the Pico’s onboard flash.
- *Portability*: Data stored on the SD card can be read by other
  devices (e.g., PCs).
- *Simple Interface*: The SPI protocol and MicroPython’s filesystem
  support make SD card integration straightforward.
- *Lightweight Database*: `MiniDB` provides a simple way to manage
  structured data without requiring a full database system.

*Limitations*:
- *Performance*: SD card writes are slower than onboard flash, and
  frequent writes can wear out the card.
- *Power Sensitivity*: Sudden power loss may result in data loss if
  buffered data isn’t flushed (mitigated by `commit` or lower `flush_every`
  in `sminidb.py`).
- *Error Handling*: The code assumes the SD card is present and properly
  formatted; robust applications should add more error checking.
- *SPI Pin Usage*: The SD card occupies several GPIO pins, which may
  limit other peripherals.



### Security Considerations

- *Basic Security*: The `sminidb.py` file claims "slightly better security" due to
  improved documentation and controlled buffer flushing, but neither `minidb.py` nor
  `sminidb.py` really implements robust security features (e.g., encryption or access control).

- *Potential Risks*:
  - Data on the SD card is stored in plain-text CSV files, vulnerable to unauthorized
    access if the card is removed.
  - No input validation ensures safe data handling, which could lead to errors or
    exploits if malformed data is provided.

- *Improvements*:
  - Add data encryption for sensitive information.
  - Validate inputs to prevent injection attacks (e.g., malicious CSV data).
  - Use checksums to detect file corruption.



### Conclusion

The provided code demonstrates a complete solution for using an SD card with the Raspberry
Pi Pico in MicroPython. The `sdcard.py` driver handles low-level SD card communication,
`osfile.py` enables basic filesystem operations, and `minidb.py`/`sminidb.py` provide a
simple database for structured data storage. These scripts are ideal for IoT projects, data
logging, or any application requiring persistent storage on the Pico. By understanding and
modifying these scripts, you can build robust applications tailored to your needs, such as
logging sensor data or managing device configurations.



### NOTE: Secondary Pico Storage

On the Pico, the internal flash is the same chip that stores both the firmware (MicroPython
itself) and the Python scripts you upload. The Pico port of MicroPython does not ship with
a built-in filesystem on the internal flash. Technically it is non-volatile secondary memory
(NOR flash, mapped into the RP2040’s address space).

- The flash is managed by the firmware and normally reserved for storing the MicroPython
  binary and your main.py / boot.py files.
- Writing directly to flash while the firmware is running risks corrupting MicroPython itself.
- The Pico’s RP2040 flash interface requires erasing in 4 KB sectors before rewriting,
  which complicates direct use.

Options if you really want to use internal flash:

1. Frozen modules: you can embed Python code into the firmware image itself when you
   build MicroPython from source. This is read-only storage.

2. flashbdev low-level driver: the MicroPython source tree contains a rp2 port driver
   (rp2_flash.c) that exposes the flash as a block device. You can, with some hacking,
   mount it as a filesystem (uos.VfsFat), but this isn’t enabled in the default builds.

3. Custom C code or SDK: if you are working in C with the Pico SDK, you can write to
   flash directly using pico/stdlib.h and the flash API, but you must handle erases
   and alignment carefully.

4. MicroPython alternatives: on ESP8266/ESP32 boards, MicroPython exposes the internal
   flash as a filesystem (/flash), but on Pico the maintainers chose not to, precisely
   because of the corruption risk.

So there is no safe high-level library call in standard MicroPython on the Pico to store arbitrary
files on the internal flash. That’s why SD cards are the recommended path if you want persistent
storage beyond your program itself.


#### Go further ..

The RPI Pico has a limited number of write cycles (around 100,000) for its original 2MB
of built-in flash memory , so it's not at all suitable for high-frequency data logging,
but it is good for storing persistent data like user preferences or calibration data. 

If you want to travel deeper into small databases and storages, see:
the https://github.com/littlefs-project.

