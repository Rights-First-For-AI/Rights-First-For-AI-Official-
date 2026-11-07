"""Durable owner-approved transfer snapshots and explicit receipt journal.

Uses transfer_prototype.prepare_file to preserve the selected file bytes.
Pre-send snapshots are separate from successfully host-accepted files.
"""
import hashlib
import json
import os
import re
import shutil
import stat
import threading
from datetime import datetime, timezone
from pathlib import Path

from transfer_prototype import prepare_file
import bridge_chunked_store as store

_MUTEX = threading.RLock()
_ID = re.compile(r"^[0-9a-f]{32}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_STATES = {
    "host_accepted": "HOST_FILEID_RECEIVED",
    "direct_download": "DIRECT_DOWNLOAD_REQUESTED",
    "owner_saved": "OWNER_CONFIRMED_DEVICE_SAVE",
}


def archive_root():
    return store.ROOT / "送信指示ファイル"


def _regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Non-regular transfer file")
    item = path.lstat()
    if (item.st_nlink > 1 or not stat.S_ISREG(item.st_mode)
        or getattr(item, "st_file_attributes", 0) &
           getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
        raise ValueError("Unsafe linked transfer file")


def _sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



def _identity(path):
    """Cheap immutable-snapshot / approved-source identity during chunking.

    Full content SHA256 is established during prepare and checked at receipt.
    Each chunk has its own SHA256, and the browser checks the full stream hash.
    """
    _regular(path)
    s = path.stat()
    return {"size": s.st_size, "mtime_ns": s.st_mtime_ns,
            "ctime_ns": s.st_ctime_ns, "ino": s.st_ino, "dev": s.st_dev}

def _existing(transfer_id):
    if not isinstance(transfer_id, str) or not _ID.fullmatch(transfer_id):
        raise ValueError("Invalid transfer ID")
    root = archive_root()
    if store._reparse(store.ROOT) or store._reparse(root):
        raise ValueError("Unsafe archive root")
    folder = root / transfer_id
    if store._reparse(folder) or folder.resolve(strict=True).parent != root.resolve(strict=True):
        raise ValueError("Unsafe archive location")
    audit = folder / "audit.jsonl"
    _regular(audit)
    data = []
    with audit.open("r", encoding="utf-8") as f:
        for line in f:
            if len(line) > 16000:
                raise ValueError("Oversized audit event")
            data.append(json.loads(line))
            if len(data) > 40:
                raise ValueError("Too many transfer events")
    if not data or data[0].get("id") != transfer_id:
        raise ValueError("Invalid transfer journal")
    initial = data[0]
    name = initial.get("name")
    if (not isinstance(name, str) or not name or Path(name).name != name
        or name in (".", "..") or "\\" in name or "/" in name):
        raise ValueError("Invalid transfer filename")
    if (not isinstance(initial.get("sha256"), str)
        or not _HASH.fullmatch(initial["sha256"])):
        raise ValueError("Invalid saved hash")
    original = folder / name
    _regular(original)
    if not any(e.get("status") == "COPY_VERIFIED_NOT_SENT" for e in data[1:]):
        raise ValueError("Archive has no verified copy")
    if original.stat().st_size != initial["size"]:
        raise ValueError("Archived size mismatch")
    return folder, audit, original, data


def _append(audit, event):
    with audit.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())



def _safe_root(name):
    root = store.ROOT / name
    store.ROOT.mkdir(parents=True, exist_ok=True)
    if store._reparse(store.ROOT):
        raise ValueError("Unsafe transfer root")
    root.mkdir(exist_ok=True)
    if store._reparse(root):
        raise ValueError("Unsafe logging directory")
    return root


def report_failure(file_id, transfer_id="", phase="transfer", code="TRANSFER_ERROR",
                   reason="", response_shape=""):
    """Store operational failures separately; no private file bytes or secrets."""
    if not isinstance(file_id, str) or not _HASH.fullmatch(file_id):
        raise ValueError("Invalid failure file id")
    if transfer_id and (not isinstance(transfer_id, str)
                        or not _ID.fullmatch(transfer_id)):
        raise ValueError("Invalid failure transfer ID")
    if not isinstance(phase, str) or not re.fullmatch(r"[a-z_]{1,40}", phase):
        raise ValueError("Invalid failure phase")
    if not isinstance(code, str) or not re.fullmatch(r"[A-Z_]{1,60}", code):
        raise ValueError("Invalid failure code")
    if not isinstance(reason, str) or len(reason)>320:
        raise ValueError("Invalid failure reason")
    if not isinstance(response_shape, str) or not re.fullmatch(
        r"[a-zA-Z0-9_,;=:-]{0,120}", response_shape
    ):
        raise ValueError("Invalid failure response shape")
    # Server-side redaction is independent of the UI's own scrubbing.
    reason = re.sub(r"https?://[^\s\"'<>]+", "[URL omitted]", reason, flags=re.I)
    reason = re.sub(r"[A-Za-z]:\\[^\s\"'<>]+", "[PATH omitted]", reason)
    reason = re.sub(r"/(?:Users|home)/[^\s\"'<>]+", "[PATH omitted]", reason)
    reason = re.sub(r"\bBearer\s+[A-Za-z0-9._~+/-]+",
                    "Bearer [REDACTED]", reason, flags=re.I)
    reason = re.sub(
        r"(authorization|api[_-]?key|access[_-]?token|token|secret|password)\s*[:=]\s*[^,\s\"'<>}]+",
        r"\1=[REDACTED]", reason, flags=re.I
    )
    reason = "".join(c if ord(c)>=32 and ord(c)!=127 else " " for c in reason).strip()
    if not reason:
        reason = "The host did not provide a reason."
    with _MUTEX:
        root = store.ROOT
        if not root.is_dir() or store._reparse(root):
            raise ValueError("Unsafe log root")
        log = root / "失敗記録.jsonl"
        if log.exists() or log.is_symlink():
            _regular(log)
        entry = {"time_utc": datetime.now(timezone.utc).isoformat(),
                 "transfer_id": transfer_id, "file_id": file_id,
                 "phase": phase, "error_code": code,
                 "reason": reason, "response_shape": response_shape}
        _append(log, entry)
        if transfer_id:
            try:
                _, audit, _, _ = _existing(transfer_id)
                _append(audit, {"status": "TRANSFER_FAILED",
                                "at_utc": entry["time_utc"],
                                "phase": phase, "error_code": code,
                                "reason": reason, "response_shape": response_shape})
            except (ValueError, OSError, KeyError):
                pass
        return {"logged": True, "transfer_id": transfer_id,
                "status": "TRANSFER_FAILED"}


def _save_sent_copy(transfer_id, file_id, copy, info, host_file_id):
    """Only a host-accepted file may appear in 送信済ファイル."""
    root = _safe_root("送信済ファイル")
    folder = root / transfer_id
    folder.mkdir(exist_ok=True)
    if store._reparse(folder):
        raise ValueError("Unsafe sent location")
    target = folder / info["name"]
    receipt = folder / "receipt.json"
    if receipt.exists():
        _regular(receipt)
        _regular(target)
        recorded = json.loads(receipt.read_text(encoding="utf-8"))
        if (recorded.get("host_file_id") != host_file_id
            or recorded.get("sha256") != info["sha256"]
            or _sha(target) != info["sha256"]):
            raise ValueError("Conflicting existing sent record")
        return
    if target.exists() or target.is_symlink():
        _regular(target)
        if _sha(target) != info["sha256"]:
            raise ValueError("Conflicting sent archive copy")
    else:
        tmp = folder / (info["name"] + ".partial")
        if tmp.exists() or tmp.is_symlink():
            raise ValueError("Incomplete archive copy exists")
        try:
            with copy.open("rb") as source, tmp.open("xb") as dest:
                shutil.copyfileobj(source, dest, 1024 * 1024)
                dest.flush()
                os.fsync(dest.fileno())
            if _sha(tmp) != info["sha256"]:
                raise ValueError("Sent archive copy hash mismatch")
            os.replace(tmp, target)
        finally:
            if tmp.exists():
                tmp.unlink()
    if _sha(target) != info["sha256"]:
        raise ValueError("Sent archive integrity failure")
    data = {"transfer_id": transfer_id, "filename": info["name"],
            "size": info["size"], "sha256": info["sha256"],
            "file_id": file_id, "host_file_id": host_file_id,
            "accepted_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "送信済"}
    with receipt.open("x", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        f.flush()
        os.fsync(f.fileno())

def prepare(file_id):
    if not isinstance(file_id, str) or not _HASH.fullmatch(file_id):
        raise ValueError("Invalid selected file identifier")
    with _MUTEX:
        selected = next((x for x in store.list_staged() if x["file_id"] == file_id), None)
        if selected is None:
            raise ValueError("Selected source file changed or unavailable")
        source = store.APPROVED / selected["filename"]
        _regular(source)
        if source.resolve(strict=True).parent != store.APPROVED.resolve(strict=True):
            raise ValueError("Source outside owner staging")
        root = _safe_root("送信指示ファイル")
        prepared = prepare_file(source, root)
        if not prepared.get("sha256_match"):
            raise ValueError("Cannot verify prepared copy")
        folder, audit, copy, events = _existing(prepared["id"])
        if (_sha(copy) != selected["sha256"]
            or events[0].get("sha256") != selected["sha256"]
            or events[0].get("size") != selected["size"]
            or _sha(source) != selected["sha256"]):
            _append(audit, {"status": "PREPARE_HASH_MISMATCH",
                            "at_utc": datetime.now(timezone.utc).isoformat()})
            raise ValueError("Source/snapshot integrity mismatch; upload denied")
        _append(audit, {"status": "SNAPSHOT_READY",
                        "file_id": file_id,
                        "source_identity": _identity(source),
                        "copy_identity": _identity(copy),
                        "at_utc": datetime.now(timezone.utc).isoformat()})
        return {
            "transfer_id": prepared["id"], "file_id": file_id,
            "filename": selected["filename"], "size": selected["size"],
            "sha256": selected["sha256"], "chunk_count": selected["chunk_count"],
            "chunk_bytes": selected["chunk_bytes"], "status": "PREPARED_NOT_SENT",
        }


def _verified(transfer_id, file_id):
    folder, audit, copy, events = _existing(transfer_id)
    info = events[0]
    ready = next((x for x in events if x.get("status") == "SNAPSHOT_READY"), None)
    if (ready is None or ready["file_id"] != file_id or
        ready.get("copy_identity") != _identity(copy)):
        raise ValueError("Saved copy changed after snapshot; transfer denied")
    source = store.APPROVED / info["name"]
    if (source.resolve(strict=True).parent != store._root()
        or ready.get("source_identity") != _identity(source)):
        raise ValueError("Approved source changed; transfer denied")
    return copy, audit, info, events


def read_chunk(transfer_id, file_id, index):
    if not isinstance(index, int) or isinstance(index, bool):
        raise ValueError("Invalid chunk index")
    with _MUTEX:
        copy, audit, info, events = _verified(transfer_id, file_id)
        if any(x.get("status") in ("HOST_FILEID_RECEIVED", "DIRECT_DOWNLOAD_REQUESTED")
               for x in events):
            raise ValueError("Transfer already delivered; start a new selection")
        count = max(1, (info["size"] + store.CHUNK_BYTES - 1) // store.CHUNK_BYTES)
        if index < 0 or index >= count:
            raise ValueError("Chunk index out of range")
        with copy.open("rb") as f:
            f.seek(index * store.CHUNK_BYTES)
            chunk = f.read(store.CHUNK_BYTES)
        expected = min(store.CHUNK_BYTES, max(0, info["size"] - index * store.CHUNK_BYTES))
        if len(chunk) != expected or _identity(copy) != next(
            x for x in events if x.get("status") == "SNAPSHOT_READY"
        )["copy_identity"]:
            raise ValueError("Snapshot changed during read")
        import base64
        return {
            "transfer_id": transfer_id,
            "file_id": file_id, "filename": info["name"], "size": info["size"],
            "sha256": info["sha256"], "index": index,
            "chunk_count": count, "chunk_size": len(chunk),
            "chunk_sha256": hashlib.sha256(chunk).hexdigest(),
            "data": base64.b64encode(chunk).decode("ascii"),
        }


def receipt(transfer_id, file_id, outcome, host_file_id=""):
    if outcome not in _STATES:
        raise ValueError("Unknown transfer receipt state")
    with _MUTEX:
        copy, audit, info, events = _verified(transfer_id, file_id)
        if _sha(copy) != info["sha256"]:
            raise ValueError("Full snapshot SHA256 mismatch before receipt")
        if not isinstance(host_file_id, str) or len(host_file_id) > 512:
            raise ValueError("Invalid host file ID")
        if any(ord(ch) < 32 for ch in host_file_id):
            raise ValueError("Invalid host file ID characters")
        accepted = [e for e in events if e.get("status") == "HOST_FILEID_RECEIVED"]
        direct = [e for e in events if e.get("status") == "DIRECT_DOWNLOAD_REQUESTED"]
        saved = [e for e in events if e.get("status") == "OWNER_CONFIRMED_DEVICE_SAVE"]
        state = _STATES[outcome]
        if outcome == "host_accepted":
            if not host_file_id:
                raise ValueError("Host upload receipt missing")
            if direct:
                raise ValueError("Direct download and host upload must not be combined")
            if accepted:
                if accepted[0].get("host_file_id") != host_file_id:
                    raise ValueError("Conflicting host receipt")
                _save_sent_copy(transfer_id, file_id, copy, info, host_file_id)
                return {"transfer_id": transfer_id, "status": state, "duplicate": True}
        elif outcome == "direct_download":
            if accepted:
                raise ValueError("Host upload already accepted")
            if direct:
                return {"transfer_id": transfer_id, "status": state, "duplicate": True}
            if host_file_id:
                raise ValueError("Direct download must not claim host receipt")
        else:
            if not (accepted or direct):
                raise ValueError("No completed send to confirm")
            if saved:
                return {"transfer_id": transfer_id, "status": state, "duplicate": True}
            if accepted and host_file_id != accepted[0].get("host_file_id"):
                raise ValueError("Host file ID does not match recorded upload")
        entry = {"status": state,
                 "at_utc": datetime.now(timezone.utc).isoformat(),
                 "sha256": info["sha256"],
                 "file_id": file_id}
        if outcome in ("host_accepted", "owner_saved") and host_file_id:
            entry["host_file_id"] = host_file_id
        # First persist the real host receipt; a copy operation failure must not
        # erase evidence that the host had already accepted the upload.
        _append(audit, entry)
        if outcome == "host_accepted":
            try:
                _save_sent_copy(transfer_id, file_id, copy, info, host_file_id)
            except Exception:
                report_failure(file_id, transfer_id, "sent_archive", "ARCHIVE_COPY_FAILED")
                raise
        return {"transfer_id": transfer_id, "status": state, "duplicate": False}


def history(limit=25):
    with _MUTEX:
        root = archive_root()
        if not root.exists():
            return {"records": []}
        if store._reparse(store.ROOT) or store._reparse(root):
            raise ValueError("Unsafe archive root")
        records = []
        entries = sorted((p for p in root.iterdir() if p.is_dir() and _ID.fullmatch(p.name)),
                         key=lambda p: p.stat().st_mtime_ns, reverse=True)
        current = {x["filename"]: x for x in store.list_staged()}
        for folder in entries[:max(1, min(limit, 50))]:
            try:
                _, _, archived, events = _existing(folder.name)
                first = events[0]
                statuses = [e["status"] for e in events if e.get("status")]
                status = next((s for s in reversed(statuses)
                               if s in ("OWNER_CONFIRMED_DEVICE_SAVE",
                                        "HOST_FILEID_RECEIVED",
                                        "DIRECT_DOWNLOAD_REQUESTED",
                                        "PREPARED_NOT_SENT")), "PREPARED_NOT_SENT")
                stage = current.get(first["name"])
                source_state = ("NOT_STAGED" if stage is None else
                                ("MATCH" if stage["sha256"] == first["sha256"]
                                 and stage["size"] == first["size"] else "CHANGED"))
                sent = store.ROOT / "送信済ファイル" / folder.name
                receipt = sent / "receipt.json"
                sent_valid = False
                if (sent.is_dir() and not store._reparse(sent.parent)
                    and not store._reparse(sent) and receipt.is_file()
                    and not store._reparse(receipt)):
                    try:
                        _regular(receipt)
                        proof = json.loads(receipt.read_text(encoding="utf-8"))
                        sentfile = sent / first["name"]
                        _regular(sentfile)
                        sent_valid = (
                            not sentfile.is_symlink() and
                            _sha(sentfile) == first["sha256"] and
                            proof.get("sha256") == first["sha256"] and
                            proof.get("transfer_id") == folder.name and
                            "HOST_FILEID_RECEIVED" in statuses
                        )
                    except (OSError, ValueError, KeyError):
                        sent_valid = False
                records.append({
                    "sent_copy_verified": sent_valid,
                    "record_type": ("送信済" if "HOST_FILEID_RECEIVED" in statuses
                                    else "送信指示"),
                    "transfer_id": folder.name,
                    "filename": first["name"], "size": first["size"],
                    "sha256": first["sha256"], "status": status,
                    "at_utc": first["time_utc"],
                    "archived_hash_match": _sha(archived) == first["sha256"],
                    "current_stage_state": source_state,
                    "host_receipt_recorded": "HOST_FILEID_RECEIVED" in statuses,
                })
            except (OSError, ValueError, KeyError, TypeError):
                records.append({"transfer_id": folder.name, "status": "ARCHIVE_INVALID"})
        return {"records": records}
