# Security and vulnerability reporting

[日本語](SECURITY.ja.md)

- Windows Hello approves a time-limited session. The chosen permissions apply for that session. Stopping the server or reaching the time limit blocks new operations. Effects of completed commands persist.
- File tools operate in the configured workspace. If you enable PowerShell, it runs with your Windows account's permissions and can access resources outside that workspace, including the network. Enable only the permissions you need.
- Use private workspace, data, and PLUS1 staging folders. Keep real configuration values, credentials, logs, and transfer copies outside public repositories and shared folders.
- If a connection fails and the outcome of an operation is uncertain, inspect its result before retrying. For a retry of the same operation, reuse the same request ID and arguments.
- If you download a signed Windows ZIP from GitHub Releases, [verify it](VERIFY.md) before extraction.

Report vulnerabilities privately to [contact@rightsfirst-ai.jp](mailto:contact@rightsfirst-ai.jp). Include the version, a description, and reproduction steps with secrets and personal data removed.

See [Privacy](PRIVACY.md) for storage and transfer details.
