import sys
from src.core.mcp_server import mcp

if __name__ == "__main__":
    print("🚀 Starting MCP server over stdio wrapper...", file=sys.stderr)
    mcp.run("stdio")
