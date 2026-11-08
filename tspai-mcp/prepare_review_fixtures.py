"""Create synthetic review files in an explicitly selected empty directory."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory
    if not root.is_absolute() or not root.is_dir():
        parser.error("Choose an existing absolute empty directory")
    if any(root.iterdir()):
        parser.error("Refusing to write fixtures into a nonempty directory")
    values = {
        "welcome.txt": b"TSPAI review sample.\n",
        "replace-me.txt": b"Before review.\n",
    }
    for name, data in values.items():
        (root / name).write_bytes(data)
    print(json.dumps({
        "workspace": str(root.resolve()),
        "files": {name: {"sha256": hashlib.sha256(data).hexdigest(),
                         "bytes": len(data)} for name, data in values.items()}
    }, indent=2))


if __name__ == "__main__":
    main()
