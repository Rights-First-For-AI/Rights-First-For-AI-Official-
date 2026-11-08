"""Plugin adapter for the unchanged TSPAI MCP OPEN.version runtime.

Adds explicit MCP safety annotations; permissions and execution stay in server.py.
"""
from pathlib import Path
import inspect
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
import server as runtime

ANNOTATIONS = {
    "tspai_file_read": (True, False, False),
    "tspai_file_list": (True, False, False),
    "tspai_file_write": (False, True, False),
    "tspai_file_delete": (False, True, False),
    "tspai_powershell_probe": (True, False, False),
    "tspai_powershell_execute": (False, True, True),
    "tspai_powershell_session_status": (True, False, False),
}


class PluginFastMCP(FastMCP):
    def add_tool(self, fn, *args, **kwargs):
        # Bind against the SDK signature so positional and keyword callers work.
        bound = inspect.signature(FastMCP.add_tool).bind(self, fn, *args, **kwargs)
        name = bound.arguments.get("name") or fn.__name__
        if bound.arguments.get("annotations") is None and name in ANNOTATIONS:
            read_only, destructive, open_world = ANNOTATIONS[name]
            bound.arguments["annotations"] = ToolAnnotations(
                readOnlyHint=read_only,
                destructiveHint=destructive,
                openWorldHint=open_world,
            )
        return FastMCP.add_tool(*bound.args, **bound.kwargs)


def main():
    runtime.FastMCP = PluginFastMCP
    return runtime.main()


if __name__ == "__main__":
    raise SystemExit(main())
