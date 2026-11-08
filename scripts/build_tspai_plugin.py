"""Build and inspect the TSPAI local-plugin preparation ZIP."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import zipfile

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "tspai-mcp"
    plugin = json.loads((root / "plugin.json").read_text())
    mcp = json.loads((root / "mcp.json").read_text())
    assert plugin["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert mcp["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    assert re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", plugin["name"])
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
    extension = plugin["extensions"]["com.openai"]
    listing = extension["interface"]
    assert 0 < len(listing["displayName"]) <= 30
    assert 0 < len(listing["shortDescription"]) <= 30
    assert 0 < len(listing["longDescription"]) <= 4000
    assert listing["category"] == "Productivity"
    assert extension["requires_local_executor"] is True
    assert "developerName" not in listing  # Still awaiting verified identity.
    assert "apps" not in plugin and "apps" not in extension
    assert not (root / ".app.json").exists()
    prompts = listing["defaultPrompt"]
    assert len(prompts) <= 3 and len(set(prompts)) == len(prompts)
    assert all(0 < len(p) <= 128 and "\n" not in p for p in prompts)
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        assert listing[key].startswith("https://") and len(listing[key]) <= 1024
    for key in ("logo", "composerIcon"):
        path = (root / listing[key]).resolve()
        assert path.is_relative_to(root.resolve())
        with Image.open(path) as icon:
            assert icon.format == "PNG"
            assert icon.width == icon.height and icon.width >= 48
        assert path.stat().st_size <= 5 * 1024 * 1024
    cases = extension["review"]["test_cases"]
    assert len(cases["positive"]) == 5 and len(cases["negative"]) == 3
    for case in cases["positive"]:
        assert all(isinstance(case[k], str) and case[k].strip()
                   for k in ("description", "prompt", "tools_triggered", "expected_behavior"))
    for case in cases["negative"]:
        assert all(isinstance(case[k], str) and case[k].strip() for k in ("description", "prompt"))
    server = mcp["mcpServers"]["tspai-local"]
    assert server["type"] == "stdio" and server["command"] == "powershell.exe"
    assert server["cwd"] == "${PLUGIN_ROOT}"
    assert "${PLUGIN_ROOT}/Launch-Plugin.ps1" in server["args"]
    assert "url" not in server and "headers" not in server
    source_hashes = json.loads((root / "SHA256SUMS.json").read_text())
    for name, expected in source_hashes.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    wheel_files = list((root / "vendor" / "wheels").glob("*.whl"))
    locked_hashes = set(re.findall(r"sha256:([0-9a-f]{64})", (root / "requirements-windows.lock.txt").read_text()))
    assert len(wheel_files) == 30 and len(locked_hashes) == 30
    actual_wheel_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in wheel_files}
    assert actual_wheel_hashes == locked_hashes
    for path in root.rglob("*.py"):
        if "__pycache__" not in path.parts:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    omitted = {".git", ".venv", "__pycache__", "node_modules"}
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and not any(part in omitted for part in p.relative_to(root).parts)
                   and p.suffix != ".pyc")
    output = args.output.resolve()
    assert not output.is_relative_to(root.resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(2026, 11, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert "plugin.json" in names and "mcp.json" in names
        assert ".app.json" not in names
        assert len(names) == len(set(names))
        for name in names:
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
        assert json.loads(archive.read("plugin.json")) == plugin
        for path in files:
            assert archive.read(path.relative_to(root).as_posix()) == path.read_bytes()
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n")
    print(json.dumps({"archive": str(output), "bytes": output.stat().st_size,
                      "sha256": digest, "files": len(files),
                      "original_hashes_verified": len(source_hashes),
                      "status": "preparation draft; not ready to submit"}, indent=2))


if __name__ == "__main__":
    main()
