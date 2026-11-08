# TSPAI plugin package — preparation draft

This package wraps TSPAI MCP OPEN.version 0.3.0-pre.4 for a Windows local-MCP plugin host. It is **not submitted, approved, installed, or runtime-verified on Windows by this packaging run**.

The original runtime files are preserved. The new adapter adds explicit safety annotations to the seven core tools. It does not change Windows Hello, file boundaries, request-ID handling, or local permission selection. File overwrite/deletion and arbitrary PowerShell are marked potentially destructive; arbitrary PowerShell is also open-world.

## Setup on Windows

Requires Windows x64, Python 3.11 x64 (including the Python launcher and Tkinter), Windows Hello, and a compatible desktop plugin host. Use a standard, non-elevated account.

1. Extract the package into a directory you control.
2. Choose an existing dedicated workspace containing only files you intend the plugin to access.
3. Open PowerShell in the extracted directory and run the following, replacing the example path:

```powershell
.\Setup-Plugin.ps1 -Workspace 'C:\TSPAI\workspace' -Language ja
```

The script installs the bundled Windows wheels using the original dependency hashes into a dedicated environment under `%LOCALAPPDATA%\TSPAI-MCP-Plugin`. It saves the workspace setting and keeps private runtime data separate from your workspace. Dependency installation uses --no-index and does not contact a package registry. It does not change system execution policy or install services. If your policy blocks scripts, use your organization's approved script process; the package does not bypass policy.

4. Install this local package using the host's supported desktop plugin flow. The public submission ZIP is not an install approval.
5. Start the plugin and approve Windows Hello. Its first approved session is read-only. On later starts you can select additional permissions in the existing local approval screen.
6. Stop the plugin to end its session. The default limit is one hour.

`mcp.json` starts `powershell.exe` with `Launch-Plugin.ps1`. The launcher uses the prepared Python environment and never downloads dependencies during a conversation.

## Optional PLUS1

Setup defaults PLUS1 to off. You may opt in using `-EnablePlus1` on setup. File transfer additionally requires compatible host file APIs and a separately configured connection where applicable. This package does not create a Secure MCP Tunnel, bundle credentials, or establish that PLUS1 works in every local desktop host. PLUS1 is excluded from the initial draft review cases pending host verification.

## Removal

Remove the plugin from the host and stop its process. Program files, the dedicated `%LOCALAPPDATA%\TSPAI-MCP-Plugin` directory, and the chosen workspace are separate. Removing this package alone does not erase local records or the workspace. Review any private data before removing it manually. Existing TSPAI MCP installations and their settings are separate.

## Public submission

Read [SUBMISSION-GAPS.md](SUBMISSION-GAPS.md). The ZIP is a preparation draft. It contains no claimed verified developer identity, reviewer credentials, recorded demo URL, or completed review results. The authorized publisher must supply these facts and declarations.

Product licensing and existing source validation: [LICENSE.md](LICENSE.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), and [VALIDATION.md](VALIDATION.md). This new wrapper ZIP has its own checksum and is not the signed Windows release ZIP linked in the original README.
