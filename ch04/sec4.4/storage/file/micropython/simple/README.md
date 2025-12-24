
## SimpleVFS for MicroPython SD Card

`SimpleVFS` is a lightweight virtual file system (VFS) for MicroPython, designed to manage
files on an SD card with a FAT filesystem. It provides a simple interface for creating, reading,
writing, and deleting files, with basic permission controls (read/write)
stored in a JSON metadata file.


### What

The `vfs.py` script enables file management on an SD card connected to a MicroPython board
(Pico or ESP32, for exampe). Key features:
- Create files with custom permissions (`rw` or `r`).
- Read and write files, enforcing permissions.
- List files with metadata (size, permissions, creation time).
- Delete files and update metadata.
- Provide filesystem stats (e.g., total/free space).
- Run multiple times without errors, overwriting existing files.


### How
- *Setup*: Initialises an SD card via SPI and mounts it as a FAT filesystem using `uos.VfsFat`.
- *File Operations*: Stores files on the SD card and tracks metadata (permissions, size, timestamps)
  in a `.vfs_metadata.json` file.
- *Permissions*: Enforces read/write permissions via metadata checks, using `OSError` for compatibility
  with MicroPython’s limited exception set.
- *Persistence*: Files and metadata persist on the SD card across runs, with file overwrites handled
  automatically.


## Use

1. *Hardware Setup*:
   - Connect an SD card to your MicroPython board via
     SPI (CS: Pin 1, SCK: Pin 2, MOSI: Pin 3, MISO: Pin 4).
   - Ensure the SD card is formatted as FAT.
   - Verify your MicroPython firmware includes `sdcard` and `ujson` modules.

2. *Running the Script*:
   - Copy `vfs.py` to your MicroPython device (e.g., via Thonny or rshell).
   - Run the script to:
     - Create `hello.txt` (read/write) and `secret.txt` (read-only).
     - List files with metadata.
     - Read `hello.txt`’s content.
     - Attempt to write to `secret.txt` (fails with permission error).
     - Display filesystem stats.
   - The script can be run multiple times, overwriting existing files.

3. *Example Output*:
   ```
   Created file: hello.txt (12 bytes)
   Created file: secret.txt (10 bytes)
   Files: [{'name': 'secret.txt', 'size': 10, 'permissions': 'r', 'created': <timestamp>}, {'name': 'hello.txt', 'size': 12, 'permissions': 'rw', 'created': <timestamp>}]
   Content: Hello World!
   Permission denied: No write permission for 'secret.txt'
   Stats: {'files': 2, 'used_by_vfs': 22, 'total_space': <total_bytes>, 'free_space': <free_bytes>}
   ```


### Important Notes
- *SD Card Format*: Requires a FAT-formatted SD card. Back up data before use, as existing files may be overwritten.
- *Limitations*: No directory support; permissions are metadata-based, not enforced by the underlying FAT filesystem.
- *Compatibility*: Designed for MicroPython’s minimal builds, using `OSError` for errors like permission denials.


### Troubleshooting
- *SD Card Errors*: If you see `OSError: [Errno 19] ENODEV` or `[Errno 5] EIO`, check wiring, SD card format,
  or power supply.
- *Module Not Found*: Ensure `sdcard` and `ujson` are in your firmware.
- *Other Errors*: Share the traceback with your board and MicroPython version for help.

