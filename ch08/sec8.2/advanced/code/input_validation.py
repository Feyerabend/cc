import re
import os

# Bad: denylist. Tries to block known-bad characters. An attacker only
# needs to find one encoding or bypass not on the list (%2F, unicode
# lookalikes, null bytes, etc.).
def read_file_bad(base_dir: str, filename: str) -> bytes:
    if ".." in filename or filename.startswith("/"):
        raise ValueError("invalid path")
    path = os.path.join(base_dir, filename)
    with open(path, "rb") as f:
        return f.read()

# Good: allowlist the filename structure, then resolve and verify confinement.
# realpath() collapses all symlinks and ".." components; the prefix check
# then proves the resolved path is still inside base_dir regardless of
# what tricks were in the original string.
_SAFE_NAME = re.compile(r'^[A-Za-z0-9_\-]+\.[A-Za-z0-9]+$')

def read_file_good(base_dir: str, filename: str) -> bytes:
    if not _SAFE_NAME.match(filename):
        raise ValueError("filename contains disallowed characters")
    path     = os.path.realpath(os.path.join(base_dir, filename))
    resolved = os.path.realpath(base_dir)
    if not path.startswith(resolved + os.sep):
        raise ValueError("path traversal detected")
    with open(path, "rb") as f:
        return f.read()
