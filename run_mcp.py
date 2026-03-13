from src.core.mcp_server import mcp

if __name__ == "__main__":
    print("🚀 Starting MCP server over stdio wrapper...")
    mcp.run("stdio")
