
## Storage: Files and Databases

Storage in computing refers to persisting data beyond volatile memory (like RAM).
It enables data to be saved, retrieved, and managed over time. Two primary forms
are *files* (unstructured or semi-structured data) and *databases* (structured
data with querying capabilities).

- *What*: Files are basic units for storing arbitrary data (text, images, executables).
  Databases are organised collections of data, often optimised for efficient access,
  updates, and relationships.
- *How*: At a hardware level, storage devices (e.g., HDDs, SSDs, SD cards) divide space
  into fixed-size units called *sectors* (typically 512 bytes) or *blocks* (larger aggregates,
  like 4KB). Data is read/written in these units. File systems and database management
  systems (DBMS) handle organisation, allocation, and access.
- *Key Principles*:
  - *Blocking*: Data is grouped into blocks to minimise overhead. Fixed parts include
    headers (metadata like size, timestamps) and payloads (actual data).
  - *Organisation*: Uses indexes, tables, or trees to track locations. Fragmentation
    can occur when data is scattered across non-contiguous blocks.
  - *Access Methods*: Sequential (reading block-by-block) vs. random
    (direct jumps via addresses).

Also you might want to read some historical [notes](HISTORY.md), and
the specifics of Flash [memory](FLASH.md) for Raspberry Pi Pico in relation
to files, and file system.


### File Storage

#### What is a File?
A file is a named collection of data stored on a device. It can hold anything from plain
text to binary code. Files are managed by a *file system*, which acts as an abstraction
layer over raw storage.

#### How Files Work
- *Low-Level Structure*:
  - *Sectors and Blocks*: The smallest addressable unit is a sector (512 bytes on most disks).
    Files are allocated in *clusters* (groups of sectors, e.g., 4-32KB) to reduce management overhead.
  - *Fixed Parts*: Each file has metadata (inode in Unix-like systems or directory entries in FAT),
    including name, size, creation date, permissions, and pointers to data blocks.
- *Organisation*:
  - *File Allocation Table (FAT)*: Used in SD cards; a table maps file clusters.
    E.g., FAT32 chains clusters like a linked list.
  - *Other Systems*: NTFS (Windows) uses a Master File Table (MFT) with B-trees for faster lookups;
    ext4 (Linux) uses inodes and block groups.
  - *Directories*: Tree structures where directories are special files containing lists of file entries.
- *Operations*:
  - *Writing*: Allocate free blocks, update metadata, write data.
  - *Reading*: Follow pointers from metadata to blocks.
  - *Challenges*: Defragmentation fixes scattered blocks;
    wear-leveling (on flash like SD) distributes writes to prevent failures.

Files are versatile but lack built-in structure for complex queries, leading to databases for relational data.


### Database Storage

#### What is a Database?
A database is a structured repository for data, allowing efficient storage, retrieval, and manipulation.
Unlike files, databases enforce schemas and support queries (e.g., SQL).

#### Types of Databases
- *Relational (SQL)*: Data in tables with rows (records) and columns (fields). E.g., MySQL, SQLite.
- *NoSQL*: Flexible schemas; types include key-value (Redis), document (MongoDB), graph (Neo4j).
- *Embedded*: Lightweight like SQLite, stored as a single file.

#### How Databases Work
- *Low-Level Structure*:
  - *Pages/Blocks*: Databases divide storage into fixed-size pages (e.g., 4KB-8KB), similar to file blocks.
    Each page holds headers (type, checksum) and data.
  - *Fixed Parts*: Metadata includes system catalogs (table definitions), transaction logs
    (for durability), and indexes.
- *Organisation*:
  - *Tables*: Rows stored in heap files or clustered indexes.
    B-trees or hash tables index keys for fast lookups.
  - *Records*: Fixed or variable length; fields packed with offsets.
    E.g., in SQLite, a database is a single file with a B-tree for each table/index.
  - *Storage Engines*: InnoDB (MySQL) uses row-level locking and MVCC (multi-version
    concurrency control); others use append-only logs.
- *Operations*:
  - *Writing*: Insert into pages, update indexes, log changes (WAL - Write-Ahead Logging for crash recovery).
  - *Reading*: Query optimiser scans or uses indexes to fetch blocks.
  - *Challenges*: Vacuuming cleans unused space; sharding distributes data across nodes.

Databases build on file storage--most use underlying files--but
add layers for integrity (ACID properties) and performance.


![Pico W / SD Card](./../../assets/image/storage/store.png)
