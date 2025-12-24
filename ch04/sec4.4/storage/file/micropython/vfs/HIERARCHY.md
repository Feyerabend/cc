
> [!CAUTION]
> *Formatting overwrites any existing FAT filesystem on the SD card.*

## HierarchicalVFS: A Simple Custom File System for SD Cards

The `HierarchicalVFS` replaces the standard FAT filesystem with a simple hierarchical
structure supporting basic operations: creating files and directories, reading files,
listing directories, and navigating (with limited `..` support; parent).

*Features and Limitations:*
- *Block Size:* 512 bytes (standard for SD cards).
- *Total Blocks:* Hardcoded to 1000.
- *Structure:* Superblock (metadata), block bitmap (allocation tracking), directories
  (blocks with entries), files (single-block, zero-padded).
- *Entry Format:* 32 bytes per directory entry: 1 byte (type: 1=file, 2=dir), 27 bytes
  (name, null-padded), 4 bytes (block pointer, little-endian).
- *Magic Number:* `0x53465648` (ASCII "HVFS" in little-endian).
- *Limitations:*
  - Files limited to 512 bytes (no multi-block support).
  - No delete, rename, or multi-level path resolution.
  - `cd ..` resets to root (no parent pointers).
  - Directory limited to 16 entries (512/32).


The simulation below runs the example usage:
```python
vfs = HierarchicalVFS(sd)
vfs.create_file("readme.txt", b"This is a test file")
vfs.create_dir("documents")
vfs.create_dir("images")
vfs.change_dir("documents")
vfs.create_file("note.txt", b"A note in documents folder")
vfs.create_file("todo.txt", b"1. Learn VFS\n2. Build filesystem\n3. Expand!")
vfs.change_dir("..")
```


### Disk Layout

The disk has 1000 blocks of 512 bytes each. After running the example:
- *Used Blocks:* 0-7 (superblock, bitmap, root dir, readme.txt, documents dir,
  images dir, note.txt, todo.txt).
- *Free Blocks:* 992 (1000 - 8), correctly tracked in superblock.

*ASCII Illustration of Storage* (each [] is a 512-byte block):
```
Block 0: [Superblock] - Metadata (magic, totals, root pointer)
Block 1: [Bitmap]    - Allocation bits (first byte: FF)
Block 2: [Root Dir]  - Entries: readme.txt (file@3), documents (dir@4), images (dir@5)
Block 3: [File Data] - readme.txt content
Block 4: [Dir Data]  - documents/ entries: note.txt (file@6), todo.txt (file@7)
Block 5: [Dir Data]  - images/ (empty)
Block 6: [File Data] - note.txt content
Block 7: [File Data] - todo.txt content39
Block 8-999: [Free]  - Unused (all zeros in simulation)
```

*Bitmap Details* (first byte, binary):
- After format: `00000111` (blocks 0-2 used).
- After example: `11111109` (0xFF, blocks 0-7 used).
- Rest: `00000000`.


### Directory Structure

Post-example directory tree:

```
/
├── readme.txt    (File, Block 3, ~19 bytes + padding)
├── documents/    (Dir, Block 4)
│   ├── note.txt  (File, Block 6, ~27 bytes + padding)
│   └── todo.txt  (File, Block 7, ~40 bytes + padding)
└── images/       (Dir, Block 5, Empty)
```

- Root (Block 2): 3 entries.
- documents/ (Block 4): 2 entries.
- images/ (Block 5): 0 entries.
- Paths: `get_current_path()` returns "/" or "/unknown".


### Block Contents

Hex dumps of key blocks. Only relevant portions shown; full 512 bytes mostly zeros after content.


#### Block 0: Superblock

Metadata: magic, total blocks (1000), free blocks (992), root dir block (2).

```
0000: 48 56 46 53 e8 03 00 00 e0 03 00 00 02 00 00 00  HVFS............
0010: 00 00 00 00 ... (zeros to end)
```
- Magic: `0x53465648` ("HVFS").
- Total: `0x000003e8` (1000).
- Free: `0x000003e0` (992, updated after 5 allocations).
- Root: `0x00000002`.

```
+----------------------+
| Superblock (Block 0) |
| Magic: 0x53465648    | 48 56 46 53 ("HVFS")
| Total Blocks:        | 00 00 03 e8 (1000)
| Free Blocks:         | 00 00 03 e0 (992)
| Root Dir Block:      | 00 00 00 02 (2)
| (Padding: 496 zeros) |
+----------------------+
```

#### Block 1: Bitmap

Tracks used blocks (1 bit/block, 512 bytes = 4096 bits, 1000 used).

```
0000: ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
0010: 00 00 00 00 ... (zeros to end)
```
- First byte `0xFF`: Blocks 0-7 used.
- Rest: Free.


#### Block 2: Root Directory

Entries (32 bytes): type, name (padded), block ptr.

```
0000: 01 72 65 61 64 6d 65 2e 74 78 74 00 00 00 00 00  .readme.txt.....
0010: 00 00 00 00 00 00 00 00 00 00 00 00 03 00 00 00  ................
0020: 02 64 6f 63 75 6d 65 6e 74 73 00 00 00 00 00 00  .documents......
0030: 00 00 00 00 00 00 00 00 00 00 00 00 04 00 00 00  ................
0040: 02 69 6d 61 67 65 73 00 00 00 00 00 00 00 00 00  .images.........
0050: 00 00 00 00 00 00 00 00 00 00 00 00 05 00 00 00  ................
0060: 00 00 00 00 ... (zeros to end)
```
- Entry 1: Type 1 (file), "readme.txt", Block 3.
- Entry 2: Type 2 (dir), "documents", Block 4.
- Entry 3: Type 2 (dir), "images", Block 5.
- Max 16 entries/dir.

```
+--------------------+
| Root Dir (Block 2) |
| Entry 0 (32 bytes) |
| 01                 | Type: File (1)
| 72 65 61 64 ..     | Name: "readme.txt" (27 bytes, padded)
| 03 00 00 00        | Block Ptr: 3
+--------------------+
| Entry 1 (32 bytes) |
| 02                 | Type: Dir (2)
| 64 6f 63 75 ..     | Name: "documents" (27 bytes, padded)
| 04 00 00 00        | Block Ptr: 4
+--------------------+
| Entry 2 (32 bytes) |
| 02                 | Type: Dir (2)
| 69 6d 61 67 ..     | Name: "images" (27 bytes, padded)
| 05 00 00 00        | Block Ptr: 5
+--------------------+
|  (13 empty slots)  |
|  ..                |
```

#### Block 3: readme.txt (File Data)

```
0000: 54 68 69 73 20 69 73 20 61 20 74 65 73 74 20 66  This is a test f
0010: 69 6c 65 00 00 00 00 00 00 00 00 00 00 00 00 00  ile.............
0020: 00 00 00 00 ... (zeros to end)
```
- Content: "This is a test file".

```
+----------------------------+
| File: readme.txt (Block 3) |
| 54 68 69 73 ..             | "This is a test file"
| 00                         | Null terminator
| (Padding: 493 zeros)       |
+----------------------------+
[Write Process]
1. Allocate block (e.g., 3)
2. Write data (truncate to 512 bytes)
3. Pad with zeros
4. Add dir entry (type 1, name, ptr)
```

#### Block 4: documents Directory

```
0000: 01 6e 6f 74 65 2e 74 78 74 00 00 00 00 00 00 00  .note.txt.......
0010: 00 00 00 00 00 00 00 00 00 00 00 00 06 00 00 00  ................
0020: 01 74 6f 64 6f 2e 74 78 74 00 00 00 00 00 00 00  .todo.txt.......
0030: 00 00 00 00 00 00 00 00 00 00 00 00 07 00 00 00  ................
0040: 00 00 00 00 ... (zeros to end)
```
- Entry 1: Type 1, "note.txt", Block 6.
- Entry 2: Type 1, "todo.txt", Block 7.


#### Block 5: images Directory

Empty (all zeros).

```
0000: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
0010: 00 00 00 00 ... (all zeros)
```


#### Block 6: note.txt (File Data)

```
0000: 41 20 6e 6f 74 65 20 69 6e 20 64 6f 63 75 6d 65  A note in docume
0010: 6e 74 73 20 66 6f 6c 64 65 72 00 00 00 00 00 00  nts folder......
0020: 00 00 00 00 ... (zeros to end)
```
- Content: "A note in documents folder".


#### Block 7: todo.txt (File Data)

```
0000: 31 2e 20 4c 65 61 72 6e 20 56 46 53 0a 32 2e 20  1. Learn VFS.2. 
0010: 42 75 69 6c 64 20 66 69 6c 65 73 79 73 74 65 6d  Build filesystem
0020: 0a 33 2e 20 45 78 70 61 6e 64 21 00 00 00 00 00  .3. Expand!.....
0030: 00 00 00 00 ... (zeros to end)
```
- Content: "1. Learn VFS\n2. Build filesystem\n3. Expand!".


### Code Walkthrough

### Init and Formatting
- `__init__`: Reads superblock; formats if invalid magic (`0x53465648`).
- `_format_disk`: Writes superblock (magic, 1000 blocks, 997 free, root@2),
  bitmap (0-2 used), empty root dir.

### Allocation
- `_allocate_block`: Finds free bit in bitmap, sets it, decrements `free_blocks`,
  updates superblock on disk, returns block number.

```
+--------------------+
| Bitmap (Block 1)   |
| Byte 0: 11111111   | Blocks 0-7 used (0xFF)
| Byte 1: 00000000   | Blocks 8-15 free
| ..                 |
| Byte 511: 00000000 | Blocks 4088-4095 free
+--------------------+
[Allocation Process]
1. Scan bitmap for 0 bit
2. Set bit to 1 (e.g., block 3 for readme.txt)
3. Update byte in block 1
4. Decrement free_blocks (superblock)
5. Write superblock back
```

### Directory Operations
- `_find_entry`: Scans dir block for name match (32-byte entries).
- `_add_dir_entry`: Writes entry to empty slot.
- `create_file/dir`: Allocates block, writes data/dir, adds entry.
- `list_dir`: Lists non-zero entries in dir block.

### File Operations
- `read_file`: Reads file block, returns content up to first \x00.

### Navigation
- `change_dir`: Sets `current_dir` to target block or root for "..".

## Example Output (Simulation)
- Root contents: `[{'name': 'readme.txt', 'type': 'FILE'}, {'name': 'documents', 'type': 'DIR'}, {'name': 'images', 'type': 'DIR'}]`
- Documents contents: `[{'name': 'note.txt', 'type': 'FILE'}, {'name': 'todo.txt', 'type': 'FILE'}]`
- Note content: `A note in documents folder`
- Back to root: Same as root contents.
- Superblock free_blocks: 992 (hex `0x03e0`).


NOTE/Project: For a more production oriented system,
add multi-block files, deletion, and full path resolution.

