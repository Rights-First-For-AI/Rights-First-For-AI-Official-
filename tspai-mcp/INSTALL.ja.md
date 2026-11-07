# Windowsでの導入

[English](INSTALL.md) · [日本語のトップ](README.ja.md)

## 1. 展開と依存関係の導入

公式ZIPに署名が付いている場合は、展開前に[検証手順](VERIFY.md)に従って確認してください。既存版を上書きせず、新しいフォルダーに展開します。GitHubのソースから導入する場合は、対象のリリースタグを取得します。

標準ユーザーで製品フォルダー（ソース取得時は `tspai-mcp`）を開き、PowerShellで次を実行します。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements-windows.lock.txt
.\.venv\Scripts\python.exe -m pip check
.\Start-MCP.ps1 -Check
```

`-Check` はローカルファイルのハッシュとPythonの読み込みを確認します。Windows Helloでの承認やクライアント接続は次の手順で確認します。

## 2. 日本語で接続する

1. 専用の作業フォルダーを作ります。
2. `mcp-config.example.json` のPython、`server.py`、作業フォルダーのパスをそれぞれ絶対パスに置き換えます。クライアントの引数配列に `"--language", "ja"` を追加します。PowerShellランチャーを使う場合は `-Language ja` を指定します。
3. MCPクライアントから起動し、Windows上で内容を確認してWindows Helloで承認します。初回は一覧と読み取りだけです。試験用のファイルを1つ作業フォルダーに置き、読み取れるか確認してください。
4. 追加の権限はクライアントでサーバーを停止してから再起動し、必要な項目だけを選びます。終了時もクライアントでサーバーを停止します。セッションの既定は1時間、上限は12時間です。

## 3. PLUS1で転送する場合

初回承認を終えた後、`--enable-plus1`（ランチャーでは `-EnablePlus1`）を指定し、利用者自身のSecure MCP Tunnelと対応するChatGPT環境を使います。資格情報は自分の環境で管理してください。

送るファイルだけを `%LOCALAPPDATA%\TSPAI-MCP-Open\plus1\approved-for-transfer` に置きます。`--data-dir` を指定した場合は、その下の `plus1\approved-for-transfer` を使います。PLUS1画面で対象を選んで送信し、受付後に保存操作を行って、端末上で保存を確認してください。上限は1ファイル20,000,000バイトです。

ツールや画面リソースを更新した場合はChatGPT側のプラグインを更新し、以前の画面が残る場合は新しい会話で開き直します。トンネルの実行キーが期限切れの場合は、トンネル側でキーを差し替えます。Windows Helloの承認でキーの期限は更新されません。

## 4. 更新と切り戻し

前の製品フォルダーを保ち、新版を別フォルダーで検証します。クライアントのサーバーを停止し、Pythonとサーバーのパスを新版に切り替えます。戻すときは停止して前のパスに戻します。操作記録とPLUS1のコピーは製品フォルダーと別のデータフォルダーにあります。

## 5. アンインストール

サーバーを停止し、MCPクライアントから登録を外して、導入時に作った製品フォルダーを取り除きます。操作記録とPLUS1のコピーは `%LOCALAPPDATA%\TSPAI-MCP-Open` または `--data-dir` の指定先にあります。不要なデータを取り除く場合は、その中身を確認してから操作してください。
