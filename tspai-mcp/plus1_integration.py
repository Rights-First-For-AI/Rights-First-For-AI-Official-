"""Register the opt-in PLUS1 transfer widget and scoped MCP tools."""
import json
from pathlib import Path

from mcp.types import ToolAnnotations, CallToolResult, TextContent

import bridge_chunked_store as store
import transfer_ledger as ledger

UI_URI = "ui://tspai/open-plus1-transfer.html"
JA_UI_URI = "ui://tspai/open-plus1-transfer-ja.html"
MODEL_META = {"ui": {"visibility": ["model", "app"]}}
APP_META = {"ui": {"visibility": ["app"]}}
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, openWorldHint=False
)
LOCAL_WRITE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, openWorldHint=False
)


def attach_plus1(server, executor, staging_root, *, language="en"):
    """Register transfer tools for the current authenticated session."""
    store.ROOT = staging_root
    store.APPROVED = staging_root / "approved-for-transfer"
    widget_path = Path(__file__).resolve().parent / "bridge_chunked_widget.html"

    ui_uri = JA_UI_URI if language == "ja" else UI_URI
    ui_meta = {"ui": {"resourceUri": ui_uri, "visibility": ["model", "app"]}}

    def require_active():
        if executor.status().get("active") is not True:
            raise PermissionError("Active local session required for PLUS1")

    def catalog():
        require_active()
        return {
            "files": store.list_staged(),
            "max_file_bytes": store.MAX_FILE_BYTES,
            "chunk_bytes": store.CHUNK_BYTES,
        }

    @server.tool(
        name="bridge_open_transfer_widget", annotations=READ_ONLY, meta=ui_meta, structured_output=True
    )
    def bridge_open_transfer_widget() -> dict[str, object]:
        """Open the owner-selected transfer UI (requires explicit user click)."""
        return catalog()

    @server.tool(
        name="bridge_list_staged_chunked", annotations=READ_ONLY, meta=MODEL_META, structured_output=True
    )
    def bridge_list_staged_chunked() -> dict[str, object]:
        """List only files explicitly staged for transfer; owner session required."""
        return catalog()

    @server.tool(
        name="bridge_read_chunk_private", annotations=READ_ONLY, meta=APP_META, structured_output=False
    )
    def bridge_read_chunk_private(file_id: str, index: int, transfer_id: str) -> CallToolResult:
        """Read a staged file chunk for the app only, never request as model text."""
        require_active()
        result = ledger.read_chunk(transfer_id, file_id, index)
        # Keep raw file bytes out of model-facing result fields.
        public = {
            "transfer_id": transfer_id,
            "file_id": result["file_id"],
            "filename": result["filename"],
            "size": result["size"],
            "sha256": result["sha256"],
            "index": result["index"],
            "chunk_count": result["chunk_count"],
            "chunk_size": result["chunk_size"],
            "chunk_sha256": result["chunk_sha256"],
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(public, ensure_ascii=False))],
            structuredContent=public,
            _meta={"tspai/private_chunk_data": {"encoding": "base64", "data": result["data"]}},
            isError=False,
        )
    @server.tool(
        name="bridge_prepare_transfer", annotations=LOCAL_WRITE,
        meta=APP_META, structured_output=True
    )
    def bridge_prepare_transfer(file_id: str) -> dict[str, object]:
        """Save SHA-verified source snapshot and local audit entry before upload."""
        require_active()
        return ledger.prepare(file_id)

    @server.tool(
        name="bridge_transfer_receipt", annotations=LOCAL_WRITE,
        meta=APP_META, structured_output=True
    )
    def bridge_transfer_receipt(
        transfer_id: str, file_id: str, outcome: str, host_file_id: str = ""
    ) -> dict[str, object]:
        """Record host file receipt or owner-reported save; no inferred delivery."""
        require_active()
        return ledger.receipt(transfer_id, file_id, outcome, host_file_id)

    @server.tool(
        name="bridge_report_transfer_failure", annotations=LOCAL_WRITE,
        meta=APP_META, structured_output=True
    )
    def bridge_report_transfer_failure(
        file_id: str, transfer_id: str = "", phase: str = "upload",
        code: str = "TRANSFER_ERROR", reason: str = "",
        response_shape: str = ""
    ) -> dict[str, object]:
        """Journal sanitised failure stage, host reason and response shape."""
        require_active()
        return ledger.report_failure(
            file_id, transfer_id, phase, code, reason, response_shape
        )

    @server.tool(
        name="bridge_list_transfer_records", annotations=READ_ONLY,
        meta=APP_META, structured_output=True
    )
    def bridge_list_transfer_records() -> dict[str, object]:
        """List local transfer history and source/sent copy integrity statuses."""
        require_active()
        return ledger.history()

    @server.resource(
        ui_uri, name="TSPAI MCP PLUS1 transfer",
        mime_type="text/html;profile=mcp-app"
    )
    def plus1_ui() -> str:
        document = widget_path.read_text(encoding="utf-8")
        if language == "ja":
            return document.replace('<html lang="en">', '<html lang="ja">', 1)
        return document

    return server
