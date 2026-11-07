# Frequently asked questions

[日本語](FAQ.ja.md)

## What does TSPAI MCP OPEN.version do?

It connects a Windows PC to a compatible Model Context Protocol (MCP) client. You choose the permissions on Windows and approve the session with Windows Hello. OPEN.version is one implementation within the wider TSPAI initiative.

## Which devices and software do I need?

Use a Windows x64 PC with Python 3.11, Windows Hello, and an MCP client that supports stdio. The first approved session can list and read files in your chosen workspace. Later sessions can allow additional operations you select.

## Do I need ChatGPT or a Secure MCP Tunnel?

A compatible local stdio client can use the core tools on your PC. To use PLUS1 with ChatGPT, you need a compatible ChatGPT plugin environment and a Secure MCP Tunnel you configure yourself. Availability depends on your account and permissions.

## Where do I get OPEN.version, and does it cost anything?

TSPAI MCP and TSPAI are free of charge from Rights First For AI. Get OPEN.version source and the bilingual Windows ZIP from the official GitHub release linked in the README. Rights First For AI does not require your name or email address to obtain public source. External services may charge separately. Supported routes may work with a ChatGPT Free account, but account eligibility and features vary. ORIGINAL.version is private, with phased public publication planned.

## How do I check a signed Windows ZIP?

If a signed Windows ZIP is attached to a GitHub Release, verify it before extraction using the verifier and release public key identified in the [verification guide](VERIFY.md).

## Can I modify, redistribute, or sell a copy?

The [license](LICENSE.md) permits use, modification, sale, resale, and redistribution under its terms and applicable law. Identify the original project and the distributor, and disclose material modifications. You may create independent or AI-generated branding and may retain original artwork for truthful identification. Do not falsely present a third-party copy as an official Rights First For AI release or imply its endorsement. Check the official GitHub repository and any published hashes or signatures to verify an official release.

## What happens when I use PLUS1?

Choose a staged file and select Upload to send it to ChatGPT. The local limit is 20,000,000 bytes per file. Acceptance can depend on file type, account, and host capabilities. Windows keeps a transfer record and local copy. Check the file on your device separately after ChatGPT accepts it.

## What if the ChatGPT connection or upload fails?

The core Windows stdio tools and optional PLUS1 ChatGPT transfer use different connection paths. A host error or rate limit (including HTTP 429) does not prove that a file reached ChatGPT. Check the host acceptance status and your Windows transfer records before retrying. If the result of a write, upload, or command is unknown, inspect it first and do not blindly repeat the action. See [Security](SECURITY.md) for request-ID safety.

## What does the file deletion permission do?

After the first approved session, enabling file deletion allows the client to delete individual files and empty folders in the configured workspace. The file tool performs deletion directly and does not send items to the Recycle Bin. To remove OPEN.version itself, see [Uninstall](INSTALL.md#5-uninstall).

## What should I know before enabling PowerShell?

PowerShell runs with your Windows account's permissions. It can access files and the network outside the configured workspace. Enable it only for sessions that require it.
