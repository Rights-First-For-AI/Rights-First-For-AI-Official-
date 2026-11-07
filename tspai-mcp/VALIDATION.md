# Validation and limits — 0.3.0-pre.4

Validated on the developer's Windows x64 PC with Python 3.11.9, Windows Hello, and the locked Python dependencies.

- Real ChatGPT PLUS1 tunnel: two 20,000,000-byte TXT transfers accepted by the host on November 8, 2026 JST. Each transfer used 77 chunks through `_meta` only. Source, staged, and sent copies matched SHA-256.
- The owner confirmed saving the received file to the desktop. The downloaded copy's hash was not independently measured.
- The temporary test route was switched back to the existing connection and the original tools responded. This test does not establish every possible failure-recovery scenario.
- English/Japanese widget simulations passed at the size limit. Corrupted chunks, missing metadata, and model-visible-only chunk bytes were rejected.
- The MCP Apps initialization repair was checked in a browser and then in the real ChatGPT transfer above.
- Authentication cancellation and first-session read-only behavior were checked in the preceding Windows acceptance tests.

Final assembly also checks file hashes, a clean ZIP extraction, English/Japanese import checks, and signature verification with rejection of a wrong key and a modified covered file.

This is a Windows prerelease. A separate third-party PC, macOS, Linux, all ChatGPT accounts, and all file types have not been verified. PLUS1 requires compatible host file APIs and a user-configured connection. There is no claim of OpenAI endorsement or guaranteed service availability.
