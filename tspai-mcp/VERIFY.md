# Verify a signed Windows ZIP before extraction

Use the verifier and pinned Python dependencies from the official repository at tag v0.3.0-pre.4, in its tspai-mcp subdirectory. Obtain release-public-key.hex from that trusted source, separately from the downloaded ZIP. A key found only inside an unverified ZIP is not a trusted identity.

In the trusted source directory, open PowerShell:

```powershell
py -3.11 -m venv .verify
.\.verify\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements-windows.lock.txt
$key = (Get-Content .elease-public-key.hex -Raw).Trim()
$zip = Read-Host 'Path to downloaded ZIP'
.\.verify\Scripts\python.exe .elease_integrity.py verify $zip $key
if ($LASTEXITCODE -ne 0) { throw 'ZIP verification failed. Do not extract it.' }
```

Check that the reported version is 0.3.0-pre.4. Extract into a new folder only after verification succeeds. The verifier checks the signed release manifest and every covered file without running code from the ZIP.

The release also supplies a .sha256 file for checking transport integrity. A hash alone does not establish who published a file.
