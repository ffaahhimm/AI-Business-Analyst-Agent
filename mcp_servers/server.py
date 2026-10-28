"""MCP adapter for the guarded local analytics tools.

The API remains usable without the optional MCP dependency. Install `mcp` and
run this module when connecting an MCP-compatible client.
"""

from app.db import schema
from app.sql_guard import run_readonly_sql

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


def build_server():
    if FastMCP is None:
        raise RuntimeError("Install the optional `mcp` package to run the MCP adapter.")
    server = FastMCP("business-analyst-tools")

    @server.tool()
    def inspect_schema() -> dict[str, dict[str, str]]:
        return schema()

    @server.tool()
    def run_readonly_sql_tool(sql: str, max_rows: int = 500) -> dict:
        result = run_readonly_sql(sql, max_rows)
        return {"result_id": result.result_id, "sql": result.sql, "rows": result.rows, "elapsed_ms": result.elapsed_ms}

    return server


if __name__ == "__main__":
    build_server().run()

