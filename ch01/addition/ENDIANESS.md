
## Endianness: Little vs. Big Endian

Endianness refers to the order in which bytes are stored in memory when representing multi-byte
values such as integers and floating-point numbers. The two most common byte orderings are:

1. Big-endian: The most significant byte (MSB) is stored at the lowest memory address.
- Example: The 4-byte integer 0x12345678 (hexadecimal) is stored in memory as:

```plaintext
Address:   0   1   2   3
Value:    12  34  56  78
```

2. Little-endian: The least significant byte (LSB) is stored at the lowest memory address.
- Example: The 4-byte integer 0x12345678 is stored in memory as:

```plaintext
Address:   0   1   2   3
Value:    78  56  34  12
```


### Other Byte Orderings

- Middle-endian (Mixed-endian): Some architectures (rare today) use an unconventional mix of big
  and little-endian order. One example is PDP-11's 16-bit words where 32-bit values were stored
  as [byte1 byte0 byte3 byte2].

- Bi-endian: Some modern processors (like ARM and PowerPC) support switching between big and
  little-endian modes.



### Uses

1. Cross-Platform Compatibility: Ensuring data is stored in a consistent format when working between different architectures.
2. Networking: Always use network byte order (big-endian) when transmitting data between systems.
3. File Formats: Some formats specify endianness (e.g., WAV is little-endian, JPEG may use big-endian).



### Endianness in Python

Since different systems may use different endianness, handling conversions is essential when working
with binary data, file formats, and network protocols.

#### Detecting System Endianness

Python provides a way to check the system's native byte order:

```python
import sys
print(f"System endianness: {sys.byteorder}")  # 'little' or 'big'
```

#### Converting Between Endianness

Python's `struct` module is useful for handling binary data and converting between byte orderings.

```python
import struct

# Pack an integer in little-endian and big-endian format
num = 0x12345678
little_endian = struct.pack('<I', num)  # '<' for little-endian, 'I' for unsigned int
big_endian = struct.pack('>I', num)     # '>' for big-endian

print("Little-endian:", little_endian.hex())  # Outputs: '78563412'
print("Big-endian:", big_endian.hex())        # Outputs: '12345678'
```

#### Converting Endianness of Binary Data

If you receive data in an unexpected format, you can swap it:

```python
# Unpack from little-endian and convert to big-endian
num_from_little = struct.unpack('<I', little_endian)[0]
big_endian_again = struct.pack('>I', num_from_little)

print("Converted back to big-endian:", big_endian_again.hex())  # '12345678'
```

#### Using int.from_bytes() and to_bytes()

These methods provide another way to convert integers to byte sequences and vice versa.

```python
num = 0x12345678

# Convert to bytes (little-endian)
little_bytes = num.to_bytes(4, byteorder='little')
big_bytes = num.to_bytes(4, byteorder='big')

print("Little-endian:", little_bytes.hex())  # '78563412'
print("Big-endian:", big_bytes.hex())        # '12345678'

# Convert back to integer
num_from_little = int.from_bytes(little_bytes, byteorder='little')
num_from_big = int.from_bytes(big_bytes, byteorder='big')

print(f"Restored number (little-endian): {hex(num_from_little)}")  # 0x12345678
print(f"Restored number (big-endian): {hex(num_from_big)}")        # 0x12345678
```



### Endianness in C

#### Detecting Endianness in C

To check whether a system is little-endian or big-endian, we can use a union or bitwise operations:

```c
#include <stdio.h>

int main() {
    unsigned int x = 0x12345678;
    unsigned char *c = (unsigned char*)&x;

    if (*c == 0x78) {
        printf("System is Little-Endian\n");
    } else {
        printf("System is Big-Endian\n");
    }
    
    return 0;
}
```

Here, we interpret an integer's memory as a byte array and check which byte appears first.



#### Converting Between Endianness in C

If you need to swap endianness, you can manually swap bytes:

```c
#include <stdio.h>

unsigned int swap_endian(unsigned int num) {
    return ((num >> 24) & 0xFF) |      // Move byte 3 to byte 0
           ((num >> 8) & 0xFF00) |     // Move byte 2 to byte 1
           ((num << 8) & 0xFF0000) |   // Move byte 1 to byte 2
           ((num << 24) & 0xFF000000); // Move byte 0 to byte 3
}

int main() {
    unsigned int num = 0x12345678;
    printf("Original: 0x%X\n", num);
    
    unsigned int swapped = swap_endian(num);
    printf("Swapped: 0x%X\n", swapped);
    
    return 0;
}
```

This function manually swaps the bytes in a 32-bit integer.


#### Using Standard Library Functions for Endianness Handling

Many systems provide built-in functions for swapping endianness:

```c
#include <stdio.h>
#include <arpa/inet.h>  // For htonl and ntohl (network byte order conversion)

int main() {
    unsigned int num = 0x12345678;
    
    unsigned int network_order = htonl(num);  // Convert to network (big-endian)
    unsigned int host_order = ntohl(network_order); // Convert back to host format
    
    printf("Original: 0x%X\n", num);
    printf("Network byte order: 0x%X\n", network_order);
    printf("Converted back to host order: 0x%X\n", host_order);
    
    return 0;
}
```

- `htonl()` (Host to Network Long) converts a 32-bit integer to big-endian.
- `ntohl()` (Network to Host Long) converts a 32-bit integer from big-endian to host order.

These are useful when sending binary data across a network, as network protocols typically use big-endian.


#### Memory Representation of Multi-Byte Values

To visualise how numbers are stored in memory:

```c
#include <stdio.h>

void print_bytes(void *ptr, size_t size) {
    unsigned char *bytes = (unsigned char*)ptr;
    for (size_t i = 0; i < size; i++) {
        printf("%02X ", bytes[i]);
    }
    printf("\n");
}

int main() {
    unsigned int num = 0x12345678;
    printf("Memory representation: ");
    print_bytes(&num, sizeof(num));

    return 0;
}
```

On a little-endian machine, this will print:

```plaintext
Memory representation: 78 56 34 12
```

On a big-endian machine, it will print:

```plaintext
Memory representation: 12 34 56 78
```

