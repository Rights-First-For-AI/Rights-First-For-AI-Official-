# Bundled dependency wheels

The prepared plugin ZIP includes all 30 Windows x64 / CPython 3.11 wheels from the original hash-locked requirements. Setup verifies their hashes with pip and uses --no-index, so it does not download packages during installation.

The wheel binaries are build inputs rather than repository source. To reproduce the bundle, run from the repository root:

```bash
python3 -m pip download --require-hashes --only-binary=:all: --platform win_amd64 --python-version 311 --implementation cp --abi cp311 -r tspai-mcp/requirements-windows.lock.txt --dest tspai-mcp/vendor/wheels
```

Then run the build script. Python 3.11 x64 itself is a user prerequisite and is not bundled.

Third-party licenses and notices remain in each wheel and in the accompanying THIRD_PARTY_NOTICES.md.
