
> [!IMPORTANT]
> *The SD card you use for this example will have to be formatted with FAT in order to work.*

## SimpleVFS: A Metadata-Based Virtual File System Wrapper

The `SimpleVFS` class is a MicroPython module that provides a simplified interface for
managing files on an SD card mounted with a FAT filesystem. It wraps the standard `uos`
file operations, adding a metadata layer stored in a JSON file (`.vfs_metadata.json`)
to track file permissions, creation times, and sizes. Unlike a full custom filesystem,
it relies on the underlying FAT filesystem for storage, making it simpler but dependent
on the SD card's existing FAT setup.


*Features:*
- *Mount Point:* Defaults to `/sd`.
- *Metadata:* Stored in `/sd/.vfs_metadata.json`, tracking permissions (`rw` or `r`),
  creation time, size, and optional modification time.
- *Operations:* Create, read, write, delete files; list files; set permissions; get
  filesystem stats.
- *Permissions:* Basic `r` (read) and `w` (write) permissions enforced by the class.
- *Limitations:*
  - No directory support (flat structure under mount point).
  - Metadata is centralised in one JSON file, which could be a bottleneck.
  - Relies on FAT filesystem (no custom block management).
  - No error handling for JSON corruption or disk full conditions.

This simulates the example usage:
```python
simple_vfs = SimpleVFS("/sd")
simple_vfs.create_file("hello.txt", "Hello World!", "rw")
simple_vfs.create_file("secret.txt", "Top Secret", "r")
simple_vfs.list_files()
simple_vfs.read_file("hello.txt")
try:
    simple_vfs.write_file("secret.txt", "Modified")
except PermissionError as e:
    print("Permission denied:", e)
simple_vfs.get_stats()
```

> [!INFO]
> *Prerequisites:* The SD card is initialised and mounted as a FAT filesystem at `/sd`
> using `uos.VfsFat`, as shown in the example setup.

#### Init
- `__init__(mount_point="/sd")`: Sets mount point and metadata file path
  (`/sd/.vfs_metadata.json`). Loads metadata via `_load_metadata`.
- `_load_metadata`: Reads `.vfs_metadata.json` using `ujson.load`; returns
  empty dict if file doesn't exist.
- `_save_metadata`: Writes metadata to `.vfs_metadata.json` using `ujson.dump`.


#### File Operations
- `create_file(filename, data, permissions="rw")`: Writes data to `/sd/filename`,
  stores metadata (permissions, creation time, size).
- `read_file(filename)`: Checks read permission, reads file content from `/sd/filename`.
- `write_file(filename, data)`: Checks write permission, overwrites file, updates
  metadata (size, modified time).
- `delete_file(filename)`: Removes file and metadata entry.
- `set_permissions(filename, permissions)`: Updates permissions in metadata.

#### Metadata and Stats
- `list_files`: Returns list of dicts with file name, size, permissions, and creation time.
- `get_stats`: Reports number of files, total size (from metadata), and SD card's
  total/free space via `uos.statvfs`.



### Running the Example

The example creates two files, lists them, reads one, attempts a forbidden write, and
checks stats. Below is the simulated outcome on a FAT-formatted SD card.


#### File System State
After running the example, the SD card at `/sd` contains:
- `.vfs_metadata.json`: Metadata for all files.
- `hello.txt`: Contains "Hello World!".
- `secret.txt`: Contains "Top Secret".

```
/sd
├── .vfs_metadata.json  (JSON, tracks all files)
├── hello.txt           (Text, "Hello World!", rw)
└── secret.txt          (Text, "Top Secret", r-only)
```
This flat structure shows the mount point `/sd` with the metadata file and two example
files.


#### Metadata File Content
The `.vfs_metadata.json` file stores:
```json
{
  "hello.txt": {
    "permissions": "rw",
    "created": 1690710123,
    "size": 12
  },
  "secret.txt": {
    "permissions": "r",
    "created": 1690710124,
    "size": 10
  }
}
```
Timestamps are simplified as "epoch" (actual values depend on `utime.time()`).


#### Disk Layout
The FAT filesystem handles block allocation, but `SimpleVFS` adds a logical layer.
Assuming a 512-byte block size (typical for FAT):

```
+---------------------+
| SD Card (/sd)       |
| [FAT Metadata]      | (Managed by VfsFat)
| [Block: .vfs_meta]  | JSON metadata
| [Block: hello.txt]  | "Hello World!"
| [Block: secret.txt] | "Top Secret"
| [Free Blocks]       | Available space
+---------------------+
```
This abstracts the FAT filesystem's block structure, showing `SimpleVFS` files as
logical blocks. The exact block allocation depends on FAT, but as the illustration
shows the metadata file and user files coexisting with FAT's own metadata
(e.g., file allocation table).


#### Example Output
Simulating the example (assuming `utime.time()` starts at 1690710123):
- *Create Files*:
  - `Created file: hello.txt (12 bytes)`
  - `Created file: secret.txt (10 bytes)`
- *List Files*:
  ```python
  [
    {"ქ "name": "hello.txt", "size": 12, "permissions": "rw", "created": 1690710123},
    {"name": "secret.txt", "size": 10, "permissions": "r", "created": 1690710124}
  ]
  ```
- *Read File*:
  ```python
  b'Hello World!'
  ```
- *Write Attempt*:
  ```python
  Permission denied: No write permission for 'secret.txt'
  ```
- *Stats* (example, depends on SD card!):
  ```python
  {
    "files": 2,
    "used_by_vfs": 22,
    "total_space": 33554432,  # e.g., 32MB card
    "free_space": 33450000    # Approximate
  }
  ```

```
[User] --> [SimpleVFS]
   |          |
   |          v
   |    [Check Metadata]
   |          |
   |          v
   |    [Permissions OK?]
   |          |
   v          v
[Read/Write] [FAT File Ops]
   |          |
   v          v
[SD Card] <---+
```
This shows the `SimpleVFS` workflow: user requests go through metadata checks
(permissions, existence), then translate to FAT file operations via `uos`. It
shows the permission enforcement layer (e.g., denying write to `secret.txt`).


### Notes
- The simulation assumes a small SD card and typical FAT behaviour.
- Timestamps depend on the system clock (`utime.time()`).
- For projects, add error handling for JSON corruption and disk space checks.
