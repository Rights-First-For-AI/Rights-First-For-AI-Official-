# ChatGPT Plugin Submission — Public Preparation Record

Date: 2026-11-08 (JST)  
Publisher/project: Rights First For AI / TSPAI MCP OPEN.version  
Inspected source: [c0f931b77be4416f52a3fde364bdac19088525c1](https://github.com/Rights-First-For-AI/Rights-First-For-AI-Official-/tree/c0f931b77be4416f52a3fde364bdac19088525c1/tspai-mcp)

## Submission on hold — payment-method requirement (2026-11-08 JST)

**Current status: submission process on hold at developer verification; no plugin review submission has been completed.**

Rights First For AI attempted to proceed with ChatGPT plugin registration. The publisher reported that the portal required a verified developer identity before creating or uploading a plugin. During organization verification, the publisher received this message:

> Payment method required  
> To verify your organization, you’ll need to add a valid payment method and set it as your default payment method.

This is a publisher-provided transcription of the displayed message. It was not independently observed in an authenticated dashboard during this documentation update.

Rights First For AI has placed the application process on hold because registration of a payment method was required before proceeding, and a no-cost verification/submission path has not been confirmed. The publisher will consider proceeding only if the process can be completed free of charge. Registration in OpenAI's directory is optional for this project; GitHub distribution continues independently.

### What was checked

- [OpenAI's submission guide](https://developers.openai.com/plugins/deploy/submission) requires a verified individual or business publishing identity.
- [App Developer Terms, section 7.8](https://openai.com/policies/developer-apps-terms/) (page dated September 28, 2026, checked November 8, 2026 JST) states that minor charges may arise in verification, compliance, or related administrative processes, and reserves the right to introduce future submission/publication fees with advance notice.
- The examined materials do not establish why this particular verification flow required a payment method, whether this publisher would actually be charged, or any applicable amount. **Requiring a payment method is not evidence that a plugin submission fee has been charged or that a paid subscription must be purchased.**

The reported prompt occurred in the developer/organization-verification stage. No submission case ID, acceptance, rejection, actual charge, or charge amount has been confirmed in this record. Other previously recorded preparation and eligibility items remain unresolved; this hold is the publisher's decision, not an OpenAI review rejection.

### 日本語での公開記録

**当社はChatGPTのプラグイン登録を進めようとしましたが、申請に必要な開発者認証の段階で、有効な支払い方法の登録と既定の支払い方法への設定を求められたため、申請手続きを保留しました。**

支払い方法が求められた理由、この手続きで当社に実際の請求が発生するか、請求額はいくらかは確認できていません。公式規約には認証等に少額の費用が生じる可能性の記載がありますが、これをもって「プラグイン申請が有料」「当社に請求が発生した」とは断定しません。

当社は無料で完了できる条件を確認できた場合に申請を検討します。OpenAIへの登録は任意であり、GitHubでの公開・配布は継続します。現状は審査提出前の保留で、審査不承認を受けたという意味ではありません。


## Initial assessment status

**The following initial assessment and preparation entries are retained as history. No review submission, acceptance, rejection, or OpenAI endorsement is recorded.**

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

## Initial next decision (superseded by the hold above)

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

## Package preparation update — 2026-11-08 JST

The tables above preserve the initial assessment of source commit c0f931b77be4416f52a3fde364bdac19088525c1. A separate plugin preparation package has now been built from that runtime:

- Plugin/package identity: `tspai` / `0.1.0`; proposed directory display name: TSPAI.
- Archive: `TSPAI-ChatGPT-Plugin-0.1.0-DRAFT.zip` (16,659,338 bytes).
- SHA-256: `030fa2d7ea55e7278673c5d9cbd2afb777ce2d414a4d7a93027a3aee9d267672`.
- Portable manifests, Windows setup/launch scripts, an annotation adapter, support page, draft listing, five positive cases and three negative cases are included.
- All 30 locked Windows dependency wheels are bundled; Python 3.11 x64 remains a prerequisite.
- Seven core tools and their annotations were checked with MCP SDK 1.30.0 in a Linux process. Manifest schema checks, offline wheel/hash checks, original-source hash preservation, fixture checks and ZIP inspection passed.
- Clean Windows desktop installation, Windows Hello, live plugin review cases, recorded demonstration, confirmed publishing identity/countries/commerce declarations, local-MCP eligibility and legal attestations remain incomplete.

Source: [plugin manifest](../tspai-mcp/plugin.json), [MCP manifest](../tspai-mcp/mcp.json), [setup instructions](../tspai-mcp/PLUGIN-README.md), [remaining requirements](../tspai-mcp/SUBMISSION-GAPS.md), [validation scope](../tspai-mcp/PLUGIN-VALIDATION.md), [reproducible build script](../scripts/build_tspai_plugin.py).

**Outcome: preparation ZIP created; not uploaded, installed, submitted, approved or rejected.** No new hosted relay or additional hosting-provider dependency was introduced.
