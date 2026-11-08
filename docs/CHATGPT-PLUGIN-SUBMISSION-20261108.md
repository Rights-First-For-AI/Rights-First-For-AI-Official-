# ChatGPT Plugin Submission — Public Preparation Record

Date: 2026-11-08 (JST)  
Publisher/project: Rights First For AI / TSPAI MCP OPEN.version  
Inspected source: [c0f931b77be4416f52a3fde364bdac19088525c1](https://github.com/Rights-First-For-AI/Rights-First-For-AI-Official-/tree/c0f931b77be4416f52a3fde364bdac19088525c1/tspai-mcp)

## Status

**Pre-submission assessment. No submission, acceptance, rejection, or OpenAI endorsement is recorded.**

The publisher has authorized checking eligibility, proceeding with submission if applicable requirements are satisfied, and publishing a factual record of the process and outcome. GitHub distribution is already available and continues independently of any directory decision.

This is a scoped review of the published source and documentation, not a complete policy, security, or legal assessment. No authenticated Platform dashboard eligibility check was performed.

## Observed public implementation

| Item | Evidence |
| --- | --- |
| Published release | README identifies Windows prerelease `0.3.0-pre.4` and links the release. |
| Main transport | `server.py` imports and starts `stdio_server`; `mcp-config.example.json` launches a local Python process. |
| Optional ChatGPT transfer | `INSTALL.md` instructs users to configure their own Secure MCP Tunnel for PLUS1. |
| Authorization | Source and security documentation describe Windows Hello and time-limited, locally chosen session permissions. PowerShell is disabled by default; when enabled, it uses the Windows account's permissions. |
| Public supporting material | README, installation instructions, privacy statement, license and terms, security reporting instructions, validation record, and icon files are present. Their presence does not establish submission compliance. |
| Submission package | No `plugin.json` or root portable `mcp.json` exists in the inspected repository tree. The MCP client configuration example is not a directory-submission manifest. |
| Validation | `VALIDATION.md` records specific Windows and ChatGPT transfer tests and their limitations. This assessment did not rerun them. |

## Applicable official requirements

1. **Local MCP submission:** OpenAI documents a desktop-only route for local MCP plugins, limited to approved partners whose submitting organization has been allowlisted. The publisher's eligibility and allowlist status have not been verified.
2. **Secure MCP Tunnel:** OpenAI documents private connections and development testing, but explicitly excludes public plugin submission/distribution through the tunnel alone.
3. **Remote alternative:** A remote submission requires a stable public HTTPS MCP endpoint. A product webpage hosted over HTTPS does not by itself establish that an eligible MCP endpoint exists. No new hosting or relay deployment has been authorized or performed in this assessment.

The existing local implementation is therefore not established as ready for a standard remote-MCP submission. This is a preparation/eligibility gap, not a review rejection or a finding that the publisher is prohibited from applying.

## Preparation checklist

| Preparation item | Current status / required evidence |
| --- | --- |
| Local-MCP partner eligibility and organization allowlisting | Unverified; confirm through the authorized publisher's OpenAI Platform account / OpenAI representative. |
| Verified publishing identity | Unverified; check individual or business verification and the actual directory display name. |
| Submission permissions | Unverified in Platform. GitHub repository permissions do not establish Platform submission permissions. |
| Portable submission ZIP | Not prepared; requires the correct submission path and manifests, bundled assets, version, and validation. |
| Listing details | Draft and validate supported behavior, name, subtitle, category, limitations, and starter prompts. Check the guideline restricting appended “MCP”, “MCP Server”, or “Plugin” in listing names. |
| Four listing URLs | Product, support, privacy, and terms URLs must be selected, checked for public accessibility, and assessed for actual coverage. Existing GitHub documents are inputs; no finding of their inadequacy is made here. |
| Review evidence | Prepare the applicable five positive and three negative cases; mark actual run results separately from drafts. Existing validation records are supporting evidence, not proof that a directory review test suite has run. |
| Recorded demonstration and reviewer access | Verify an actual working recording URL and a suitable review environment for the chosen path. A promotional/explanatory video alone is not evidence of the submitted version's real operation. |
| Tool annotations and behavior | Complete a tool-by-tool review of explicit annotations, schemas, permission boundaries, and effects against current guidelines. Not completed by this scoped assessment. |
| Countries, translations, commerce, release notes | Obtain the publisher's actual selections and declarations; do not infer country targeting or commerce behavior. |
| Required attestations | The authorized publisher must complete applicable current legal/policy attestations. No attestations were made during this assessment. |
| Submission outcome | Not submitted. No case ID, approval, or rejection exists in this record. |

## Next decision

Confirm whether the publisher can use the local-MCP submission path. If eligible, prepare the submission around the existing implementation. If not, document that access restriction accurately and decide whether to request eligibility; do not describe an unsubmitted package as rejected.

Do not introduce a new centralized hosting dependency solely to seek approval without a separate publisher decision.

Directory approval, if eventually obtained, means listing approval within the relevant program; it does not make this product an OpenAI-developed product.

## 日本語要約

GitHubでの公開は完了しており、ChatGPTの公開ディレクトリへの掲載申請は別の手続きです。公開版はローカルstdio MCPと利用者設定のSecure MCP Tunnelを用いる構成です。現行の公式資料では、ローカルMCP申請は承認済みパートナー・組織の事前許可が必要で、Tunnel単独は公開申請に対応しません。

当社の事前許可・公開名義の認証・申請権限は未確認です。申請用パッケージと審査資料も未整備のため、この記録時点では未申請です。不承認を受けたという意味ではありません。条件が確認できれば申請を進め、実際の状態と結果を追記します。公開申請のためだけに新しい事業者への依存を追加する決定はしていません。

## Official references checked

- [Submit desktop-only plugins](https://developers.openai.com/plugins/deploy/desktop-only)
- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [Upload and submit your plugin](https://developers.openai.com/plugins/deploy/submission)
- [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines)

Public records must exclude credentials, private PC content, and reviewer login information. Future entries must distinguish preparation, upload, submission, review decision, and publication.
