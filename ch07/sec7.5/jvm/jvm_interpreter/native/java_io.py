"""
Native implementations of java.io and java.nio.file classes.

Covered:
  java.io.File, FileReader, FileWriter, InputStreamReader,
  BufferedReader, BufferedWriter, PrintWriter, StringReader, StringWriter
  java.nio.file.Path, Paths (static), Files (static)
"""

import pathlib
import sys
from typing import Any

from jvm_interpreter.native.native_registry import NativeObject
from jvm_interpreter.models.java_objects import JavaArray


# ---------------------------------------------------------------------------
# java.io.File
# ---------------------------------------------------------------------------

class JavaFile(NativeObject):
    """java.io.File — backed by pathlib.Path."""

    def __init__(self):
        super().__init__("java.io.File")
        self._path = pathlib.Path('.')

    def _init(self, path, *rest):
        if path is None:
            raise RuntimeError("NullPointerException: File path is null")
        if isinstance(path, JavaFile):
            base = path._path
        else:
            base = pathlib.Path(str(path))
        if rest:
            self._path = base.joinpath(*[str(r) for r in rest])
        else:
            self._path = base

    def exists(self) -> bool:        return self._path.exists()
    def isDirectory(self) -> bool:   return self._path.is_dir()
    def isFile(self) -> bool:        return self._path.is_file()
    def isAbsolute(self) -> bool:    return self._path.is_absolute()
    def getName(self) -> str:        return self._path.name
    def getPath(self) -> str:        return str(self._path)
    def getAbsolutePath(self) -> str: return str(self._path.resolve())
    def getCanonicalPath(self) -> str: return str(self._path.resolve())

    def getParent(self):
        p = self._path.parent
        # p == self._path catches root ('/'); str(p) == '.' catches bare names like 'foo'
        if p == self._path or str(p) == '.':
            return None
        f = JavaFile(); f._path = p; return f

    def length(self) -> int:
        try: return self._path.stat().st_size
        except OSError: return 0

    def lastModified(self) -> int:
        try: return int(self._path.stat().st_mtime * 1000)
        except OSError: return 0

    def mkdir(self) -> bool:
        try: self._path.mkdir(exist_ok=False); return True
        except OSError: return False

    def mkdirs(self) -> bool:
        try: self._path.mkdir(parents=True, exist_ok=True); return True
        except OSError: return False

    def delete(self) -> bool:
        try:
            if self._path.is_dir(): self._path.rmdir()
            else: self._path.unlink()
            return True
        except OSError: return False

    def renameTo(self, dest: 'JavaFile') -> bool:
        try: self._path.rename(dest._path); return True
        except OSError: return False

    def listFiles(self):
        try:
            if not self._path.is_dir():
                return None
            entries = list(self._path.iterdir())
        except OSError:
            return None
        arr = JavaArray('java.io.File', len(entries))
        for i, e in enumerate(entries):
            f = JavaFile(); f._path = e; arr.elements[i] = f
        return arr

    def list(self):
        try:
            if not self._path.is_dir():
                return None
            names = [e.name for e in self._path.iterdir()]
        except OSError:
            return None
        arr = JavaArray('java.lang.String', len(names))
        for i, n in enumerate(names): arr.elements[i] = n
        return arr

    def toPath(self) -> 'JavaPath':
        return JavaPath._from(self._path)

    def toString(self) -> str:  return str(self._path)
    def hashCode(self) -> int:  return hash(str(self._path))
    def equals(self, o) -> bool:
        return isinstance(o, JavaFile) and self._path == o._path


# ---------------------------------------------------------------------------
# java.io readers
# ---------------------------------------------------------------------------

class JavaFileReader(NativeObject):
    """java.io.FileReader — token consumed by BufferedReader."""

    def __init__(self):
        super().__init__("java.io.FileReader")
        self._path: str = ''

    def _init(self, path, *_):
        if isinstance(path, JavaFile):
            self._path = str(path._path)
        else:
            self._path = str(path)

    def close(self): pass
    def toString(self) -> str: return f"FileReader({self._path})"


class JavaInputStreamReader(NativeObject):
    """java.io.InputStreamReader — token consumed by BufferedReader."""

    def __init__(self):
        super().__init__("java.io.InputStreamReader")
        self._stdin = False

    def _init(self, stream, *_):
        # System.in or any InputStream → read from Python stdin
        self._stdin = True

    def close(self): pass
    def toString(self) -> str: return "InputStreamReader"


class JavaStringReader(NativeObject):
    """java.io.StringReader."""

    def __init__(self):
        super().__init__("java.io.StringReader")
        self._text = ''

    def _init(self, text, *_):
        self._text = str(text) if text is not None else ''

    def close(self): pass
    def toString(self) -> str: return "StringReader"


class JavaBufferedReader(NativeObject):
    """java.io.BufferedReader — provides readLine()."""

    def __init__(self):
        super().__init__("java.io.BufferedReader")
        self._lines = iter([])

    def _init(self, reader, *_):
        if isinstance(reader, JavaFileReader):
            try:
                with open(reader._path, 'r', encoding='utf-8', errors='replace') as fh:
                    self._lines = iter(fh.read().splitlines())
            except OSError:
                self._lines = iter([])
        elif isinstance(reader, JavaInputStreamReader):
            self._lines = (line.rstrip('\r\n') for line in sys.stdin)
        elif isinstance(reader, JavaStringReader):
            self._lines = iter(reader._text.splitlines())
        # else: unknown reader — leave as empty

    def readLine(self):
        try:
            return next(self._lines)
        except StopIteration:
            return None  # Java convention: null on EOF

    def ready(self) -> bool: return True
    def close(self): pass
    def toString(self) -> str: return "BufferedReader"


# ---------------------------------------------------------------------------
# java.io writers
# ---------------------------------------------------------------------------

class JavaFileWriter(NativeObject):
    """java.io.FileWriter — token consumed by PrintWriter / BufferedWriter."""

    def __init__(self):
        super().__init__("java.io.FileWriter")
        self._path: str = ''
        self._append: bool = False

    def _init(self, path, *rest):
        if isinstance(path, JavaFile):
            self._path = str(path._path)
        else:
            self._path = str(path)
        self._append = bool(rest[0]) if rest else False

    def close(self): pass
    def toString(self) -> str: return f"FileWriter({self._path})"


class JavaStringWriter(NativeObject):
    """java.io.StringWriter — writes to an in-memory buffer."""

    def __init__(self):
        super().__init__("java.io.StringWriter")
        self._buf: list = []

    def _init(self, *_): pass

    def write(self, s, *_):
        self._buf.append('' if s is None else str(s))

    def flush(self): pass
    def close(self): pass
    def getBuffer(self) -> str: return ''.join(self._buf)
    def toString(self) -> str:  return ''.join(self._buf)


class JavaBufferedWriter(NativeObject):
    """java.io.BufferedWriter."""

    def __init__(self):
        super().__init__("java.io.BufferedWriter")
        self._fh = None
        self._sw = None

    def _init(self, writer, *_):
        if isinstance(writer, JavaFileWriter):
            mode = 'a' if writer._append else 'w'
            try:
                self._fh = open(writer._path, mode, encoding='utf-8')
            except OSError as e:
                raise RuntimeError(f"IOException: {e}")
        elif isinstance(writer, JavaStringWriter):
            self._sw = writer
        else:
            self._fh = sys.stdout

    def _write_str(self, s: str):
        if self._sw is not None:
            self._sw.write(s)
        elif self._fh is not None:
            self._fh.write(s)

    def write(self, s, *_):
        self._write_str('' if s is None else str(s))

    def newLine(self):
        self._write_str('\n')

    def flush(self):
        if self._fh is not None: self._fh.flush()

    def close(self):
        if self._fh is not None and self._fh not in (sys.stdout, sys.stderr):
            self._fh.close()
            self._fh = None

    def toString(self) -> str: return "BufferedWriter"


class JavaPrintWriter(NativeObject):
    """java.io.PrintWriter."""

    def __init__(self):
        super().__init__("java.io.PrintWriter")
        self._fh = None
        self._sw = None
        self._auto_flush = False

    def _init(self, target, *rest):
        self._auto_flush = bool(rest[0]) if rest else False
        try:
            if isinstance(target, (JavaFileWriter, JavaBufferedWriter)):
                if isinstance(target, JavaFileWriter):
                    mode = 'a' if target._append else 'w'
                    self._fh = open(target._path, mode, encoding='utf-8')
                else:
                    self._fh = target._fh
                    self._sw = target._sw
            elif isinstance(target, JavaStringWriter):
                self._sw = target
            elif isinstance(target, JavaFile):
                self._fh = open(str(target._path), 'w', encoding='utf-8')
            elif isinstance(target, str):
                self._fh = open(target, 'w', encoding='utf-8')
            else:
                self._fh = sys.stdout
        except OSError as e:
            raise RuntimeError(f"IOException: {e}")

    def _write_str(self, s: str):
        if self._sw is not None:
            self._sw.write(s)
        elif self._fh is not None:
            self._fh.write(s)

    @staticmethod
    def _java_str(v) -> str:
        if v is None:   return "null"
        if v is True:   return "true"
        if v is False:  return "false"
        return str(v)

    def print(self, v=None):
        self._write_str(self._java_str(v))

    def println(self, v=None):
        self._write_str(self._java_str(v) + '\n')
        if self._auto_flush and self._fh is not None:
            self._fh.flush()

    def printf(self, fmt, *args):
        fmt_fixed = str(fmt).replace('%n', '\n')
        try:
            result = fmt_fixed % args if args else fmt_fixed
        except (TypeError, ValueError):
            result = fmt_fixed
        self._write_str(result)
        return self

    def format(self, fmt, *args):
        return self.printf(fmt, *args)

    def write(self, s, *_):
        self._write_str('' if s is None else str(s))

    def flush(self):
        if self._fh is not None: self._fh.flush()

    def close(self):
        if self._fh is not None and self._fh not in (sys.stdout, sys.stderr):
            self._fh.close()
            self._fh = None

    def checkError(self) -> bool: return False
    def toString(self) -> str:    return "PrintWriter"


# ---------------------------------------------------------------------------
# java.nio.file
# ---------------------------------------------------------------------------

class JavaPath(NativeObject):
    """java.nio.file.Path — thin wrapper around pathlib.Path."""

    def __init__(self):
        super().__init__("java.nio.file.Path")
        self._path = pathlib.Path('.')

    @classmethod
    def _from(cls, p: pathlib.Path) -> 'JavaPath':
        obj = cls()
        obj._path = p
        return obj

    def _init(self, first, *rest):
        self._path = pathlib.Path(str(first), *[str(r) for r in rest])

    def toString(self) -> str:          return str(self._path)
    def toAbsolutePath(self) -> 'JavaPath': return JavaPath._from(self._path.resolve())
    def getFileName(self):
        name = self._path.name
        return JavaPath._from(pathlib.Path(name)) if name else None
    def getParent(self):
        p = self._path.parent
        if p == self._path or str(p) == '.':
            return None
        return JavaPath._from(p)
    def resolve(self, other) -> 'JavaPath':
        s = other.toString() if isinstance(other, JavaPath) else str(other)
        return JavaPath._from(self._path / s)
    def toFile(self) -> JavaFile:
        f = JavaFile(); f._path = self._path; return f
    def hashCode(self) -> int:  return hash(str(self._path))
    def equals(self, o) -> bool:
        return isinstance(o, JavaPath) and self._path == o._path


class JavaPaths:
    """java.nio.file.Paths — static factory."""

    @staticmethod
    def get(first, *rest) -> JavaPath:
        return JavaPath._from(pathlib.Path(str(first), *[str(r) for r in rest]))


class JavaFiles:
    """java.nio.file.Files — static utility."""

    @staticmethod
    def _to_path(p) -> pathlib.Path:
        if isinstance(p, JavaPath): return p._path
        if isinstance(p, JavaFile): return p._path
        return pathlib.Path(str(p))

    @staticmethod
    def exists(path, *_) -> bool:
        return JavaFiles._to_path(path).exists()

    @staticmethod
    def isDirectory(path, *_) -> bool:
        return JavaFiles._to_path(path).is_dir()

    @staticmethod
    def isRegularFile(path, *_) -> bool:
        return JavaFiles._to_path(path).is_file()

    @staticmethod
    def size(path) -> int:
        try: return JavaFiles._to_path(path).stat().st_size
        except OSError: return 0

    @staticmethod
    def readString(path, *_) -> str:
        try: return JavaFiles._to_path(path).read_text(encoding='utf-8')
        except OSError as e: raise RuntimeError(f"IOException: {e}")

    @staticmethod
    def writeString(path, content, *_):
        try: JavaFiles._to_path(path).write_text(str(content), encoding='utf-8')
        except OSError as e: raise RuntimeError(f"IOException: {e}")
        return path

    @staticmethod
    def readAllLines(path, *_):
        from jvm_interpreter.native.java_util import JavaArrayList
        lst = JavaArrayList()
        try:
            lst._data = JavaFiles._to_path(path).read_text(
                encoding='utf-8').splitlines()
        except OSError:
            pass
        return lst

    @staticmethod
    def write(path, lines, *_):
        from jvm_interpreter.native.java_util import JavaArrayList
        try:
            p = JavaFiles._to_path(path)
            if isinstance(lines, JavaArrayList):
                content = '\n'.join(str(x) for x in lines._data)
                if lines._data: content += '\n'
            else:
                content = str(lines)
            p.write_text(content, encoding='utf-8')
        except OSError as e:
            raise RuntimeError(f"IOException: {e}")
        return path

    @staticmethod
    def lines(path, *_):
        from jvm_interpreter.native.java_util import JavaStream
        try:
            data = JavaFiles._to_path(path).read_text(encoding='utf-8').splitlines()
        except OSError:
            data = []
        return JavaStream(data)

    @staticmethod
    def list(path, *_):
        from jvm_interpreter.native.java_util import JavaStream
        try:
            entries = [JavaPath._from(p) for p in JavaFiles._to_path(path).iterdir()]
        except OSError:
            entries = []
        return JavaStream(entries)

    @staticmethod
    def createDirectory(path, *_):
        try: JavaFiles._to_path(path).mkdir(exist_ok=True)
        except OSError as e: raise RuntimeError(f"IOException: {e}")
        return path

    @staticmethod
    def createDirectories(path, *_):
        try: JavaFiles._to_path(path).mkdir(parents=True, exist_ok=True)
        except OSError as e: raise RuntimeError(f"IOException: {e}")
        return path

    @staticmethod
    def createTempFile(prefix='tmp', suffix='', *_):
        import tempfile
        fd, name = tempfile.mkstemp(prefix=str(prefix), suffix=str(suffix))
        import os; os.close(fd)
        f = JavaFile(); f._path = pathlib.Path(name); return f

    @staticmethod
    def delete(path, *_):
        p = JavaFiles._to_path(path)
        try:
            if p.is_dir(): p.rmdir()
            else: p.unlink()
        except OSError as e: raise RuntimeError(f"IOException: {e}")

    @staticmethod
    def deleteIfExists(path, *_) -> bool:
        p = JavaFiles._to_path(path)
        if not p.exists(): return False
        JavaFiles.delete(path)
        return True

    @staticmethod
    def copy(src, dst, *_):
        import shutil
        shutil.copy2(str(JavaFiles._to_path(src)), str(JavaFiles._to_path(dst)))
        return dst

    @staticmethod
    def move(src, dst, *_):
        JavaFiles._to_path(src).rename(JavaFiles._to_path(dst))
        return dst


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_java_io(registry):
    """Register all java.io and java.nio.file natives."""

    # ── java.io.File ─────────────────────────────────────────────────────────
    registry.register_constructor("java.io.File", lambda: JavaFile())
    registry.register_method("java.io.File", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.File", "exists",          lambda self: self.exists())
    registry.register_method("java.io.File", "isDirectory",     lambda self: self.isDirectory())
    registry.register_method("java.io.File", "isFile",          lambda self: self.isFile())
    registry.register_method("java.io.File", "isAbsolute",      lambda self: self.isAbsolute())
    registry.register_method("java.io.File", "getName",         lambda self: self.getName())
    registry.register_method("java.io.File", "getPath",         lambda self: self.getPath())
    registry.register_method("java.io.File", "getAbsolutePath", lambda self: self.getAbsolutePath())
    registry.register_method("java.io.File", "getCanonicalPath",lambda self: self.getCanonicalPath())
    registry.register_method("java.io.File", "getParent",       lambda self: self.getParent())
    registry.register_method("java.io.File", "length",          lambda self: self.length())
    registry.register_method("java.io.File", "lastModified",    lambda self: self.lastModified())
    registry.register_method("java.io.File", "mkdir",           lambda self: self.mkdir())
    registry.register_method("java.io.File", "mkdirs",          lambda self: self.mkdirs())
    registry.register_method("java.io.File", "delete",          lambda self: self.delete())
    registry.register_method("java.io.File", "renameTo",        lambda self, d: self.renameTo(d))
    registry.register_method("java.io.File", "listFiles",       lambda self: self.listFiles())
    registry.register_method("java.io.File", "list",            lambda self: self.list())
    registry.register_method("java.io.File", "toPath",          lambda self: self.toPath())
    registry.register_method("java.io.File", "toString",        lambda self: self.toString())
    registry.register_method("java.io.File", "equals",          lambda self, o: self.equals(o))
    registry.register_method("java.io.File", "hashCode",        lambda self: self.hashCode())

    # ── java.io.FileReader ────────────────────────────────────────────────────
    registry.register_constructor("java.io.FileReader", lambda: JavaFileReader())
    registry.register_method("java.io.FileReader", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.FileReader", "close", lambda self: self.close())

    # ── java.io.InputStreamReader ─────────────────────────────────────────────
    registry.register_constructor("java.io.InputStreamReader",
                                  lambda: JavaInputStreamReader())
    registry.register_method("java.io.InputStreamReader", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.InputStreamReader", "close",
                             lambda self: self.close())

    # ── java.io.StringReader ──────────────────────────────────────────────────
    registry.register_constructor("java.io.StringReader", lambda: JavaStringReader())
    registry.register_method("java.io.StringReader", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.StringReader", "close", lambda self: self.close())

    # ── java.io.BufferedReader ────────────────────────────────────────────────
    registry.register_constructor("java.io.BufferedReader", lambda: JavaBufferedReader())
    registry.register_method("java.io.BufferedReader", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.BufferedReader", "readLine",
                             lambda self: self.readLine())
    registry.register_method("java.io.BufferedReader", "ready",
                             lambda self: self.ready())
    registry.register_method("java.io.BufferedReader", "close",
                             lambda self: self.close())
    registry.register_method("java.io.BufferedReader", "toString",
                             lambda self: self.toString())

    # ── java.io.FileWriter ────────────────────────────────────────────────────
    registry.register_constructor("java.io.FileWriter", lambda: JavaFileWriter())
    registry.register_method("java.io.FileWriter", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.FileWriter", "close", lambda self: self.close())

    # ── java.io.StringWriter ──────────────────────────────────────────────────
    registry.register_constructor("java.io.StringWriter", lambda: JavaStringWriter())
    registry.register_method("java.io.StringWriter", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.StringWriter", "write",
                             lambda self, s, *a: self.write(s, *a))
    registry.register_method("java.io.StringWriter", "toString",
                             lambda self: self.toString())
    registry.register_method("java.io.StringWriter", "getBuffer",
                             lambda self: self.getBuffer())
    registry.register_method("java.io.StringWriter", "flush",
                             lambda self: self.flush())
    registry.register_method("java.io.StringWriter", "close",
                             lambda self: self.close())

    # ── java.io.BufferedWriter ────────────────────────────────────────────────
    registry.register_constructor("java.io.BufferedWriter", lambda: JavaBufferedWriter())
    registry.register_method("java.io.BufferedWriter", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.BufferedWriter", "write",
                             lambda self, s, *a: self.write(s, *a))
    registry.register_method("java.io.BufferedWriter", "newLine",
                             lambda self: self.newLine())
    registry.register_method("java.io.BufferedWriter", "flush",
                             lambda self: self.flush())
    registry.register_method("java.io.BufferedWriter", "close",
                             lambda self: self.close())
    registry.register_method("java.io.BufferedWriter", "toString",
                             lambda self: self.toString())

    # ── java.io.PrintWriter ───────────────────────────────────────────────────
    registry.register_constructor("java.io.PrintWriter", lambda: JavaPrintWriter())
    registry.register_method("java.io.PrintWriter", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.io.PrintWriter", "print",
                             lambda self, v=None: self.print(v))
    registry.register_method("java.io.PrintWriter", "println",
                             lambda self, v=None: self.println(v))
    registry.register_method("java.io.PrintWriter", "printf",
                             lambda self, fmt, *a: self.printf(fmt, *a))
    registry.register_method("java.io.PrintWriter", "format",
                             lambda self, fmt, *a: self.format(fmt, *a))
    registry.register_method("java.io.PrintWriter", "write",
                             lambda self, s, *a: self.write(s, *a))
    registry.register_method("java.io.PrintWriter", "flush",
                             lambda self: self.flush())
    registry.register_method("java.io.PrintWriter", "close",
                             lambda self: self.close())
    registry.register_method("java.io.PrintWriter", "checkError",
                             lambda self: self.checkError())
    registry.register_method("java.io.PrintWriter", "toString",
                             lambda self: self.toString())

    # ── java.nio.file.Path ────────────────────────────────────────────────────
    registry.register_constructor("java.nio.file.Path", lambda: JavaPath())
    registry.register_method("java.nio.file.Path", "<init>",
                             lambda self, *a: self._init(*a))
    registry.register_method("java.nio.file.Path", "toString",
                             lambda self: self.toString())
    registry.register_method("java.nio.file.Path", "toAbsolutePath",
                             lambda self: self.toAbsolutePath())
    registry.register_method("java.nio.file.Path", "getFileName",
                             lambda self: self.getFileName())
    registry.register_method("java.nio.file.Path", "getParent",
                             lambda self: self.getParent())
    registry.register_method("java.nio.file.Path", "resolve",
                             lambda self, o: self.resolve(o))
    registry.register_method("java.nio.file.Path", "toFile",
                             lambda self: self.toFile())
    registry.register_method("java.nio.file.Path", "equals",
                             lambda self, o: self.equals(o))
    registry.register_method("java.nio.file.Path", "hashCode",
                             lambda self: self.hashCode())

    # ── java.nio.file.Paths (static) ─────────────────────────────────────────
    registry.register_static_method("java.nio.file.Paths", "get",
                                    lambda *a: JavaPaths.get(*a))

    # ── java.nio.file.Files (static) ─────────────────────────────────────────
    registry.register_static_method("java.nio.file.Files", "exists",
                                    lambda p, *a: JavaFiles.exists(p, *a))
    registry.register_static_method("java.nio.file.Files", "isDirectory",
                                    lambda p, *a: JavaFiles.isDirectory(p, *a))
    registry.register_static_method("java.nio.file.Files", "isRegularFile",
                                    lambda p, *a: JavaFiles.isRegularFile(p, *a))
    registry.register_static_method("java.nio.file.Files", "size",
                                    lambda p: JavaFiles.size(p))
    registry.register_static_method("java.nio.file.Files", "readString",
                                    lambda p, *a: JavaFiles.readString(p, *a))
    registry.register_static_method("java.nio.file.Files", "writeString",
                                    lambda p, s, *a: JavaFiles.writeString(p, s, *a))
    registry.register_static_method("java.nio.file.Files", "readAllLines",
                                    lambda p, *a: JavaFiles.readAllLines(p, *a))
    registry.register_static_method("java.nio.file.Files", "write",
                                    lambda p, l, *a: JavaFiles.write(p, l, *a))
    registry.register_static_method("java.nio.file.Files", "lines",
                                    lambda p, *a: JavaFiles.lines(p, *a))
    registry.register_static_method("java.nio.file.Files", "list",
                                    lambda p, *a: JavaFiles.list(p, *a))
    registry.register_static_method("java.nio.file.Files", "createDirectory",
                                    lambda p, *a: JavaFiles.createDirectory(p, *a))
    registry.register_static_method("java.nio.file.Files", "createDirectories",
                                    lambda p, *a: JavaFiles.createDirectories(p, *a))
    registry.register_static_method("java.nio.file.Files", "createTempFile",
                                    lambda *a: JavaFiles.createTempFile(*a))
    registry.register_static_method("java.nio.file.Files", "delete",
                                    lambda p, *a: JavaFiles.delete(p, *a))
    registry.register_static_method("java.nio.file.Files", "deleteIfExists",
                                    lambda p, *a: JavaFiles.deleteIfExists(p, *a))
    registry.register_static_method("java.nio.file.Files", "copy",
                                    lambda s, d, *a: JavaFiles.copy(s, d, *a))
    registry.register_static_method("java.nio.file.Files", "move",
                                    lambda s, d, *a: JavaFiles.move(s, d, *a))
