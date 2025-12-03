
## Character Encodings

Not all encodings represent numbers--many are designed to encode characters or symbols
for communication across media and devices. Examples include *Morse code*, which uses short
and long pulses (dots and dashes) to encode letters for telegraphy; the *Baudot code*,
a 5-bit character set used in early teleprinters; and *Braille*, a tactile system where
raised dots encode letters and numbers for visually impaired readers. Each encoding
reflects the constraints and goals of its medium--compactness, tactile feel, transmission
timing, or mechanical limitations--and highlights the broader principle of representing
abstract information in physical form.

Thus character encodings are systems for representing text as numbers that computers can
process. Their evolution reflects the growing need to represent diverse languages and
symbols in digital systems. Below is a very concise history of some key encodings,
followed by examples of handling them in C and Python.


#### EBCDIC (Extended Binary Coded Decimal Interchange Code)

Developed by IBM in the 1960s for mainframe computers, EBCDIC was designed for punch-card
compatibility and used in IBM's System/360. It’s an 8-bit encoding with 256 possible characters,
primarily for English and some special characters, but it’s not standardized across systems,
leading to multiple variants.

- *Characteristics*: Non-contiguous alphabet (e.g., 'A' to 'I' are 0xC1 to 0xC9,
  but 'J' to 'R' are 0xD1 to 0xD9). Not widely used today outside legacy IBM systems.

- *Use Case*: Mainly in IBM mainframes and legacy applications.


#### ASCII (American Standard Code for Information Interchange)

Introduced in 1963, ASCII standardized a 7-bit encoding (128 characters) for English letters,
digits, punctuation, and control codes. It became the foundation for modern text encodings
due to its simplicity and interoperability.

- *7-bit ASCII*: Uses 7 bits, covering 0x00 to 0x7F (e.g., 'A' = 0x41, 'a' = 0x61).
  Sufficient for basic English and control characters.

- *8-bit ASCII (Extended ASCII)*: Uses the full 8 bits (256 characters), adding characters
  like accented letters or symbols (e.g., ISO-8859-1, also called Latin-1). Different 8-bit
  extensions exist, causing compatibility issues.

- *Impact*: ASCII became the de facto standard for early computing and is still a subset
  of most modern encodings.


#### Codepages

IBM introduced codepages in the 1980s to extend ASCII for international use, particularly
for DOS and Windows. A codepage is an 8-bit encoding mapping 256 code points to characters,
tailored for specific languages or regions (e.g., CP437 for US English, CP850 for Western Europe).

- *Characteristics*: Each codepage supports a specific set of characters, but switching
  codepages changes character interpretations, leading to issues in multilingual contexts.

- *Use Case*: Common in early PCs and IBM systems but largely replaced by Unicode.


#### Unicode

Introduced in 1991 to address the limitations of ASCII and codepages, Unicode aims to encode
all writing systems globally. It assigns a unique code point (e.g., U+0041 for 'A') to every
character, supporting over 1.4 million possible characters.

- *Encodings*: Unicode is implemented via encodings like UTF-8 (variable-length, 1–4 bytes,
  backward-compatible with ASCII), UTF-16, and UTF-32. UTF-8 dominates due to its efficiency
  and compatibility.
- *Impact*: Unicode is the modern standard, enabling consistent text representation across
  platforms and languages.


### Representing Character Encodings in Code

Below are examples in C and Python to demonstrate handling ASCII, EBCDIC, IBM codepages, and Unicode.

### C

C uses `char` (8-bit) or `wchar_t` (wide characters, typically 16 or 32 bits) for strings.
Libraries like `iconv` handle conversions between encodings.

__1. *ASCII String Manipulation*__

```c
#include <stdio.h>

int main() {
    char ascii_str[] = "Hello, ASCII!"; // 7-bit ASCII (0x00–0x7F)
    printf("ASCII string: %s\n", ascii_str);
    printf("First char code: %d ('%c')\n", ascii_str[0], ascii_str[0]); // H = 0x48
    return 0;
}
```

__2. *EBCDIC to ASCII Conversion (Simplified)*__

C doesn’t natively support EBCDIC, but you can simulate conversion with a lookup table or `iconv`.

```c
#include <stdio.h>
#include <iconv.h>
#include <string.h>

int main() {
    char ebcdic_str[] = "\xC8\x85\x93\x93\x96"; // EBCDIC "Hello"
    char ascii_out[10];
    iconv_t cd = iconv_open("ASCII", "EBCDIC-US");
    size_t inbytes = strlen(ebcdic_str), outbytes = sizeof(ascii_out);
    char *in = ebcdic_str, *out = ascii_out;
    iconv(cd, &in, &inbytes, &out, &outbytes);
    printf("Converted to ASCII: %s\n", ascii_out); // Prints "Hello"
    iconv_close(cd);
    return 0;
}
```

__3. *Unicode (UTF-8) Handling*__

```c
#include <stdio.h>
#include <wchar.h>
#include <locale.h>

int main() {
    setlocale(LC_ALL, "en_US.UTF-8"); // Enable UTF-8
    wchar_t unicode_str[] = L"Hello, 世界!"; // Wide string with Chinese characters
    wprintf(L"Unicode string: %ls\n", unicode_str);
    return 0;
}
```

### Python

Python 3 uses Unicode (UTF-8) by default for strings, making encoding handling
straightforward. Python 2 used ASCII by default, requiring explicit Unicode handling.

__1. *ASCII and 8-bit ASCII*__

```python
# ASCII string
ascii_str = "Hello, ASCII!"
print(ascii_str)
print(ord(ascii_str[0]))  # 72 (ASCII code for 'H')

# 8-bit ASCII (Latin-1)
latin1_str = "Café".encode("latin-1")
print(latin1_str)  # b'Caf\xe9'
print(latin1_str.decode("latin-1"))  # Café
```

__2. *EBCDIC (Using `decode`/`encode`)*__

Python supports EBCDIC via the `cp500` codec (IBM’s EBCDIC variant).

```python
ebcdic_str = b"\xC8\x85\x93\x93\x96"  # EBCDIC "Hello"
ascii_str = ebcdic_str.decode("cp500")
print(ascii_str)  # Hello
print(ascii_str.encode("cp500"))  # b'\xc8\x85\x93\x93\x96'
```

__3. *Unicode and UTF-8*__

```python
unicode_str = "Hello, 世界!"  # Unicode string (UTF-8 by default)
print(unicode_str)
print(unicode_str.encode("utf-8"))  # b'Hello, \xe4\xb8\x96\xe7\x95\x8c!'
print(unicode_str.encode("utf-16"))  # UTF-16 encoding
```

__4. *IBM Codepage (e.g., CP437)*__

```python
cp437_str = "Hello, ☺".encode("cp437")  # CP437 includes graphical characters
print(cp437_str)  # b'Hello, \x01'
print(cp437_str.decode("cp437"))  # Hello, ☺
```

__5. *Unicode Normalisation*__

Unicode allows multiple representations for the same character (e.g., "é" as a
single code point or as "e" + combining accent). Normalisation ensures consistency.

```python
import unicodedata

text = "Café"  # U+00E9 (single character)
composed = unicodedata.normalize("NFC", text)  # Composed form
decomposed = unicodedata.normalize("NFD", text)  # Decomposed form (e + combining accent)
print(composed == decomposed)  # True (visually same)
print(list(map(ord, composed)))  # [67, 97, 102, 233]
print(list(map(ord, decomposed)))  # [67, 97, 102, 101, 769]
```

### Summary

- *ASCII* is simple and universal but limited to English.
- *EBCDIC* is legacy, mainly for IBM mainframes, with complex conversion needs.
- *IBM Codepages* extended ASCII for regional use but caused compatibility issues.
- *Unicode* (via UTF-8) is the modern standard, supporting all languages.
- *C*: Use `char` for ASCII/EBCDIC, `wchar_t` for Unicode, and `iconv` for conversions.
- *Python*: Unicode is default; use `encode`/`decode` for specific encodings like `cp500` (EBCDIC) or `cp437`.
