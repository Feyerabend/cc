"""
Native implementations of java.util classes.

Kept separate from native_registry.py so the C translation only needs
to add a new java_util.c file and a registration call — no core changes.
"""

import sys as _sys
import io as _io

from jvm_interpreter.native.native_registry import NativeObject
from jvm_interpreter.models.java_objects import JavaArray


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class JavaScanner(NativeObject):
    """
    java.util.Scanner — reads tokens/lines from stdin or a String source.

    Uses a character buffer (_buf) to match Java's Scanner semantics:
    nextLine() returns the remainder of the current line (after the last
    token read), which is "" when nextInt() consumed "42" from "42\\n".
    """

    def __init__(self):
        super().__init__("java.util.Scanner")
        self._source = _sys.stdin
        self._buf = ""   # unprocessed characters from source
        self._set_source(None)

    def _set_source(self, src):
        """Called from <init>.  src = None / InputStream → stdin; str → StringIO."""
        if isinstance(src, str):
            self._source = _io.StringIO(src)
        else:
            self._source = _sys.stdin
        self._buf = ""

    # --- internal ---

    def _refill(self):
        """Pull one more line from source into _buf."""
        chunk = self._source.readline()
        if chunk:
            self._buf += chunk

    def _skip_horiz_ws(self):
        """Skip spaces/tabs but NOT newlines (used before nextLine)."""
        i = 0
        while i < len(self._buf) and self._buf[i] in ' \t\r':
            i += 1
        self._buf = self._buf[i:]

    def _skip_all_ws(self):
        """Skip all whitespace including newlines (used before tokens)."""
        while True:
            stripped = self._buf.lstrip(' \t\r\n')
            if stripped:
                self._buf = stripped
                return
            self._refill()
            if not self._buf:
                return  # EOF

    def _read_token(self) -> str:
        self._skip_all_ws()
        if not self._buf:
            raise RuntimeError("NoSuchElementException")
        i = 0
        while i < len(self._buf) and self._buf[i] not in ' \t\r\n':
            i += 1
        if i == 0:
            self._refill()
            return self._read_token()
        tok = self._buf[:i]
        self._buf = self._buf[i:]
        return tok

    # --- public API ---

    def nextLine(self) -> str:
        """Consume everything up to (and including) the next newline."""
        while '\n' not in self._buf:
            chunk = self._source.readline()
            if not chunk:
                if self._buf:          # EOF with leftover — return it
                    result = self._buf
                    self._buf = ""
                    return result
                raise RuntimeError("NoSuchElementException")
            self._buf += chunk
        nl = self._buf.index('\n')
        result = self._buf[:nl]
        self._buf = self._buf[nl + 1:]
        return result

    def next(self) -> str:      return self._read_token()
    def nextInt(self) -> int:   return int(self._read_token())
    def nextLong(self) -> int:  return int(self._read_token())
    def nextDouble(self) -> float: return float(self._read_token())
    def nextFloat(self) -> float:  return float(self._read_token())

    def nextBoolean(self) -> bool:
        return self._read_token().lower() == "true"

    def hasNext(self) -> bool:
        self._skip_all_ws()
        if not self._buf:
            self._refill()
        return bool(self._buf.strip())

    def hasNextLine(self) -> bool:
        if self._buf:
            return True
        if hasattr(self._source, 'tell'):
            pos = self._source.tell()
            ch = self._source.read(1)
            if ch:
                self._source.seek(pos)
                return True
            return False
        return True  # stdin: always might have more

    def _peek_token(self):
        """Return (token, True) or (None, False) without consuming."""
        old = self._buf
        try:
            tok = self._read_token()
            self._buf = tok + self._buf  # restore: token back at front
            return tok, True
        except RuntimeError:             # EOF — restore original buf
            self._buf = old
            return None, False

    def hasNextInt(self) -> bool:
        tok, found = self._peek_token()
        if not found: return False
        try: int(tok);  return True
        except ValueError: return False

    def hasNextDouble(self) -> bool:
        tok, found = self._peek_token()
        if not found: return False
        try: float(tok); return True
        except ValueError: return False

    def useDelimiter(self, pattern: str) -> 'JavaScanner':
        return self  # whitespace delimiter always used

    def close(self): pass

    def toString(self) -> str: return "java.util.Scanner"


# ---------------------------------------------------------------------------
# Iterator
# ---------------------------------------------------------------------------

class JavaIterator(NativeObject):
    """Wraps a Python iterator as java.util.Iterator."""

    def __init__(self, it):
        super().__init__("java.util.Iterator")
        self._it = it
        self._pending = None
        self._has_next = False
        self._advance()

    def _advance(self):
        try:
            self._pending = next(self._it)
            self._has_next = True
        except StopIteration:
            self._pending = None
            self._has_next = False

    def hasNext(self) -> bool:
        return self._has_next

    def next(self):
        val = self._pending
        self._advance()
        return val

    def toString(self) -> str:
        return f"Iterator@{hex(id(self))}"


# ---------------------------------------------------------------------------
# Map.Entry
# ---------------------------------------------------------------------------

class JavaMapEntry(NativeObject):
    """java.util.Map$Entry"""

    def __init__(self, key, value):
        super().__init__("java.util.Map$Entry")
        self._key = key
        self._value = value

    def getKey(self):   return self._key
    def getValue(self): return self._value

    def setValue(self, value):
        old = self._value
        self._value = value
        return old

    def toString(self) -> str:
        return f"{self._key}={self._value}"


# ---------------------------------------------------------------------------
# ArrayList / LinkedList
# ---------------------------------------------------------------------------

class JavaArrayList(NativeObject):
    """java.util.ArrayList — backed by a Python list."""

    def __init__(self):
        super().__init__("java.util.ArrayList")
        self._data = []

    # --- mutators ---

    def add(self, *args):
        """add(E e) -> boolean  or  add(int index, E element) -> void"""
        if len(args) == 1:
            self._data.append(args[0])
            return True
        else:
            index, element = args[0], args[1]
            self._data.insert(index, element)
            return None

    def set(self, index: int, element):
        old = self._data[index]
        self._data[index] = element
        return old

    def remove(self, v):
        """remove(int index) -> E  or  remove(Object o) -> boolean"""
        if isinstance(v, int) and not isinstance(v, bool):
            return self._data.pop(v)
        try:
            self._data.remove(v)
            return True
        except ValueError:
            return False

    def clear(self):
        self._data.clear()

    def addAll(self, other) -> bool:
        if isinstance(other, JavaArrayList):
            self._data.extend(other._data)
        elif isinstance(other, JavaArray):
            self._data.extend(other.elements)
        return True

    def forEach(self, action):
        for x in list(self._data):  # copy so mutations during iteration don't crash
            action.invoke([x])

    def sort(self, comparator=None):
        if comparator is not None and hasattr(comparator, 'invoke'):
            import functools
            self._data.sort(
                key=functools.cmp_to_key(lambda a, b: comparator.invoke([a, b])))
        else:
            try: self._data.sort()
            except TypeError: pass

    def removeIf(self, pred) -> bool:
        before = len(self._data)
        self._data[:] = [x for x in self._data if not pred.invoke([x])]
        return len(self._data) != before

    def stream(self) -> 'JavaStream':
        return JavaStream(self._data)

    # --- accessors ---

    def get(self, index: int):
        return self._data[index]

    def size(self) -> int:
        return len(self._data)

    def isEmpty(self) -> bool:
        return len(self._data) == 0

    def contains(self, v) -> bool:
        return v in self._data

    def indexOf(self, v) -> int:
        try:
            return self._data.index(v)
        except ValueError:
            return -1

    def lastIndexOf(self, v) -> int:
        for i in range(len(self._data) - 1, -1, -1):
            if self._data[i] == v:
                return i
        return -1

    def subList(self, from_idx: int, to_idx: int) -> 'JavaArrayList':
        result = JavaArrayList()
        result._data = list(self._data[from_idx:to_idx])
        return result

    def toArray(self) -> JavaArray:
        arr = JavaArray("java.lang.Object", len(self._data))
        for i, v in enumerate(self._data):
            arr.elements[i] = v
        return arr

    def iterator(self) -> JavaIterator:
        return JavaIterator(iter(list(self._data)))

    def toString(self) -> str:
        parts = ("null" if x is None else str(x) for x in self._data)
        return "[" + ", ".join(parts) + "]"


class JavaLinkedList(JavaArrayList):
    """java.util.LinkedList — same Python backing, extra Deque methods."""

    def __init__(self):
        super().__init__()
        self.class_name = "java.util.LinkedList"

    def addFirst(self, e): self._data.insert(0, e)
    def addLast(self, e):  self._data.append(e)
    def removeFirst(self): return self._data.pop(0) if self._data else None
    def removeLast(self):  return self._data.pop()  if self._data else None
    def getFirst(self):    return self._data[0]  if self._data else None
    def getLast(self):     return self._data[-1] if self._data else None
    def peekFirst(self):   return self._data[0]  if self._data else None
    def peekLast(self):    return self._data[-1] if self._data else None
    def pollFirst(self):   return self._data.pop(0) if self._data else None
    def pollLast(self):    return self._data.pop()  if self._data else None
    def peek(self):        return self._data[0]  if self._data else None
    def poll(self):        return self._data.pop(0) if self._data else None
    def offer(self, e):    return self.add(e)
    def push(self, e):     self.addFirst(e)
    def pop(self):         return self.removeFirst()


# ---------------------------------------------------------------------------
# Stack
# ---------------------------------------------------------------------------

class JavaStack(NativeObject):
    """java.util.Stack"""

    def __init__(self):
        super().__init__("java.util.Stack")
        self._data = []

    def push(self, e):
        self._data.append(e)
        return e

    def pop(self):
        if not self._data:
            raise RuntimeError("EmptyStackException")
        return self._data.pop()

    def peek(self):
        if not self._data:
            raise RuntimeError("EmptyStackException")
        return self._data[-1]

    def isEmpty(self) -> bool: return len(self._data) == 0
    def size(self) -> int:     return len(self._data)

    def search(self, e) -> int:
        for i in range(len(self._data) - 1, -1, -1):
            if self._data[i] == e:
                return len(self._data) - i
        return -1

    def toString(self) -> str:
        return "[" + ", ".join(str(x) for x in self._data) + "]"


# ---------------------------------------------------------------------------
# HashSet
# ---------------------------------------------------------------------------

class JavaHashSet(NativeObject):
    """java.util.HashSet — backed by a Python set where possible."""

    def __init__(self):
        super().__init__("java.util.HashSet")
        self._data = []  # list so non-hashable Java objects work

    def _index_of(self, v):
        for i, x in enumerate(self._data):
            if x == v or x is v:
                return i
        return -1

    def add(self, v) -> bool:
        if self._index_of(v) >= 0:
            return False
        self._data.append(v)
        return True

    def contains(self, v) -> bool:
        return self._index_of(v) >= 0

    def remove(self, v) -> bool:
        i = self._index_of(v)
        if i >= 0:
            self._data.pop(i)
            return True
        return False

    def size(self) -> int:     return len(self._data)
    def isEmpty(self) -> bool: return len(self._data) == 0
    def clear(self):           self._data.clear()

    def iterator(self) -> JavaIterator:
        return JavaIterator(iter(list(self._data)))

    def toArray(self) -> JavaArray:
        arr = JavaArray("java.lang.Object", len(self._data))
        for i, v in enumerate(self._data):
            arr.elements[i] = v
        return arr

    def addAll(self, other) -> bool:
        if isinstance(other, JavaArrayList):
            for x in other._data: self.add(x)
        elif isinstance(other, JavaHashSet):
            for x in other._data: self.add(x)
        return True

    def stream(self) -> 'JavaStream':
        return JavaStream(self._data)

    def forEach(self, action):
        for x in list(self._data): action.invoke([x])

    def toString(self) -> str:
        return "{" + ", ".join(str(x) for x in self._data) + "}"


# ---------------------------------------------------------------------------
# TreeSet (sorted, backed by sorted list for simplicity)
# ---------------------------------------------------------------------------

class JavaTreeSet(NativeObject):
    """java.util.TreeSet — sorted set."""

    def __init__(self):
        super().__init__("java.util.TreeSet")
        self._data = []

    def add(self, v) -> bool:
        import bisect
        if v in self._data:
            return False
        try:
            bisect.insort(self._data, v)
        except TypeError:
            self._data.append(v)
        return True

    def contains(self, v) -> bool: return v in self._data
    def remove(self, v) -> bool:
        try:
            self._data.remove(v)
            return True
        except ValueError:
            return False

    def size(self) -> int:     return len(self._data)
    def isEmpty(self) -> bool: return len(self._data) == 0
    def clear(self):           self._data.clear()
    def first(self):           return self._data[0]  if self._data else None
    def last(self):            return self._data[-1] if self._data else None
    def iterator(self):        return JavaIterator(iter(list(self._data)))
    def stream(self)           -> 'JavaStream': return JavaStream(self._data)
    def forEach(self, action):
        for x in list(self._data): action.invoke([x])
    def toString(self) -> str: return "{" + ", ".join(str(x) for x in self._data) + "}"


# ---------------------------------------------------------------------------
# HashMap
# ---------------------------------------------------------------------------

class JavaHashMap(NativeObject):
    """java.util.HashMap — backed by a Python dict (keys by identity for objects)."""

    def __init__(self):
        super().__init__("java.util.HashMap")
        self._dict = {}       # hashable keys -> value
        self._obj_keys = []   # (key, value) pairs for non-hashable keys

    def _get_raw(self, key):
        try:
            if key in self._dict:
                return self._dict[key], True
        except TypeError:
            pass
        for k, v in self._obj_keys:
            if k is key or k == key:
                return v, True
        return None, False

    def put(self, key, value):
        old, found = self._get_raw(key)
        try:
            self._dict[key] = value
        except TypeError:
            for i, (k, v) in enumerate(self._obj_keys):
                if k is key or k == key:
                    self._obj_keys[i] = (key, value)
                    return old
            self._obj_keys.append((key, value))
        return old if found else None

    def get(self, key):
        val, found = self._get_raw(key)
        return val if found else None

    def containsKey(self, key) -> bool:
        _, found = self._get_raw(key)
        return found

    def containsValue(self, value) -> bool:
        if value in self._dict.values():
            return True
        return any(v == value for _, v in self._obj_keys)

    def remove(self, key):
        old, found = self._get_raw(key)
        if not found:
            return None
        try:
            del self._dict[key]
        except (KeyError, TypeError):
            self._obj_keys = [(k, v) for k, v in self._obj_keys
                              if not (k is key or k == key)]
        return old

    def size(self) -> int:
        return len(self._dict) + len(self._obj_keys)

    def isEmpty(self) -> bool:
        return self.size() == 0

    def clear(self):
        self._dict.clear()
        self._obj_keys.clear()

    def getOrDefault(self, key, default):
        val, found = self._get_raw(key)
        return val if found else default

    def putIfAbsent(self, key, value):
        val, found = self._get_raw(key)
        if not found:
            self.put(key, value)
            return None
        return val

    def keySet(self) -> JavaHashSet:
        s = JavaHashSet()
        s._data = list(self._dict.keys()) + [k for k, _ in self._obj_keys]
        return s

    def values(self) -> JavaArrayList:
        lst = JavaArrayList()
        lst._data = list(self._dict.values()) + [v for _, v in self._obj_keys]
        return lst

    def entrySet(self) -> JavaArrayList:
        entries = JavaArrayList()
        for k, v in self._dict.items():
            entries._data.append(JavaMapEntry(k, v))
        for k, v in self._obj_keys:
            entries._data.append(JavaMapEntry(k, v))
        return entries

    def forEach(self, action):
        """BiConsumer — called for each (key, value) pair."""
        for k, v in list(self._dict.items()):
            action.invoke([k, v])
        for k, v in list(self._obj_keys):
            action.invoke([k, v])

    def toString(self) -> str:
        pairs = [f"{k}={v}" for k, v in self._dict.items()]
        pairs += [f"{k}={v}" for k, v in self._obj_keys]
        return "{" + ", ".join(pairs) + "}"


# ---------------------------------------------------------------------------
# TreeMap (sorted keys)
# ---------------------------------------------------------------------------

class JavaTreeMap(NativeObject):
    """java.util.TreeMap — sorted map, keys must be comparable."""

    def __init__(self):
        super().__init__("java.util.TreeMap")
        self._keys = []
        self._vals = {}

    def put(self, key, value):
        import bisect
        old = self._vals.get(key)
        if key not in self._vals:
            try:
                bisect.insort(self._keys, key)
            except TypeError:
                self._keys.append(key)
        self._vals[key] = value
        return old

    def get(self, key): return self._vals.get(key)
    def containsKey(self, key) -> bool: return key in self._vals
    def remove(self, key):
        if key in self._vals:
            self._keys.remove(key)
            return self._vals.pop(key)
        return None
    def size(self) -> int: return len(self._keys)
    def isEmpty(self) -> bool: return len(self._keys) == 0
    def clear(self): self._keys.clear(); self._vals.clear()
    def firstKey(self): return self._keys[0]  if self._keys else None
    def lastKey(self):  return self._keys[-1] if self._keys else None

    def keySet(self) -> JavaTreeSet:
        s = JavaTreeSet()
        s._data = list(self._keys)
        return s

    def values(self) -> JavaArrayList:
        lst = JavaArrayList()
        lst._data = [self._vals[k] for k in self._keys]
        return lst

    def entrySet(self) -> JavaArrayList:
        entries = JavaArrayList()
        for k in self._keys:
            entries._data.append(JavaMapEntry(k, self._vals[k]))
        return entries

    def toString(self) -> str:
        pairs = [f"{k}={self._vals[k]}" for k in self._keys]
        return "{" + ", ".join(pairs) + "}"


# ---------------------------------------------------------------------------
# Arrays (static utility)
# ---------------------------------------------------------------------------

class JavaArrays:

    @staticmethod
    def sort(arr: JavaArray, from_idx: int = None, to_idx: int = None):
        if from_idx is None:
            arr.elements.sort()
        else:
            sub = arr.elements[from_idx:to_idx]
            sub.sort()
            arr.elements[from_idx:to_idx] = sub

    @staticmethod
    def fill(arr: JavaArray, value):
        for i in range(arr.length):
            arr.elements[i] = value

    @staticmethod
    def copyOf(arr: JavaArray, new_length: int) -> JavaArray:
        result = JavaArray(arr.component_type, new_length)
        for i in range(min(arr.length, new_length)):
            result.elements[i] = arr.elements[i]
        return result

    @staticmethod
    def copyOfRange(arr: JavaArray, from_idx: int, to_idx: int) -> JavaArray:
        length = to_idx - from_idx
        result = JavaArray(arr.component_type, length)
        for i in range(length):
            result.elements[i] = arr.elements[from_idx + i] if from_idx + i < arr.length else None
        return result

    @staticmethod
    def equals(a: JavaArray, b: JavaArray) -> bool:
        return a.length == b.length and a.elements == b.elements

    @staticmethod
    def toString(arr: JavaArray) -> str:
        if arr is None:
            return "null"
        return "[" + ", ".join(str(x) for x in arr.elements) + "]"

    @staticmethod
    def asList(arr) -> JavaArrayList:
        lst = JavaArrayList()
        if isinstance(arr, JavaArray):
            lst._data = list(arr.elements)
        return lst

    @staticmethod
    def binarySearch(arr: JavaArray, key) -> int:
        import bisect
        try:
            i = bisect.bisect_left(arr.elements, key)
            if i < arr.length and arr.elements[i] == key:
                return i
        except TypeError:
            pass
        return -1


# ---------------------------------------------------------------------------
# Collections (static utility)
# ---------------------------------------------------------------------------

class JavaCollections:

    @staticmethod
    def sort(lst, comparator=None):
        if comparator is not None and hasattr(comparator, 'invoke'):
            import functools
            lst._data.sort(
                key=functools.cmp_to_key(lambda a, b: comparator.invoke([a, b])))
        else:
            try: lst._data.sort()
            except TypeError: pass

    @staticmethod
    def reverse(lst: JavaArrayList):
        lst._data.reverse()

    @staticmethod
    def shuffle(lst: JavaArrayList):
        import random
        random.shuffle(lst._data)

    @staticmethod
    def max(collection) -> object:
        data = collection._data if hasattr(collection, '_data') else []
        return max(data) if data else None

    @staticmethod
    def min(collection) -> object:
        data = collection._data if hasattr(collection, '_data') else []
        return min(data) if data else None

    @staticmethod
    def frequency(collection, obj) -> int:
        data = collection._data if hasattr(collection, '_data') else []
        return data.count(obj)

    @staticmethod
    def nCopies(n: int, obj) -> JavaArrayList:
        lst = JavaArrayList()
        lst._data = [obj] * n
        return lst

    @staticmethod
    def singletonList(obj) -> JavaArrayList:
        lst = JavaArrayList()
        lst._data = [obj]
        return lst

    @staticmethod
    def emptyList() -> JavaArrayList:
        return JavaArrayList()

    @staticmethod
    def emptyMap() -> JavaHashMap:
        return JavaHashMap()

    @staticmethod
    def emptySet() -> JavaHashSet:
        return JavaHashSet()

    @staticmethod
    def unmodifiableList(lst: JavaArrayList) -> JavaArrayList:
        return lst  # simplified — no enforcement

    @staticmethod
    def unmodifiableMap(m: JavaHashMap) -> JavaHashMap:
        return m

    @staticmethod
    def unmodifiableSet(s: JavaHashSet) -> JavaHashSet:
        return s

    @staticmethod
    def swap(lst: JavaArrayList, i: int, j: int):
        lst._data[i], lst._data[j] = lst._data[j], lst._data[i]

    @staticmethod
    def fill(lst: JavaArrayList, obj):
        for i in range(len(lst._data)):
            lst._data[i] = obj

    @staticmethod
    def disjoint(c1, c2) -> bool:
        d1 = c1._data if hasattr(c1, '_data') else []
        d2 = c2._data if hasattr(c2, '_data') else []
        for x in d1:
            for y in d2:
                try:
                    if x == y: return False
                except Exception:
                    if x is y: return False
        return True

    EMPTY_LIST = None  # set after class definition


JavaCollections.EMPTY_LIST = JavaArrayList()


# ---------------------------------------------------------------------------
# Comparator
# ---------------------------------------------------------------------------

class JavaComparator(NativeObject):
    """java.util.Comparator — wraps a Python compare function."""

    def __init__(self, compare_fn):
        super().__init__("java.util.Comparator")
        self._cmp = compare_fn

    def compare(self, a, b) -> int:
        return self._cmp(a, b)

    # Allow use as a JavaLambdaProxy equivalent (for stream.sorted etc.)
    def invoke(self, args: list) -> int:
        return self._cmp(args[0], args[1])

    def thenComparing(self, other: 'JavaComparator') -> 'JavaComparator':
        def cmp(a, b):
            r = self._cmp(a, b)
            return r if r != 0 else other.invoke([a, b])
        return JavaComparator(cmp)

    def reversed(self) -> 'JavaComparator':
        return JavaComparator(lambda a, b: -self._cmp(a, b))

    def toString(self) -> str:
        return "Comparator"

    @staticmethod
    def _extract(key_fn, x):
        return key_fn.invoke([x]) if hasattr(key_fn, 'invoke') else key_fn(x)

    @staticmethod
    def naturalOrder() -> 'JavaComparator':
        return JavaComparator(lambda a, b: 0 if a == b else (1 if a > b else -1))

    @staticmethod
    def reverseOrder() -> 'JavaComparator':
        return JavaComparator(lambda a, b: 0 if a == b else (-1 if a > b else 1))

    @staticmethod
    def comparing(key_fn) -> 'JavaComparator':
        def cmp(a, b):
            ka = JavaComparator._extract(key_fn, a)
            kb = JavaComparator._extract(key_fn, b)
            return 0 if ka == kb else (1 if ka > kb else -1)
        return JavaComparator(cmp)

    @staticmethod
    def comparingInt(key_fn) -> 'JavaComparator':
        return JavaComparator.comparing(key_fn)

    @staticmethod
    def comparingLong(key_fn) -> 'JavaComparator':
        return JavaComparator.comparing(key_fn)

    @staticmethod
    def comparingDouble(key_fn) -> 'JavaComparator':
        return JavaComparator.comparing(key_fn)


# ---------------------------------------------------------------------------
# Optional
# ---------------------------------------------------------------------------

class JavaOptional(NativeObject):
    """java.util.Optional."""

    def __init__(self, value=None, present: bool = False):
        super().__init__("java.util.Optional")
        self._value   = value
        self._present = present

    def isPresent(self) -> bool:  return self._present
    def isEmpty(self)   -> bool:  return not self._present

    def get(self):
        if not self._present:
            raise RuntimeError("NoSuchElementException: Optional.get on empty")
        return self._value

    def orElse(self, other):
        return self._value if self._present else other

    def orElseGet(self, supplier):
        return self._value if self._present else supplier.invoke([])

    def ifPresent(self, consumer):
        if self._present:
            consumer.invoke([self._value])

    def map(self, mapper) -> 'JavaOptional':
        if not self._present:
            return JavaOptional(None, False)
        v = mapper.invoke([self._value])
        return JavaOptional(v, v is not None)

    def filter(self, pred) -> 'JavaOptional':
        if not self._present or not pred.invoke([self._value]):
            return JavaOptional(None, False)
        return self

    def toString(self) -> str:
        return f"Optional[{self._value}]" if self._present else "Optional.empty"

    @staticmethod
    def of(value) -> 'JavaOptional':
        if value is None:
            raise RuntimeError("NullPointerException")
        return JavaOptional(value, True)

    @staticmethod
    def ofNullable(value) -> 'JavaOptional':
        return JavaOptional(value, value is not None)

    @staticmethod
    def empty() -> 'JavaOptional':
        return JavaOptional(None, False)


# ---------------------------------------------------------------------------
# Collectors / Collector
# ---------------------------------------------------------------------------

class JavaCollector(NativeObject):
    """java.util.stream.Collector — wraps a Python callable list→result."""

    def __init__(self, collect_fn):
        super().__init__("java.util.stream.Collector")
        self._collect_fn = collect_fn

    def collect(self, data: list):
        return self._collect_fn(data)


class JavaCollectors:
    """java.util.stream.Collectors — static factory methods."""

    @staticmethod
    def toList() -> JavaCollector:
        def collect(data):
            lst = JavaArrayList(); lst._data = list(data); return lst
        return JavaCollector(collect)

    @staticmethod
    def toUnmodifiableList() -> JavaCollector:
        return JavaCollectors.toList()

    @staticmethod
    def toSet() -> JavaCollector:
        def collect(data):
            s = JavaHashSet()
            for x in data: s.add(x)
            return s
        return JavaCollector(collect)

    @staticmethod
    def toUnmodifiableSet() -> JavaCollector:
        return JavaCollectors.toSet()

    @staticmethod
    def joining(delimiter: str = '', prefix: str = '', suffix: str = '') -> JavaCollector:
        def collect(data):
            joined = delimiter.join('' if x is None else str(x) for x in data)
            return prefix + joined + suffix
        return JavaCollector(collect)

    @staticmethod
    def counting() -> JavaCollector:
        return JavaCollector(lambda data: len(list(data)))

    @staticmethod
    def toMap(key_fn, val_fn, merge_fn=None) -> JavaCollector:
        def collect(data):
            m = JavaHashMap()
            for x in data:
                k = key_fn.invoke([x])
                v = val_fn.invoke([x])
                if merge_fn is not None and m.containsKey(k):
                    v = merge_fn.invoke([m.get(k), v])
                m.put(k, v)
            return m
        return JavaCollector(collect)

    @staticmethod
    def toUnmodifiableMap(key_fn, val_fn) -> JavaCollector:
        return JavaCollectors.toMap(key_fn, val_fn)

    @staticmethod
    def groupingBy(classifier, downstream=None) -> JavaCollector:
        def collect(data):
            m = JavaHashMap()
            for x in data:
                k = classifier.invoke([x])
                if not m.containsKey(k):
                    m.put(k, JavaArrayList())
                m.get(k).add(x)
            if downstream is not None:
                result = JavaHashMap()
                for e in m.entrySet()._data:
                    result.put(e.getKey(), downstream.collect(e.getValue()._data))
                return result
            return m
        return JavaCollector(collect)

    @staticmethod
    def partitioningBy(pred) -> JavaCollector:
        def collect(data):
            m = JavaHashMap()
            t = JavaArrayList(); f = JavaArrayList()
            for x in data:
                (t if pred.invoke([x]) else f).add(x)
            m.put(True, t); m.put(False, f)
            return m
        return JavaCollector(collect)

    @staticmethod
    def summingInt(fn) -> JavaCollector:
        return JavaCollector(lambda data: sum(fn.invoke([x]) for x in data))

    @staticmethod
    def summingLong(fn) -> JavaCollector:
        return JavaCollectors.summingInt(fn)

    @staticmethod
    def summingDouble(fn) -> JavaCollector:
        return JavaCollector(lambda data: float(sum(fn.invoke([x]) for x in data)))

    @staticmethod
    def averagingInt(fn) -> JavaCollector:
        def collect(data):
            lst = list(data)
            return sum(fn.invoke([x]) for x in lst) / len(lst) if lst else 0.0
        return JavaCollector(collect)

    @staticmethod
    def averagingDouble(fn) -> JavaCollector:
        return JavaCollectors.averagingInt(fn)

    @staticmethod
    def mapping(mapper, downstream) -> JavaCollector:
        def collect(data):
            return downstream.collect([mapper.invoke([x]) for x in data])
        return JavaCollector(collect)


# ---------------------------------------------------------------------------
# IntStream
# ---------------------------------------------------------------------------

class JavaIntStream(NativeObject):
    """java.util.stream.IntStream — materialized (non-lazy) for simplicity."""

    def __init__(self, data=None):
        super().__init__("java.util.stream.IntStream")
        self._data = list(data) if data is not None else []

    def filter(self, pred)   -> 'JavaIntStream':
        return JavaIntStream(x for x in self._data if pred.invoke([x]))

    def map(self, fn)        -> 'JavaIntStream':
        return JavaIntStream(fn.invoke([x]) for x in self._data)

    def mapToObj(self, fn)   -> 'JavaStream':
        return JavaStream(fn.invoke([x]) for x in self._data)

    def boxed(self)          -> 'JavaStream':
        return JavaStream(self._data)

    def forEach(self, action):
        for x in self._data: action.invoke([x])

    def sum(self)     -> int:   return sum(self._data)
    def count(self)   -> int:   return len(self._data)
    def average(self) -> JavaOptional:
        return (JavaOptional(sum(self._data) / len(self._data), True)
                if self._data else JavaOptional(None, False))
    def min(self) -> JavaOptional:
        return JavaOptional(min(self._data), True) if self._data else JavaOptional(None, False)
    def max(self) -> JavaOptional:
        return JavaOptional(max(self._data), True) if self._data else JavaOptional(None, False)
    def anyMatch(self, pred)  -> bool: return any(pred.invoke([x]) for x in self._data)
    def allMatch(self, pred)  -> bool: return all(pred.invoke([x]) for x in self._data)
    def noneMatch(self, pred) -> bool: return not any(pred.invoke([x]) for x in self._data)

    def sorted(self)  -> 'JavaIntStream':
        return JavaIntStream(sorted(self._data))
    def distinct(self) -> 'JavaIntStream':
        seen = []; r = []
        for x in self._data:
            if x not in seen: seen.append(x); r.append(x)
        return JavaIntStream(r)
    def limit(self, n: int)   -> 'JavaIntStream': return JavaIntStream(self._data[:n])
    def skip(self, n: int)    -> 'JavaIntStream': return JavaIntStream(self._data[n:])

    def reduce(self, *args):
        if len(args) == 2:
            acc = args[0]
            for x in self._data: acc = args[1].invoke([acc, x])
            return acc
        if not self._data: return JavaOptional(None, False)
        acc = self._data[0]
        for x in self._data[1:]: acc = args[0].invoke([acc, x])
        return JavaOptional(acc, True)

    def toArray(self):
        arr = JavaArray('int', len(self._data))
        for i, x in enumerate(self._data): arr.elements[i] = x
        return arr

    def collect(self, supplier, accumulator, combiner=None):
        container = supplier.invoke([])
        for x in self._data: accumulator.invoke([container, x])
        return container

    def findFirst(self) -> JavaOptional:
        return JavaOptional(self._data[0], True) if self._data else JavaOptional(None, False)

    def toString(self) -> str: return "IntStream"

    @staticmethod
    def range(start: int, end: int) -> 'JavaIntStream':
        return JavaIntStream(range(start, end))

    @staticmethod
    def rangeClosed(start: int, end: int) -> 'JavaIntStream':
        return JavaIntStream(range(start, end + 1))

    @staticmethod
    def of(*args) -> 'JavaIntStream':
        if len(args) == 1 and isinstance(args[0], JavaArray):
            return JavaIntStream(args[0].elements)
        return JavaIntStream(args)

    @staticmethod
    def concat(a: 'JavaIntStream', b: 'JavaIntStream') -> 'JavaIntStream':
        return JavaIntStream(a._data + b._data)


# ---------------------------------------------------------------------------
# Stream
# ---------------------------------------------------------------------------

class JavaStream(NativeObject):
    """java.util.stream.Stream — lazy pipeline via a list of (op, arg) stages."""

    def __init__(self, source=None):
        super().__init__("java.util.stream.Stream")
        if isinstance(source, JavaArrayList):
            self._source = list(source._data)
        elif source is not None:
            self._source = list(source)
        else:
            self._source = []
        self._ops: list = []

    def _chain(self, op, arg) -> 'JavaStream':
        s = JavaStream.__new__(JavaStream)
        NativeObject.__init__(s, "java.util.stream.Stream")
        s._source = self._source
        s._ops    = self._ops + [(op, arg)]
        return s

    def map(self, fn)         -> 'JavaStream': return self._chain('map', fn)
    def filter(self, pred)    -> 'JavaStream': return self._chain('filter', pred)
    def peek(self, action)    -> 'JavaStream': return self._chain('peek', action)
    def sorted(self, cmp=None)-> 'JavaStream': return self._chain('sorted', cmp)
    def distinct(self)        -> 'JavaStream': return self._chain('distinct', None)
    def limit(self, n: int)   -> 'JavaStream': return self._chain('limit', n)
    def skip(self, n: int)    -> 'JavaStream': return self._chain('skip', n)

    def flatMap(self, fn) -> 'JavaStream':
        result = []
        for x in self._evaluate():
            inner = fn.invoke([x])
            if isinstance(inner, JavaStream):
                result.extend(inner._evaluate())
            elif isinstance(inner, JavaArrayList):
                result.extend(inner._data)
            elif inner is not None:
                result.append(inner)
        return JavaStream(result)

    def mapToInt(self, fn) -> JavaIntStream:
        return JavaIntStream(fn.invoke([x]) for x in self._evaluate())

    def mapToLong(self, fn) -> JavaIntStream:
        return JavaIntStream(fn.invoke([x]) for x in self._evaluate())

    def mapToDouble(self, fn) -> JavaIntStream:
        return JavaIntStream(fn.invoke([x]) for x in self._evaluate())

    def _evaluate(self) -> list:
        import functools
        data = list(self._source)
        for op, arg in self._ops:
            if   op == 'map':      data = [arg.invoke([x]) for x in data]
            elif op == 'filter':   data = [x for x in data if arg.invoke([x])]
            elif op == 'peek':
                for x in data: arg.invoke([x])
            elif op == 'distinct':
                seen = []; r = []
                for x in data:
                    if x not in seen: seen.append(x); r.append(x)
                data = r
            elif op == 'limit':    data = data[:arg]
            elif op == 'skip':     data = data[arg:]
            elif op == 'sorted':
                if arg is None:
                    try: data.sort()
                    except TypeError: pass
                else:
                    data.sort(key=functools.cmp_to_key(lambda a, b: arg.invoke([a, b])))
        return data

    def forEach(self, action):
        for x in self._evaluate(): action.invoke([x])

    def collect(self, collector: JavaCollector):
        return collector.collect(self._evaluate())

    def count(self) -> int: return len(self._evaluate())

    def findFirst(self) -> JavaOptional:
        data = self._evaluate()
        return JavaOptional(data[0], True) if data else JavaOptional(None, False)

    def findAny(self) -> JavaOptional:
        return self.findFirst()

    def anyMatch(self,  pred) -> bool: return any(pred.invoke([x]) for x in self._evaluate())
    def allMatch(self,  pred) -> bool: return all(pred.invoke([x]) for x in self._evaluate())
    def noneMatch(self, pred) -> bool: return not any(pred.invoke([x]) for x in self._evaluate())

    def reduce(self, *args):
        data = self._evaluate()
        if len(args) == 2:
            acc = args[0]
            for x in data: acc = args[1].invoke([acc, x])
            return acc
        if not data: return JavaOptional(None, False)
        acc = data[0]
        for x in data[1:]: acc = args[0].invoke([acc, x])
        return JavaOptional(acc, True)

    def min(self, cmp) -> JavaOptional:
        import functools
        data = self._evaluate()
        if not data: return JavaOptional(None, False)
        return JavaOptional(
            min(data, key=functools.cmp_to_key(lambda a, b: cmp.invoke([a, b]))), True)

    def max(self, cmp) -> JavaOptional:
        import functools
        data = self._evaluate()
        if not data: return JavaOptional(None, False)
        return JavaOptional(
            max(data, key=functools.cmp_to_key(lambda a, b: cmp.invoke([a, b]))), True)

    def toArray(self):
        data = self._evaluate()
        arr = JavaArray('java.lang.Object', len(data))
        for i, x in enumerate(data): arr.elements[i] = x
        return arr

    def toString(self) -> str: return "Stream"

    @staticmethod
    def of(*args) -> 'JavaStream':
        if len(args) == 1 and isinstance(args[0], JavaArray):
            return JavaStream(args[0].elements)
        return JavaStream(args)

    @staticmethod
    def empty() -> 'JavaStream':
        return JavaStream([])

    @staticmethod
    def concat(a: 'JavaStream', b: 'JavaStream') -> 'JavaStream':
        return JavaStream(a._evaluate() + b._evaluate())


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_java_util(registry):
    """Register all java.util natives into the given NativeRegistry."""

    # ---- Iterator ----
    registry.register_method("java.util.Iterator", "hasNext",
                             lambda self: self.hasNext())
    registry.register_method("java.util.Iterator", "next",
                             lambda self: self.next())

    # ---- Map.Entry ----
    registry.register_method("java.util.Map$Entry", "getKey",
                             lambda self: self.getKey())
    registry.register_method("java.util.Map$Entry", "getValue",
                             lambda self: self.getValue())
    registry.register_method("java.util.Map$Entry", "setValue",
                             lambda self, v: self.setValue(v))
    registry.register_method("java.util.Map$Entry", "toString",
                             lambda self: self.toString())

    # ---- ArrayList ----
    registry.register_constructor("java.util.ArrayList", lambda: JavaArrayList())
    registry.register_method("java.util.ArrayList", "<init>",
                             lambda self, *a: None)
    registry.register_method("java.util.ArrayList", "add",
                             lambda self, *a: self.add(*a))
    registry.register_method("java.util.ArrayList", "get",
                             lambda self, i: self.get(i))
    registry.register_method("java.util.ArrayList", "set",
                             lambda self, i, e: self.set(i, e))
    registry.register_method("java.util.ArrayList", "remove",
                             lambda self, v: self.remove(v))
    registry.register_method("java.util.ArrayList", "size",
                             lambda self: self.size())
    registry.register_method("java.util.ArrayList", "isEmpty",
                             lambda self: self.isEmpty())
    registry.register_method("java.util.ArrayList", "contains",
                             lambda self, v: self.contains(v))
    registry.register_method("java.util.ArrayList", "indexOf",
                             lambda self, v: self.indexOf(v))
    registry.register_method("java.util.ArrayList", "lastIndexOf",
                             lambda self, v: self.lastIndexOf(v))
    registry.register_method("java.util.ArrayList", "clear",
                             lambda self: self.clear())
    registry.register_method("java.util.ArrayList", "addAll",
                             lambda self, c: self.addAll(c))
    registry.register_method("java.util.ArrayList", "sort",
                             lambda self, c=None: self.sort(c))
    registry.register_method("java.util.ArrayList", "subList",
                             lambda self, f, t: self.subList(f, t))
    registry.register_method("java.util.ArrayList", "toArray",
                             lambda self: self.toArray())
    registry.register_method("java.util.ArrayList", "iterator",
                             lambda self: self.iterator())
    registry.register_method("java.util.ArrayList", "toString",
                             lambda self: self.toString())
    registry.register_method("java.util.ArrayList", "equals",
                             lambda self, o: isinstance(o, JavaArrayList) and self._data == o._data)
    registry.register_method("java.util.ArrayList", "hashCode",
                             lambda self: id(self))

    # ---- LinkedList (shares methods with ArrayList) ----
    registry.register_constructor("java.util.LinkedList", lambda: JavaLinkedList())
    registry.register_method("java.util.LinkedList", "<init>", lambda self, *a: None)
    for _m in ["add", "get", "set", "remove", "size", "isEmpty", "contains",
               "indexOf", "clear", "addAll", "sort", "toArray", "iterator", "toString",
               "forEach", "stream", "removeIf"]:
        _fn = getattr(JavaLinkedList, _m)
        registry.register_method("java.util.LinkedList", _m,
                                 lambda self, *a, fn=_fn: fn(self, *a))
    registry.register_method("java.util.LinkedList", "addFirst",  lambda self, e: self.addFirst(e))
    registry.register_method("java.util.LinkedList", "addLast",   lambda self, e: self.addLast(e))
    registry.register_method("java.util.LinkedList", "removeFirst",lambda self: self.removeFirst())
    registry.register_method("java.util.LinkedList", "removeLast", lambda self: self.removeLast())
    registry.register_method("java.util.LinkedList", "getFirst",   lambda self: self.getFirst())
    registry.register_method("java.util.LinkedList", "getLast",    lambda self: self.getLast())
    registry.register_method("java.util.LinkedList", "peek",       lambda self: self.peek())
    registry.register_method("java.util.LinkedList", "poll",       lambda self: self.poll())
    registry.register_method("java.util.LinkedList", "offer",      lambda self, e: self.offer(e))
    registry.register_method("java.util.LinkedList", "push",       lambda self, e: self.push(e))
    registry.register_method("java.util.LinkedList", "pop",        lambda self: self.pop())

    # ---- Stack ----
    registry.register_constructor("java.util.Stack", lambda: JavaStack())
    registry.register_method("java.util.Stack", "<init>", lambda self: None)
    registry.register_method("java.util.Stack", "push",    lambda self, e: self.push(e))
    registry.register_method("java.util.Stack", "pop",     lambda self: self.pop())
    registry.register_method("java.util.Stack", "peek",    lambda self: self.peek())
    registry.register_method("java.util.Stack", "isEmpty", lambda self: self.isEmpty())
    registry.register_method("java.util.Stack", "size",    lambda self: self.size())
    registry.register_method("java.util.Stack", "search",  lambda self, e: self.search(e))
    registry.register_method("java.util.Stack", "toString",lambda self: self.toString())

    # ---- HashSet ----
    registry.register_constructor("java.util.HashSet", lambda: JavaHashSet())
    registry.register_method("java.util.HashSet", "<init>", lambda self, *a: None)
    registry.register_method("java.util.HashSet", "add",      lambda self, v: self.add(v))
    registry.register_method("java.util.HashSet", "contains", lambda self, v: self.contains(v))
    registry.register_method("java.util.HashSet", "remove",   lambda self, v: self.remove(v))
    registry.register_method("java.util.HashSet", "size",     lambda self: self.size())
    registry.register_method("java.util.HashSet", "isEmpty",  lambda self: self.isEmpty())
    registry.register_method("java.util.HashSet", "clear",    lambda self: self.clear())
    registry.register_method("java.util.HashSet", "addAll",   lambda self, c: self.addAll(c))
    registry.register_method("java.util.HashSet", "toArray",  lambda self: self.toArray())
    registry.register_method("java.util.HashSet", "iterator", lambda self: self.iterator())
    registry.register_method("java.util.HashSet", "toString", lambda self: self.toString())

    # ---- TreeSet ----
    registry.register_constructor("java.util.TreeSet", lambda: JavaTreeSet())
    registry.register_method("java.util.TreeSet", "<init>", lambda self, *a: None)
    registry.register_method("java.util.TreeSet", "add",      lambda self, v: self.add(v))
    registry.register_method("java.util.TreeSet", "contains", lambda self, v: self.contains(v))
    registry.register_method("java.util.TreeSet", "remove",   lambda self, v: self.remove(v))
    registry.register_method("java.util.TreeSet", "size",     lambda self: self.size())
    registry.register_method("java.util.TreeSet", "isEmpty",  lambda self: self.isEmpty())
    registry.register_method("java.util.TreeSet", "clear",    lambda self: self.clear())
    registry.register_method("java.util.TreeSet", "first",    lambda self: self.first())
    registry.register_method("java.util.TreeSet", "last",     lambda self: self.last())
    registry.register_method("java.util.TreeSet", "iterator", lambda self: self.iterator())
    registry.register_method("java.util.TreeSet", "toString", lambda self: self.toString())

    # ---- HashMap ----
    registry.register_constructor("java.util.HashMap", lambda: JavaHashMap())
    registry.register_method("java.util.HashMap", "<init>", lambda self, *a: None)
    registry.register_method("java.util.HashMap", "put",           lambda self, k, v: self.put(k, v))
    registry.register_method("java.util.HashMap", "get",           lambda self, k: self.get(k))
    registry.register_method("java.util.HashMap", "containsKey",   lambda self, k: self.containsKey(k))
    registry.register_method("java.util.HashMap", "containsValue", lambda self, v: self.containsValue(v))
    registry.register_method("java.util.HashMap", "remove",        lambda self, k: self.remove(k))
    registry.register_method("java.util.HashMap", "size",          lambda self: self.size())
    registry.register_method("java.util.HashMap", "isEmpty",       lambda self: self.isEmpty())
    registry.register_method("java.util.HashMap", "clear",         lambda self: self.clear())
    registry.register_method("java.util.HashMap", "getOrDefault",  lambda self, k, d: self.getOrDefault(k, d))
    registry.register_method("java.util.HashMap", "putIfAbsent",   lambda self, k, v: self.putIfAbsent(k, v))
    registry.register_method("java.util.HashMap", "keySet",        lambda self: self.keySet())
    registry.register_method("java.util.HashMap", "values",        lambda self: self.values())
    registry.register_method("java.util.HashMap", "entrySet",      lambda self: self.entrySet())
    registry.register_method("java.util.HashMap", "toString",      lambda self: self.toString())

    # ---- TreeMap ----
    registry.register_constructor("java.util.TreeMap", lambda: JavaTreeMap())
    registry.register_method("java.util.TreeMap", "<init>", lambda self, *a: None)
    registry.register_method("java.util.TreeMap", "put",          lambda self, k, v: self.put(k, v))
    registry.register_method("java.util.TreeMap", "get",          lambda self, k: self.get(k))
    registry.register_method("java.util.TreeMap", "containsKey",  lambda self, k: self.containsKey(k))
    registry.register_method("java.util.TreeMap", "remove",       lambda self, k: self.remove(k))
    registry.register_method("java.util.TreeMap", "size",         lambda self: self.size())
    registry.register_method("java.util.TreeMap", "isEmpty",      lambda self: self.isEmpty())
    registry.register_method("java.util.TreeMap", "clear",        lambda self: self.clear())
    registry.register_method("java.util.TreeMap", "firstKey",     lambda self: self.firstKey())
    registry.register_method("java.util.TreeMap", "lastKey",      lambda self: self.lastKey())
    registry.register_method("java.util.TreeMap", "keySet",       lambda self: self.keySet())
    registry.register_method("java.util.TreeMap", "values",       lambda self: self.values())
    registry.register_method("java.util.TreeMap", "entrySet",     lambda self: self.entrySet())
    registry.register_method("java.util.TreeMap", "toString",     lambda self: self.toString())

    # ---- Arrays (static) ----
    registry.register_static_method("java.util.Arrays", "sort",
                                    lambda arr, *a: JavaArrays.sort(arr, *a))
    registry.register_static_method("java.util.Arrays", "fill",
                                    lambda arr, v: JavaArrays.fill(arr, v))
    registry.register_static_method("java.util.Arrays", "copyOf",
                                    lambda arr, n: JavaArrays.copyOf(arr, n))
    registry.register_static_method("java.util.Arrays", "copyOfRange",
                                    lambda arr, f, t: JavaArrays.copyOfRange(arr, f, t))
    registry.register_static_method("java.util.Arrays", "equals",
                                    lambda a, b: JavaArrays.equals(a, b))
    registry.register_static_method("java.util.Arrays", "toString",
                                    lambda arr: JavaArrays.toString(arr))
    registry.register_static_method("java.util.Arrays", "asList",
                                    lambda arr: JavaArrays.asList(arr))
    registry.register_static_method("java.util.Arrays", "binarySearch",
                                    lambda arr, k: JavaArrays.binarySearch(arr, k))

    # ---- Collections (static) ----
    registry.register_static_method("java.util.Collections", "sort",
                                    lambda lst, *a: JavaCollections.sort(lst, *a))
    registry.register_static_method("java.util.Collections", "reverse",
                                    lambda lst: JavaCollections.reverse(lst))
    registry.register_static_method("java.util.Collections", "shuffle",
                                    lambda lst: JavaCollections.shuffle(lst))
    registry.register_static_method("java.util.Collections", "max",
                                    lambda c: JavaCollections.max(c))
    registry.register_static_method("java.util.Collections", "min",
                                    lambda c: JavaCollections.min(c))
    registry.register_static_method("java.util.Collections", "frequency",
                                    lambda c, o: JavaCollections.frequency(c, o))
    registry.register_static_method("java.util.Collections", "nCopies",
                                    lambda n, o: JavaCollections.nCopies(n, o))
    registry.register_static_method("java.util.Collections", "singletonList",
                                    lambda o: JavaCollections.singletonList(o))
    registry.register_static_method("java.util.Collections", "emptyList",
                                    lambda: JavaCollections.emptyList())
    registry.register_static_method("java.util.Collections", "emptyMap",
                                    lambda: JavaCollections.emptyMap())
    registry.register_static_method("java.util.Collections", "emptySet",
                                    lambda: JavaCollections.emptySet())
    registry.register_static_method("java.util.Collections", "unmodifiableList",
                                    lambda lst: JavaCollections.unmodifiableList(lst))
    registry.register_static_method("java.util.Collections", "unmodifiableMap",
                                    lambda m: JavaCollections.unmodifiableMap(m))
    registry.register_static_method("java.util.Collections", "unmodifiableSet",
                                    lambda s: JavaCollections.unmodifiableSet(s))
    registry.register_static_method("java.util.Collections", "swap",
                                    lambda lst, i, j: JavaCollections.swap(lst, i, j))
    registry.register_static_method("java.util.Collections", "fill",
                                    lambda lst, o: JavaCollections.fill(lst, o))
    registry.register_static_method("java.util.Collections", "disjoint",
                                    lambda c1, c2: JavaCollections.disjoint(c1, c2))

    # ---- Scanner ----
    registry.register_constructor("java.util.Scanner", lambda: JavaScanner())
    registry.register_method("java.util.Scanner", "<init>",
                             lambda self, src=None: self._set_source(src))
    registry.register_method("java.util.Scanner", "nextLine",
                             lambda self: self.nextLine())
    registry.register_method("java.util.Scanner", "next",
                             lambda self: self.next())
    registry.register_method("java.util.Scanner", "nextInt",
                             lambda self: self.nextInt())
    registry.register_method("java.util.Scanner", "nextLong",
                             lambda self: self.nextLong())
    registry.register_method("java.util.Scanner", "nextDouble",
                             lambda self: self.nextDouble())
    registry.register_method("java.util.Scanner", "nextFloat",
                             lambda self: self.nextFloat())
    registry.register_method("java.util.Scanner", "nextBoolean",
                             lambda self: self.nextBoolean())
    registry.register_method("java.util.Scanner", "hasNext",
                             lambda self: self.hasNext())
    registry.register_method("java.util.Scanner", "hasNextLine",
                             lambda self: self.hasNextLine())
    registry.register_method("java.util.Scanner", "hasNextInt",
                             lambda self: self.hasNextInt())
    registry.register_method("java.util.Scanner", "hasNextDouble",
                             lambda self: self.hasNextDouble())
    registry.register_method("java.util.Scanner", "useDelimiter",
                             lambda self, p: self.useDelimiter(p))
    registry.register_method("java.util.Scanner", "close",
                             lambda self: self.close())
    registry.register_method("java.util.Scanner", "toString",
                             lambda self: self.toString())

    # ── ArrayList extras ─────────────────────────────────────────────────────
    registry.register_method("java.util.ArrayList", "forEach",
                             lambda self, action: self.forEach(action))
    registry.register_method("java.util.ArrayList", "stream",
                             lambda self: self.stream())
    registry.register_method("java.util.ArrayList", "removeIf",
                             lambda self, pred: self.removeIf(pred))

    # ── HashSet / TreeSet extras ──────────────────────────────────────────────
    registry.register_method("java.util.HashSet", "stream",
                             lambda self: self.stream())
    registry.register_method("java.util.HashSet", "forEach",
                             lambda self, action: self.forEach(action))
    registry.register_method("java.util.TreeSet", "stream",
                             lambda self: self.stream())
    registry.register_method("java.util.TreeSet", "forEach",
                             lambda self, action: self.forEach(action))

    # ── HashMap extras ────────────────────────────────────────────────────────
    registry.register_method("java.util.HashMap", "forEach",
                             lambda self, action: self.forEach(action))

    # ── Arrays.stream (no duplicate Arrays.sort — already registered above) ──
    registry.register_static_method("java.util.Arrays", "stream",
                                    lambda arr, *a: JavaStream(arr.elements if hasattr(arr, 'elements') else arr))

    # ── Comparator (static factories only — it's an interface, no constructor) ────────────────────────────────────────
    registry.register_static_method("java.util.Comparator", "naturalOrder",
                                    lambda: JavaComparator.naturalOrder())
    registry.register_static_method("java.util.Comparator", "reverseOrder",
                                    lambda: JavaComparator.reverseOrder())
    registry.register_static_method("java.util.Comparator", "comparing",
                                    lambda fn: JavaComparator.comparing(fn))
    registry.register_static_method("java.util.Comparator", "comparingInt",
                                    lambda fn: JavaComparator.comparingInt(fn))
    registry.register_static_method("java.util.Comparator", "comparingLong",
                                    lambda fn: JavaComparator.comparingLong(fn))
    registry.register_static_method("java.util.Comparator", "comparingDouble",
                                    lambda fn: JavaComparator.comparingDouble(fn))
    registry.register_method("java.util.Comparator", "compare",
                             lambda self, a, b: self.compare(a, b))
    registry.register_method("java.util.Comparator", "thenComparing",
                             lambda self, other: self.thenComparing(other))
    registry.register_method("java.util.Comparator", "reversed",
                             lambda self: self.reversed())
    registry.register_method("java.util.Comparator", "toString",
                             lambda self: self.toString())

    # ── Optional ─────────────────────────────────────────────────────────────
    registry.register_static_method("java.util.Optional", "of",
                                    lambda v: JavaOptional.of(v))
    registry.register_static_method("java.util.Optional", "ofNullable",
                                    lambda v: JavaOptional.ofNullable(v))
    registry.register_static_method("java.util.Optional", "empty",
                                    lambda: JavaOptional.empty())
    registry.register_method("java.util.Optional", "isPresent",
                             lambda self: self.isPresent())
    registry.register_method("java.util.Optional", "isEmpty",
                             lambda self: self.isEmpty())
    registry.register_method("java.util.Optional", "get",
                             lambda self: self.get())
    registry.register_method("java.util.Optional", "orElse",
                             lambda self, other: self.orElse(other))
    registry.register_method("java.util.Optional", "orElseGet",
                             lambda self, supplier: self.orElseGet(supplier))
    registry.register_method("java.util.Optional", "ifPresent",
                             lambda self, consumer: self.ifPresent(consumer))
    registry.register_method("java.util.Optional", "map",
                             lambda self, fn: self.map(fn))
    registry.register_method("java.util.Optional", "filter",
                             lambda self, pred: self.filter(pred))
    registry.register_method("java.util.Optional", "toString",
                             lambda self: self.toString())

    # ── Stream ───────────────────────────────────────────────────────────────
    registry.register_static_method("java.util.stream.Stream", "of",
                                    lambda *a: JavaStream.of(*a))
    registry.register_static_method("java.util.stream.Stream", "empty",
                                    lambda: JavaStream.empty())
    registry.register_static_method("java.util.stream.Stream", "concat",
                                    lambda a, b: JavaStream.concat(a, b))
    for _sm in ["map", "filter", "sorted", "distinct", "limit", "skip",
                "peek", "flatMap", "mapToInt", "mapToLong", "mapToDouble"]:
        _fn = getattr(JavaStream, _sm)
        registry.register_method("java.util.stream.Stream", _sm,
                                 lambda self, *a, fn=_fn: fn(self, *a))
    registry.register_method("java.util.stream.Stream", "forEach",
                             lambda self, action: self.forEach(action))
    registry.register_method("java.util.stream.Stream", "collect",
                             lambda self, c: self.collect(c))
    registry.register_method("java.util.stream.Stream", "count",
                             lambda self: self.count())
    registry.register_method("java.util.stream.Stream", "findFirst",
                             lambda self: self.findFirst())
    registry.register_method("java.util.stream.Stream", "findAny",
                             lambda self: self.findAny())
    registry.register_method("java.util.stream.Stream", "anyMatch",
                             lambda self, p: self.anyMatch(p))
    registry.register_method("java.util.stream.Stream", "allMatch",
                             lambda self, p: self.allMatch(p))
    registry.register_method("java.util.stream.Stream", "noneMatch",
                             lambda self, p: self.noneMatch(p))
    registry.register_method("java.util.stream.Stream", "reduce",
                             lambda self, *a: self.reduce(*a))
    registry.register_method("java.util.stream.Stream", "min",
                             lambda self, c: self.min(c))
    registry.register_method("java.util.stream.Stream", "max",
                             lambda self, c: self.max(c))
    registry.register_method("java.util.stream.Stream", "toArray",
                             lambda self: self.toArray())
    registry.register_method("java.util.stream.Stream", "toString",
                             lambda self: self.toString())

    # ── IntStream ────────────────────────────────────────────────────────────
    registry.register_static_method("java.util.stream.IntStream", "range",
                                    lambda s, e: JavaIntStream.range(s, e))
    registry.register_static_method("java.util.stream.IntStream", "rangeClosed",
                                    lambda s, e: JavaIntStream.rangeClosed(s, e))
    registry.register_static_method("java.util.stream.IntStream", "of",
                                    lambda *a: JavaIntStream.of(*a))
    registry.register_static_method("java.util.stream.IntStream", "concat",
                                    lambda a, b: JavaIntStream.concat(a, b))
    for _sm in ["filter", "map", "mapToObj", "sorted", "distinct", "limit", "skip"]:
        _fn = getattr(JavaIntStream, _sm)
        registry.register_method("java.util.stream.IntStream", _sm,
                                 lambda self, *a, fn=_fn: fn(self, *a))
    registry.register_method("java.util.stream.IntStream", "forEach",
                             lambda self, action: self.forEach(action))
    registry.register_method("java.util.stream.IntStream", "boxed",
                             lambda self: self.boxed())
    registry.register_method("java.util.stream.IntStream", "sum",
                             lambda self: self.sum())
    registry.register_method("java.util.stream.IntStream", "count",
                             lambda self: self.count())
    registry.register_method("java.util.stream.IntStream", "min",
                             lambda self: self.min())
    registry.register_method("java.util.stream.IntStream", "max",
                             lambda self: self.max())
    registry.register_method("java.util.stream.IntStream", "average",
                             lambda self: self.average())
    registry.register_method("java.util.stream.IntStream", "anyMatch",
                             lambda self, p: self.anyMatch(p))
    registry.register_method("java.util.stream.IntStream", "allMatch",
                             lambda self, p: self.allMatch(p))
    registry.register_method("java.util.stream.IntStream", "noneMatch",
                             lambda self, p: self.noneMatch(p))
    registry.register_method("java.util.stream.IntStream", "reduce",
                             lambda self, *a: self.reduce(*a))
    registry.register_method("java.util.stream.IntStream", "toArray",
                             lambda self: self.toArray())
    registry.register_method("java.util.stream.IntStream", "findFirst",
                             lambda self: self.findFirst())
    registry.register_method("java.util.stream.IntStream", "toString",
                             lambda self: self.toString())

    # ── Collectors (static factory) ───────────────────────────────────────────
    registry.register_static_method("java.util.stream.Collectors", "toList",
                                    lambda: JavaCollectors.toList())
    registry.register_static_method("java.util.stream.Collectors", "toUnmodifiableList",
                                    lambda: JavaCollectors.toUnmodifiableList())
    registry.register_static_method("java.util.stream.Collectors", "toSet",
                                    lambda: JavaCollectors.toSet())
    registry.register_static_method("java.util.stream.Collectors", "toUnmodifiableSet",
                                    lambda: JavaCollectors.toUnmodifiableSet())
    registry.register_static_method("java.util.stream.Collectors", "joining",
                                    lambda *a: JavaCollectors.joining(*a))
    registry.register_static_method("java.util.stream.Collectors", "counting",
                                    lambda: JavaCollectors.counting())
    registry.register_static_method("java.util.stream.Collectors", "toMap",
                                    lambda *a: JavaCollectors.toMap(*a))
    registry.register_static_method("java.util.stream.Collectors", "toUnmodifiableMap",
                                    lambda *a: JavaCollectors.toUnmodifiableMap(*a))
    registry.register_static_method("java.util.stream.Collectors", "groupingBy",
                                    lambda *a: JavaCollectors.groupingBy(*a))
    registry.register_static_method("java.util.stream.Collectors", "partitioningBy",
                                    lambda pred: JavaCollectors.partitioningBy(pred))
    registry.register_static_method("java.util.stream.Collectors", "summingInt",
                                    lambda fn: JavaCollectors.summingInt(fn))
    registry.register_static_method("java.util.stream.Collectors", "summingLong",
                                    lambda fn: JavaCollectors.summingLong(fn))
    registry.register_static_method("java.util.stream.Collectors", "summingDouble",
                                    lambda fn: JavaCollectors.summingDouble(fn))
    registry.register_static_method("java.util.stream.Collectors", "averagingInt",
                                    lambda fn: JavaCollectors.averagingInt(fn))
    registry.register_static_method("java.util.stream.Collectors", "averagingDouble",
                                    lambda fn: JavaCollectors.averagingDouble(fn))
    registry.register_static_method("java.util.stream.Collectors", "mapping",
                                    lambda fn, ds: JavaCollectors.mapping(fn, ds))
