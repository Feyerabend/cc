
## History of Storage Technologies: Files and Databases


### Early Storage (1940s-1960s)

- *Punched Cards and Paper Tape (1940s-1950s)*:
  - Used in early computers like the IBM 701. Data was stored as physical holes in cards or tape, read sequentially.
  - Limitations: Slow, bulky, and prone to physical damage. No concept of dynamic file systems or databases.
- *Magnetic Tape (1950s)*:
  - Introduced for sequential storage, storing kilobytes of data on reels. Used in systems like UNIVAC.
  - Files were rudimentary, stored as sequential records with no random access. Early "databases" were manual indexes on tape.
- *Hard Disk Drives (1956)*:
  - IBM's RAMAC 305 introduced the first HDD, with 5MB across 50 24-inch platters. Data was organised in *sectors* (fixed-size blocks, ~100 bytes initially).
  - Enabled random access, laying the groundwork for modern file systems. Early files were simple data streams with minimal metadata.


### Rise of File Systems and Databases (1970s-1980s)

- *File Systems (1970s)*:
  - *FAT (1977)*: Microsoft’s File Allocation Table, developed for floppy disks, organised data into clusters (e.g., 4KB). A table tracked cluster chains, enabling file storage on portable media.
  - *Unix File Systems (1970s)*: Introduced inodes, hierarchical directories, and metadata (permissions, timestamps). Systems like UFS organised disks into block groups.
  - Files became named entities with metadata, stored in contiguous or linked blocks. This allowed flexible storage for text, binaries, and more.
- *Relational Databases (1970s-1980s)*:
  - Edgar Codd’s 1970 paper formalised relational databases, using tables with rows and columns. IBM’s System R (1974) and Oracle (1979) implemented SQL.
  - Databases stored data in files but added structure: *tables* held records, *indexes* (B-trees) enabled fast lookups, and *logs* ensured crash recovery.
  - Storage relied on underlying file systems, with data split into fixed-size *pages* (e.g., 4KB), similar to disk blocks.


### Modern Storage and Flash Era (1990s-2000s)

- *Advanced File Systems (1990s)*:
  - *NTFS (1993)*: Windows NT introduced the Master File Table (MFT) with B-trees for faster file access and recovery features.
  - *ext2/ext3 (1990s)*: Linux file systems improved inode-based storage, adding journaling for reliability.
  - File systems handled larger disks (GBs to TBs), with metadata for access control and fragmentation management.
- *Flash Storage (1990s-2000s)*:
  - *NAND Flash (1989)*: Enabled compact, non-volatile storage. SD cards (1999) adopted FAT32, storing data in 512-byte sectors with wear-leveling to extend lifespan.
  - SSDs (early 2000s) replaced HDDs in many applications, using flash with file systems like exFAT for larger files.
- *Embedded and NoSQL Databases (2000s)*:
  - *SQLite (2000)*: A lightweight, file-based relational database for embedded systems. Stored as a single file with B-tree structures for tables and indexes.
  - *NoSQL (2000s)*: Databases like MongoDB (2009) and Redis addressed unstructured data needs for web-scale applications. Stored data in files or memory, using formats like JSON or key-value pairs.
  - Storage engines (e.g., InnoDB for MySQL) optimised page layouts and caching for performance.


### Contemporary Storage (2010s-Present)

- *Cloud and Distributed Storage*:
  - Cloud platforms (e.g., AWS S3, 2006) abstract file storage into object stores, using distributed file systems. Databases like DynamoDB scale across nodes.
  - File systems like ZFS (2005) and Btrfs add features like snapshots and compression.
- *NVMe and Advanced Flash (2010s)*:
  - NVMe SSDs (2013) reduced latency, with block sizes like 4KB. SD cards evolved to UHS standards, supporting high-speed access for embedded devices like the Raspberry Pi Pico.
- *Modern Databases*:
  - Distributed databases (e.g., Cassandra, 2008) use log-structured storage for scalability. Embedded databases remain popular for IoT, storing data on SD cards or flash.
  - Techniques like *write-ahead logging (WAL)* and *sharding* ensure durability and scalability, building on block-based principles.


### Relevance to Embedded Systems

In devices like the Raspberry Pi Pico, SD cards use FAT32 for compatibility, with 512-byte sectors organised into clusters. The historical shift from tapes to flash enables compact, reliable storage for files and simple databases (e.g., SQLite). Understanding this evolution highlights why modern storage balances performance, durability, and simplicity.

