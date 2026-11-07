"""Sign or independently verify official ZIP contents without extracting them."""
import argparse
from hashlib import file_digest
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
from zipfile import BadZipFile, ZipFile, ZipInfo

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


ROOT = "TSPAI-MCP-OPEN/"
MANIFEST = ROOT + "RELEASE-FILES.json"
SIGNATURE = ROOT + "RELEASE-FILES.sig"
RELEASE_FILES = {MANIFEST, SIGNATURE}
ISSUANCE_FILES = {ROOT + name for name in
                  ("DISTRIBUTION-RECEIPT.json", "DISTRIBUTION-RECEIPT.sig", ".tspai-origin")}
MAX_BYTES = 64 * 1024 * 1024
MAX_FILES = 256
MAX_MANIFEST_BYTES = 128 * 1024
CONTEXT = b"TSPAI-MCP-release-files-v1\x00"


def index_files(archive):
    entries = archive.infolist()
    if len(entries) > MAX_FILES or sum(entry.file_size for entry in entries) > MAX_BYTES:
        raise ValueError("ZIP contents exceed review limits")
    indexed = {}
    folded = set()
    for entry in entries:
        name = entry.filename
        parts = name.removeprefix(ROOT).split("/")
        invalid = any(not re.fullmatch(r"[A-Za-z0-9._-]+", part) or part.endswith(".")
                      or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])", part.split(".")[0])
                      for part in parts)
        mode = stat.S_IFMT(entry.external_attr >> 16)
        if (not name.startswith(ROOT) or invalid or name.casefold() in folded
                or name != entry.orig_filename or mode not in (0, stat.S_IFREG)):
            raise ValueError(f"Unsafe or ambiguous ZIP entry: {name!r}")
        folded.add(name.casefold())
        indexed[name] = entry
    return indexed


def sha256_of(archive, entry):
    with archive.open(entry) as stream:
        return file_digest(stream, "sha256").hexdigest()


def read_zip(path: Path):
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or not data.startswith(b"PK\x03\x04"):
        raise ValueError("Expected an ordinary ZIP within the review size limit")
    return data


def sign_zip(path: Path, version: str, key: Ed25519PrivateKey) -> bytes:
    if not re.fullmatch(r"[0-9][A-Za-z0-9.-]{0,63}", version):
        raise ValueError("Invalid release version")
    output = BytesIO(read_zip(path))
    with ZipFile(output, "a") as archive:
        files = index_files(archive)
        if (not files or len(files) > MAX_FILES - len(RELEASE_FILES | ISSUANCE_FILES)
                or files.keys() & (RELEASE_FILES | ISSUANCE_FILES)):
            raise ValueError("Expected an unsigned base ZIP with room for release records")
        manifest = json.dumps({"version": version, "files": {
            name: sha256_of(archive, entry) for name, entry in files.items()
        }}, sort_keys=True, separators=(",", ":")).encode("ascii")
        if (len(manifest) > MAX_MANIFEST_BYTES
                or sum(entry.file_size for entry in files.values()) + len(manifest) + 64 > MAX_BYTES):
            raise ValueError("Signed ZIP contents exceed review limits")
        archive.writestr(ZipInfo(MANIFEST), manifest)
        archive.writestr(ZipInfo(SIGNATURE), key.sign(CONTEXT + manifest))
    signed = output.getvalue()
    if len(signed) > MAX_BYTES:
        raise ValueError("Signed ZIP exceeds the review size limit")
    return signed


def verify_zip(path: Path, public_key: Ed25519PublicKey):
    return verify_zip_bytes(read_zip(path), public_key)


def verify_zip_bytes(data: bytes, public_key: Ed25519PublicKey):
    if len(data) > MAX_BYTES or not data.startswith(b"PK\x03\x04"):
        raise ValueError("Expected an ordinary ZIP within the review size limit")
    with ZipFile(BytesIO(data)) as archive:
        files = index_files(archive)
        if (not RELEASE_FILES <= files.keys() or files[MANIFEST].file_size > MAX_MANIFEST_BYTES
                or files[SIGNATURE].file_size != 64):
            raise ValueError("Release manifest or signature is missing or invalid")
        manifest = archive.read(files[MANIFEST])
        public_key.verify(archive.read(files[SIGNATURE]), CONTEXT + manifest)
        record = json.loads(manifest)
        if (not isinstance(record, dict) or set(record) != {"version", "files"}
                or not isinstance(record["version"], str) or not isinstance(record["files"], dict)):
            raise ValueError("Invalid signed release manifest")
        issuance = ISSUANCE_FILES & files.keys()
        if issuance and issuance != ISSUANCE_FILES:
            raise ValueError("Distribution records are incomplete")
        expected = record["files"]
        if not expected or expected.keys() != files.keys() - RELEASE_FILES - issuance:
            raise ValueError("ZIP file set differs from the signed release")
        for name, digest in expected.items():
            if sha256_of(archive, files[name]) != digest:
                raise ValueError(f"Release file differs from its signed hash: {name}")
        return {"version": record["version"], "verified_files": len(expected),
                "distribution_records": "present_not_verified" if issuance else "absent"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    sign = commands.add_parser("sign")
    sign.add_argument("archive", type=Path)
    sign.add_argument("output", type=Path)
    sign.add_argument("version")
    verify = commands.add_parser("verify")
    verify.add_argument("archive", type=Path)
    verify.add_argument("trusted_public_key_hex")
    args = parser.parse_args()
    try:
        if args.operation == "sign":
            key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(os.environ["TSPAI_RELEASE_SIGNING_KEY"]))
            signed = sign_zip(args.archive, args.version, key)
            result = verify_zip_bytes(signed, key.public_key())
            with args.output.open("xb") as stream:
                stream.write(signed)
        else:
            key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(args.trusted_public_key_hex))
            result = verify_zip(args.archive, key)
    except InvalidSignature:
        parser.exit(1, "Release signature verification failed\n")
    except (BadZipFile, KeyError, OSError, NotImplementedError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"Release verification error: {exc}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
