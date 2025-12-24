
> [!WARNING]
> After use of SD card: Low-level formatting of the card: https://www.sdcard.org/downloads/formatter/


## Hierarchical VFS for MicroPython SD Card

This project implements a simple Hierarchical Virtual File System (VFS) for MicroPython,
designed to manage files and directories on an SD card. Unlike the standard FAT filesystem,
this custom VFS provides a lightweight, hierarchical structure for organizing data, suitable
for embedded systems with limited resources.


### What

The `vfs.py` script creates a custom filesystem on an SD card connected to a
MicroPython-compatible board (even should work with ESP32). It supports:
- Creating files and directories.
- Reading file contents.
- Listing directory contents.
- Navigating directories (including a basic "parent" navigation).
- Persistent storage across runs, with error handling to skip existing files/directories.

The filesystem uses a superblock, block bitmap, and directory entries to manage
up to 1000 blocks (512 bytes each), with a simple structure for files and directories.


### How

- *Initialisation*: The script initializes the SD card via SPI and sets up the VFS.
  If no valid filesystem is detected, it formats the SD card!
- *File/Directory Management*: Files and directories are stored as entries (32 bytes
  each) in directory blocks, with a 27-byte name field and a block pointer.
- *Error Handling*: The script checks for existing files/directories and skips creation
  to allow multiple runs without errors.
- *Persistence*: The filesystem persists on the SD card until reformatted.


### Use

1. *Hardware Setup*:
   - Connect an SD card to your MicroPython board via
     SPI (CS: Pin 1, SCK: Pin 2, MOSI: Pin 3, MISO: Pin 4).
   - Ensure your MicroPython firmware includes the `sdcard` module.

2. *Running the Script*:
   - Copy `vfs.py` to your MicroPython device (e.g., via Thonny or rshell).
   - Run the script to:
     - Create a file (`readme.txt`) and directories (`documents`, `images`) in the root.
     - Create files (`note.txt`, `todo.txt`) in the `documents` directory.
     - List directories and read file contents.
   - The script can be run multiple times; it skips creating existing files/directories.

3. *Example Output*:
   ```
   Formatting Hierarchical VFS...
   Created file: readme.txt
   Created directory: documents
   Created directory: images
   Root contents: [{'name': 'readme.txt', 'type': 'FILE'}, {'name': 'documents', 'type': 'DIR'}, {'name': 'images', 'type': 'DIR'}]
   Changed to directory: documents
   Created file: note.txt
   Created file: todo.txt
   Documents contents: [{'name': 'note.txt', 'type': 'FILE'}, {'name': 'todo.txt', 'type': 'FILE'}]
   Note content: A note in documents folder
   Back to root: [{'name': 'readme.txt', 'type': 'FILE'}, {'name': 'documents', 'type': 'DIR'}, {'name': 'images', 'type': 'DIR'}]
   ```

   On subsequent runs, it skips existing items:
   ```
   Skipped creating file 'readme.txt': File 'readme.txt' already exists
   Skipped creating directory 'documents': Directory 'documents' already exists
   ...
   ```


### Important Notes
- *Data Loss Warning*: The first run may format the SD card, overwriting any existing FAT filesystem.
  Back up data before running, if you use the card for anything else!
- *Limitations*: Directory navigation (`..`) is basic and lacks full path tracking. The filesystem
  supports up to 1000 blocks (512 KB total). No "large" files.
- *Compatibility*: Tested for MicroPython environments with minimal builds (lacking some standard
  Python features like `ljust` or `FileExistsError`).

### Troubleshooting
- *SD Card Errors*: If you see `OSError: [Errno 5] EIO`, check wiring or SPI configuration.
- *Module Not Found*: Ensure the `sdcard` module is in your firmware.
- *Other Errors*: Share the traceback with your board and MicroPython version for assistance.

