# Plugin preparation validation — 0.1.0

Date: 2026-11-08 (JST).

| Check | Result and scope |
| --- | --- |
| Published portable JSON schemas | plugin.json and mcp.json both validated against their declared Agent Plugins 1.0.0 schemas. This is not OpenAI Portal approval or submission validation. |
| Core tool registration | Seven tools registered with the bundled MCP SDK 1.30.0 wheel in a Linux Python process using host dependencies. No Windows Hello session or live PC operations were exercised. |
| Safety annotations | All seven core tools advertise the intended explicit boolean hints. Explicit annotations and positional SDK registration remain supported. |
| Windows dependency bundle | All 30 CPython 3.11 / Windows x64 wheels downloaded with the original lock's hashes. Offline pip resolution with --no-index and --require-hashes succeeded. This did not install or run Windows binaries. |
| Review fixtures | Synthetic files were created in an empty temporary directory; an attempt to reuse a nonempty directory was refused. |
| Icon assets | Existing PNGs retained: listing 512 x 512; composer 256 x 256. Both square and below 5 MiB. Listing icon visually inspected. |
| Archive | Build script verifies covered original-source hashes, wheel hashes, listing limits, manifest/reference consistency, Python syntax, case counts, and ZIP entry bytes/CRC. |
| Windows setup / PowerShell launcher | Not run; a clean Windows desktop acceptance test is still required. |
| Five positive / three negative review cases | Not run against the plugin host. The manifest contains draft cases and observable expectations, not fabricated pass results. |
| PLUS1 in a local desktop plugin host | Not run. Disabled by default. |
| Verified publisher, partner eligibility, attestations, public review | Not completed. |

The original product's separate validation record is retained in VALIDATION.md. It must not be confused with acceptance of this new plugin wrapper.
