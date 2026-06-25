"""
MCP Filesystem Server — exposes read_file and write_file as MCP tools.
Run this as a standalone process: python mcp_servers/filesystem_server.py

Agents connect to it via the MCP Python SDK. This demonstrates the
Model Context Protocol pattern: tools are served over a standard protocol,
not hardcoded into the agent.
"""

import asyncio
import json
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("filesystem-server")
BASE_DIR = Path(__file__).parent.parent


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_file",
            description="Read the contents of a file by path (relative to project root)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"}
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="write_file",
            description="Write text content to a file (relative to project root)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "content": {"type": "string", "description": "Text content to write"},
                },
                "required": ["path", "content"],
            },
        ),
        types.Tool(
            name="list_files",
            description="List files in a directory (relative to project root)",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Relative directory path"}
                },
                "required": ["directory"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "read_file":
        file_path = BASE_DIR / arguments["path"]
        if not file_path.exists():
            return [types.TextContent(type="text", text=f"ERROR: File not found: {file_path}")]
        content = file_path.read_text(encoding="utf-8")
        return [types.TextContent(type="text", text=content)]

    elif name == "write_file":
        file_path = BASE_DIR / arguments["path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(arguments["content"], encoding="utf-8")
        return [types.TextContent(type="text", text=f"Written {len(arguments['content'])} chars to {file_path}")]

    elif name == "list_files":
        dir_path = BASE_DIR / arguments["directory"]
        if not dir_path.exists():
            return [types.TextContent(type="text", text=f"ERROR: Directory not found: {dir_path}")]
        files = [str(p.relative_to(BASE_DIR)) for p in dir_path.iterdir()]
        return [types.TextContent(type="text", text=json.dumps(files))]

    return [types.TextContent(type="text", text=f"ERROR: Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
