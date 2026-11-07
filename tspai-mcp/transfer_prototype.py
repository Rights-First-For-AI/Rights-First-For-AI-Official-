"""Isolated TSPAI transfer prototype. Never alters source files."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import uuid

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def prepare_file(source, archive_root):
    source = Path(source)
    archive_root = Path(archive_root)
    if not source.is_file() or source.is_symlink():
        raise ValueError("Regular non-symlink file required")
    if archive_root.resolve() == source.resolve() or archive_root.resolve() in source.resolve().parents:
        raise ValueError("Archive must not be inside source")
    send_id = uuid.uuid4().hex
    folder = archive_root / send_id
    folder.mkdir(parents=True, exist_ok=False)
    log = folder / "audit.jsonl"
    dest = folder / source.name
    entry = {"id": send_id, "time_utc": datetime.now(timezone.utc).isoformat(),
             "source": str(source), "name": source.name, "size": source.stat().st_size,
             "sha256": digest(source), "status": "PREPARED_NOT_SENT"}
    with log.open("x", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    with source.open("rb") as inp, dest.open("xb") as out:
        shutil.copyfileobj(inp, out, 1024 * 1024)
        out.flush()
        os.fsync(out.fileno())
    copied = digest(dest)
    if copied != entry["sha256"]:
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"status": "COPY_MISMATCH"}) + "\n")
        raise IOError("Copy SHA256 mismatch")
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"status": "COPY_VERIFIED_NOT_SENT", "copy": str(dest),
                            "sha256": copied}) + "\n")
    return {"id": send_id, "source": str(source), "copy": str(dest),
            "name_preserved": dest.name == source.name,
            "sha256_match": copied == entry["sha256"], "status": "NOT_SENT"}

if __name__ == "__main__":
    import sys
    print(json.dumps(prepare_file(sys.argv[1], sys.argv[2]), ensure_ascii=False))
