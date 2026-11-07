# Install on Windows

[日本語](INSTALL.ja.md)

## 1. Verify and prepare

Choose the tag for the version you want in this GitHub repository. Clone the repository and check out that tag, or download its source archive. If you choose a signed Windows ZIP attached to the GitHub Release, follow [Verify the official ZIP](VERIFY.md) **before extracting it**. Use a standard Windows account with Windows Hello and Python 3.11.

In the extracted product directory, or the source checkout's `tspai-mcp` subdirectory, open PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements-windows.lock.txt
.\.venv\Scripts\python.exe -m pip check
.\Start-MCP.ps1 -Check
```

For a source checkout, `-Check` checks local file hashes and Python imports. Use the separate signature verification procedure before extracting a signed Windows ZIP.

## 2. Connect and authorize

1. Create a dedicated workspace folder. Replace the Python, server, and workspace paths in `mcp-config.example.json` with your own absolute paths.
2. Register the example with a compatible stdio MCP client. On Windows, review the permissions and approve with Windows Hello. The first approved session permits listing and reading only.
3. Test with a file you placed in the dedicated workspace. For additional permissions, stop the server in the client, restart it, and choose the permissions on Windows.
4. Stop the server in the client when finished. The default session is one hour and the configurable maximum is 12 hours. The server rejects new operations after expiration.

To display the startup summary in Japanese, add `--language`, `ja` to the client arguments or pass `-Language ja` to `Start-MCP.ps1`.

## 3. Optional PLUS1 transfer

After the first approved session, add `--enable-plus1` to the stdio command or pass `-EnablePlus1` to the PowerShell launcher. Check the Windows approval screen before proceeding.

1. Set up your own [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) with a compatible ChatGPT plugin environment. Keep credentials in your own environment.
2. Put only files you intend to share under `%LOCALAPPDATA%\TSPAI-MCP-Open\plus1\approved-for-transfer`. If you configured `--data-dir`, use its `plus1\approved-for-transfer` subdirectory.
3. Open the PLUS1 panel, select a file, and choose **Upload to ChatGPT**. When ChatGPT accepts the file, use the save control and confirm it exists on your device.
4. After changing server tools or panel resources, refresh the ChatGPT plugin and open a new conversation if the previous panel is cached. An expired tunnel runtime key must be replaced in the tunnel's own credential setup; Windows Hello approval does not renew that key.
5. Start with a small test file. The local limit is 20,000,000 bytes. File type and account support depend on the ChatGPT host.

## 4. Update or roll back

Keep the previous directory and prepare the new version in a separate, unused directory. Verify any signed Windows ZIP before extracting it. Run the checks above with the new copy. Stop the old server and point the client at the new Python and server paths. To roll back, stop the server and restore the previous paths. Your operation records and PLUS1 copies are stored separately in the user data directory.

Apply any local modifications yourself after comparing the releases. Official updates do not merge changes into a modified copy.

## 5. Uninstall

Stop the server and remove its entry from your MCP client. Then remove the OPEN.version program directory you created at installation. Operation records and PLUS1 copies are stored separately in `%LOCALAPPDATA%\TSPAI-MCP-Open`, or in the directory you supplied with `--data-dir`. Review that directory before removing any data you no longer need. Your configured workspace is separate from the uninstall steps.
