

> [!WARNING]
> *As these scripts may corrupt your SD card, please use a card which you can __spoil__ in worst case.*
> Usually reformatting the card after use of these scripts will be enough.
> Format the SD card for *MS-DOS FAT32* before attempting to use the script in the case of `SimpleVFS`.
> In the case of the file system which does not use FAT32 but writes directly its own,
> you might have to low-level format the card to be usefulm, the Hierarchical Virtual File System
> (`HierarchicalVFS`). One such low-level formatting which is usually good enough: "dd" on a Mac or Linux.
> Another tool can be found at the official SD Association website:
> [SD Memory Card Formatter](https://www.sdcard.org/downloads/formatter/).


## Custom File Systems on the Raspberry Pi Pico using SD card


### SimpleVFS

*Overview*:
`SimpleVFS` is a lightweight wrapper over a FAT filesystem, using a JSON metadata file
(`/sd/.vfs_metadata.json`) to track file attributes. It relies on the underlying FAT
system (via `uos.VfsFat`) for storage, adding a layer for permissions and stats.

*Features*:
- *Mount Point*: `/sd`, with files stored directly (flat structure).
- *Metadata*: JSON file stores permissions (`rw` or `r`), creation/modification times,
  and file sizes.
- *Operations*: Create, read, write, delete files; set permissions; list files; get stats
  (file count, sizes, disk space).
- *Permissions*: Enforces read/write access (e.g., prevents writing to read-only files).
- *Storage*: Files stored via FAT; metadata in `/sd/.vfs_metadata.json`.

*Example Usage Outcome* (from provided code):
- Creates `hello.txt` ("Hello World!", 12 bytes, `rw`) and `secret.txt` ("Top Secret",
  10 bytes, `r`).
- Lists files with metadata (name, size, permissions, creation time).
- Reads `hello.txt` successfully; fails to write to `secret.txt` (PermissionError).
- Stats: 2 files, 22 bytes used, total/free space depends on SD card.
- File system state: `/sd` contains `.vfs_metadata.json`, `hello.txt`, `secret.txt`.

*Strengths*:
- Simple, leverages FAT for reliability and compatibility.
- Adds permissions and metadata without complex block management.
- Easy to integrate with existing FAT-formatted SD cards.

*Limitations*:
- No directory support (flat structure).
- Centralized JSON metadata can be a bottleneck or corruption risk.
- Relies on FAT, limiting low-level control.

*Use Case*:
Ideal for simple projects needing basic file operations with permissions
on a FAT-formatted SD card, where directory hierarchies are unnecessary.


### HierarchicalVFS

*Overview*:
`HierarchicalVFS` is a custom file system that replaces FAT, managing blocks
directly on the SD card. It uses a superblock, bitmap, and directory blocks
to support a hierarchical structure with files and directories.

*Features*:
- *Block Size*: 512 bytes, 1000 total blocks.
- *Structure*: Superblock (metadata, magic `0x53465648` = "HVFS"), bitmap
  (block allocation), directory blocks (32-byte entries: type, name, block pointer),
  single-block files.
- *Operations*: Create/read files, create/list/navigate directories (`cd`,
  limited `..` support).
- *Metadata*: Stored in superblock (free blocks, root dir) and directory entries;
  no permissions.
- *Fixes*: Corrected magic number (`0x53465648`) and `free_blocks` decrement on allocation.

*Example Usage Outcome* (from provided code):
- Creates root files (`readme.txt`, 19 bytes) and directories (`documents`, `images`).
- In `documents`, creates `note.txt` (~27 bytes) and `todo.txt` (~40 bytes).
- Lists root (`readme.txt`, `documents`, `images`) and `documents` (`note.txt`, `todo.txt`).
- Reads `note.txt`; navigates to `documents` and back to root.
- Superblock: 992 free blocks (after 8 used: superblock, bitmap, root, 3 files, 2 dirs).

*Strengths*:
- Full control over block allocation, independent of FAT.
- Supports directories for hierarchical organization.
- Educational for understanding low-level file system design.

*Limitations*:
- Files limited to 512 bytes (single block).
- No permissions, delete, or rename operations.
- Limited path navigation (e.g., `..` resets to root).
- Overwrites FAT, requiring reformatting.

*Use Case*:
Still suited for educational purposes or project applications needing a lightweight,
hierarchical file system with direct block control, where FAT compatibility is not required.

## Comparison

| Feature              | SimpleVFS                         | HierarchicalVFS                     |
|----------------------|-----------------------------------|-------------------------------------|
| *Underlying System*  | FAT (via `uos.VfsFat`)            | Custom block-based                  |
| *Metadata*           | JSON file (`/sd/.vfs_metadata.json`) | Superblock, directory blocks     |
| *Hierarchy*          | Flat (no directories)             | Hierarchical (directories)          |
| *Permissions*        | Read/write enforcement            | None                                |
| *File Size Limit*    | Limited by FAT                    | 512 bytes (single block)            |
| *Operations*         | Create, read, write, delete, permissions, stats | Create, read, list, navigate dirs |
| *Complexity*         | Simpler, FAT-dependent            | Complex, low-level control          |
| *Disk Impact*        | Uses existing FAT                 | Overwrites FAT (reformat needed)    |

```
SimpleVFS:                HierarchicalVFS:
/sd                       /
├── .vfs_metadata.json   ├── readme.txt
├── hello.txt            ├── documents/
└── secret.txt           │   ├── note.txt
                         │   └── todo.txt
                         └── images/
```
`SimpleVFS` has a flat structure with metadata in a single JSON file, while `HierarchicalVFS`
supports nested directories with metadata distributed across superblock and directory blocks.


### Conclusion

- *SimpleVFS*: Best for simple, FAT-based applications needing permissions and minimal overhead.
  It's practical for quick file management on existing SD cards.

- *HierarchicalVFS*: Ideal for learning file system mechanics or projects requiring custom storage
  without FAT dependency, but limited by file size and features.

Both serve educational purposes for projects, with `SimpleVFS` being more user-friendly and
`HierarchicalVFS` offering deeper insight into block-based file systems.

