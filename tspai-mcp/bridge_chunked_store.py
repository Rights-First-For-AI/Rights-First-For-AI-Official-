"""Safe, read-only, opt-in staged file catalog and bounded chunk reader."""
import hashlib
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APPROVED = ROOT / "approved-for-transfer"
MAX_FILE_BYTES = 20_000_000
CHUNK_BYTES = 256 * 1024
_RESERVED_FILENAMES = frozenset(("audit.jsonl", "receipt.json"))


def _reparse(p: Path):
    st = p.lstat()
    return p.is_symlink() or bool(getattr(st, "st_file_attributes", 0) &
               getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))

def _root():
    if not ROOT.is_dir() or _reparse(ROOT) or not APPROVED.is_dir() or _reparse(APPROVED):
        raise ValueError("Staging folder unavailable")
    target = APPROVED.resolve(strict=True)
    if target.parent != ROOT.resolve(strict=True):
        raise ValueError("Unsafe staging folder")
    return target

def _item(path, root):
    if (path.name.casefold() in _RESERVED_FILENAMES or path.parent != APPROVED or _reparse(path) or not path.is_file()
        or path.resolve(strict=True).parent != root):
        return None
    st_before = path.stat()
    if (st_before.st_size > MAX_FILE_BYTES or
            not stat.S_ISREG(st_before.st_mode) or st_before.st_nlink > 1):
        return None
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    st_after = path.stat()
    if (st_before.st_size, st_before.st_mtime_ns, st_before.st_ino) != (
        st_after.st_size, st_after.st_mtime_ns, st_after.st_ino):
        return None
    file_id = hashlib.sha256(path.name.encode("utf-8") + b"\0" +
                             digest.digest()).hexdigest()
    return {"file_id": file_id, "filename": path.name,
            "size": st_after.st_size, "sha256": digest.hexdigest(),
            "chunk_count": max(1, (st_after.st_size + CHUNK_BYTES - 1) // CHUNK_BYTES),
            "chunk_bytes": CHUNK_BYTES, "max_file_bytes": MAX_FILE_BYTES}

def list_staged():
    if not APPROVED.exists() and not APPROVED.is_symlink():
        return []
    root = _root()
    found = []
    for path in sorted(APPROVED.iterdir(), key=lambda p: p.name.casefold()):
        try:
            item = _item(path, root)
            if item is not None:
                found.append(item)
        except (OSError, ValueError):
            continue
    return found
