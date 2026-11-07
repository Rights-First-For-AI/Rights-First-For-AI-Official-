# TSPAI MCP OPEN.version

[日本語](README.ja.md)

## Our Vision — Beyond TSPAI MCP

**TSPAI Will Change the World.**

**TSPAI MCP is only one part of a much broader TSPAI vision.** Triple Star Protocol (TSP) provides the guiding principles; TSPAI is the broader initiative built around those principles; and TSPAI MCP OPEN.version is the Windows implementation provided here.

Learn more about the initiative and its principles at the [official Rights First For AI website](https://www.rightsfirst-ai.jp/) and the [TSPAI MCP official introduction](https://www.rightsfirst-ai.jp/tspai-mcp-en.html) ([日本語](https://www.rightsfirst-ai.jp/tspai-mcp-ja.html)).

## About this release

TSPAI MCP OPEN.version connects a Windows PC to a compatible Model Context Protocol (MCP) client. Rights First For AI develops this technical release independently; it is not produced or endorsed by OpenAI. The Windows user chooses which operations to enable and confirms the session with Windows Hello.

- List and read files in a dedicated workspace. The first approved session is read-only.
- On later starts, you can separately enable file creation, editing, deletion, or PowerShell. File deletion applies to individual files and empty folders in the configured workspace.
- Use optional PLUS1 to select a staged file and send it to ChatGPT. The local limit is 20,000,000 bytes per file. Acceptance depends on the ChatGPT account, host capabilities, and file type.
- Review operation and transfer records on Windows.

**Requirements** Windows x64, Python 3.11, Windows Hello, and a compatible stdio MCP client. PLUS1 also requires a compatible ChatGPT plugin environment and a connection configured by the user.

## Get OPEN.version

**Version: 0.3.0-pre.4 — Windows prerelease.** Get the full source and the English/Japanese Windows ZIP from the [official GitHub release](https://github.com/Rights-First-For-AI/Rights-First-For-AI-Official-/releases/tag/v0.3.0-pre.4). Verify the signed ZIP before extraction. This is an early technical release; see [validation and limits](VALIDATION.md).

**Price:** TSPAI MCP and TSPAI are free of charge from Rights First For AI. External services may charge separate fees, and compatible ChatGPT connections/features depend on the account and service. ORIGINAL.version is currently private, with a phased public release planned. Rights First For AI does not require your name or email address to obtain its public source.

[Installation](INSTALL.md) · [Verify the official ZIP](VERIFY.md) · [Security](SECURITY.md) · [FAQ](FAQ.md) · [Release notes](CHANGELOG.md)

[License and terms](LICENSE.md) · [Logo policy](TRADEMARK_POLICY.md) · [Privacy](PRIVACY.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)
