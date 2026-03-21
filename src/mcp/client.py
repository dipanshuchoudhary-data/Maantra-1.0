"""
MCP (Model Context Protocol) Client Manager

Responsible for:

1. Spawning MCP server processes
2. Communicating via JSON-RPC over stdio
3. Discovering tools
4. Executing tools on the correct server
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from src.utils.logger import get_logger
from src.mcp.config import load_mcp_config

logger = get_logger("mcp-client")

# ---------------------------------------------------------
# Data Models
# ---------------------------------------------------------


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPServer:
    name: str
    process: asyncio.subprocess.Process
    tools: List[MCPTool] = field(default_factory=list)
    request_id: int = 0
    pending_requests: Dict[int, asyncio.Future] = field(default_factory=dict)
    buffer: bytes = b""


# ---------------------------------------------------------
# Global Server Registry
# ---------------------------------------------------------

servers: Dict[str, MCPServer] = {}


# ---------------------------------------------------------
# Initialization
# ---------------------------------------------------------

async def initialize_mcp():

    logger.info("Initializing MCP servers...")

    config = load_mcp_config()

    if not config.servers:
        logger.warning("No MCP servers configured")
        return

    for server_config in config.servers:

        try:
            await connect_server(server_config)
        except Exception as e:
            logger.error(f"Failed connecting MCP server {server_config.name}: {e}")

    logger.info(f"MCP initialized with {len(servers)} servers")


# ---------------------------------------------------------
# Server Connection
# ---------------------------------------------------------

async def connect_server(config):

    logger.info(f"Connecting MCP server: {config.name}")

    process = await asyncio.create_subprocess_exec(
        config.command,
        *(config.args or []),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        # Preserve PATH and system environment so commands like npx resolve on Windows.
        env={**os.environ, **(config.env or {})},
    )

    server = MCPServer(
        name=config.name,
        process=process,
    )

    asyncio.create_task(read_stdout(server))
    asyncio.create_task(read_stderr(server))

    await asyncio.sleep(0.5)

    # Initialize server

    await send_request(
        server,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "maantra",
                "version": "1.0",
            },
        },
    )

    await send_notification(server, "notifications/initialized", {})

    result = await send_request(server, "tools/list", {})

    tools = result.get("tools", [])

    server.tools = [
        MCPTool(
            name=t["name"],
            description=t.get("description", ""),
            input_schema=t.get("inputSchema", {}),
        )
        for t in tools
    ]

    servers[config.name] = server

    logger.info(f"{config.name} connected with {len(server.tools)} tools")


def _drain_stdout_messages(server: MCPServer) -> List[Dict[str, Any]]:

    messages: List[Dict[str, Any]] = []

    while True:

        # Skip protocol separators between framed messages
        while server.buffer.startswith((b"\r", b"\n")):
            server.buffer = server.buffer[1:]

        if not server.buffer:
            break

        header_end = server.buffer.find(b"\r\n\r\n")
        delimiter_size = 4

        if header_end < 0:
            header_end = server.buffer.find(b"\n\n")
            delimiter_size = 2

        if header_end >= 0:

            headers_raw = server.buffer[:header_end]

            content_length = None

            try:
                for line in headers_raw.decode("ascii", errors="ignore").splitlines():
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":", 1)[1].strip())
                        break
            except Exception:
                content_length = None

            if content_length is not None:

                body_start = header_end + delimiter_size
                body_end = body_start + content_length

                if len(server.buffer) < body_end:
                    break

                body = server.buffer[body_start:body_end]
                server.buffer = server.buffer[body_end:]

                try:
                    messages.append(json.loads(body.decode("utf-8")))
                except Exception:
                    logger.debug(f"[{server.name}] Invalid framed JSON message")

                continue

        # Fallback: newline-delimited JSON
        newline_index = server.buffer.find(b"\n")

        if newline_index < 0:
            break

        raw_line = server.buffer[:newline_index].strip()
        server.buffer = server.buffer[newline_index + 1:]

        if not raw_line:
            continue

        try:
            messages.append(json.loads(raw_line.decode("utf-8")))
        except Exception:
            logger.debug(f"[{server.name}] Non JSON output: {raw_line[:200]!r}")

    return messages


# ---------------------------------------------------------
# IO Handling
# ---------------------------------------------------------

async def read_stdout(server: MCPServer):

    while True:

        data = await server.process.stdout.read(4096)

        if not data:
            break

        server.buffer += data

        for message in _drain_stdout_messages(server):

            if "id" in message:

                request_id = message["id"]

                future = server.pending_requests.pop(request_id, None)

                if future:

                    if "error" in message:
                        future.set_exception(
                            RuntimeError(message["error"].get("message", "MCP error"))
                        )
                    else:
                        future.set_result(message.get("result"))


async def read_stderr(server: MCPServer):

    while True:

        data = await server.process.stderr.readline()

        if not data:
            break

        logger.debug(f"[{server.name}] {data.decode().strip()}")


# ---------------------------------------------------------
# JSON-RPC Communication
# ---------------------------------------------------------

async def send_request(server: MCPServer, method: str, params: Dict):

    server.request_id += 1
    request_id = server.request_id

    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }

    future = asyncio.get_event_loop().create_future()

    server.pending_requests[request_id] = future

    message = json.dumps(request) + "\n"

    server.process.stdin.write(message.encode())
    await server.process.stdin.drain()

    try:
        return await asyncio.wait_for(future, timeout=30)
    except asyncio.TimeoutError:
        raise RuntimeError(f"MCP request timeout: {method}")


async def send_notification(server: MCPServer, method: str, params: Dict):

    notification = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
    }

    message = json.dumps(notification) + "\n"

    server.process.stdin.write(message.encode())
    await server.process.stdin.drain()


# ---------------------------------------------------------
# Tool Discovery
# ---------------------------------------------------------

def get_all_mcp_tools():

    tools = []

    for server_name, server in servers.items():

        for tool in server.tools:

            tools.append(
                {
                    "serverName": server_name,
                    "name": f"{server_name}_{tool.name}",
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                }
            )

    return tools


# ---------------------------------------------------------
# Tool Execution
# ---------------------------------------------------------

async def execute_mcp_tool(server_name: str, tool_name: str, args: Dict):

    server = servers.get(server_name)

    if not server:
        raise RuntimeError(f"MCP server not connected: {server_name}")

    logger.info(f"Executing MCP tool {server_name}/{tool_name}")

    result = await send_request(
        server,
        "tools/call",
        {
            "name": tool_name,
            "arguments": args,
        },
    )

    return result


# ---------------------------------------------------------
# Tool Name Parser
# ---------------------------------------------------------

def parse_tool_name(prefixed_name: str):

    for server_name in servers.keys():

        if prefixed_name.startswith(f"{server_name}_"):

            return {
                "serverName": server_name,
                "toolName": prefixed_name[len(server_name) + 1 :],
            }

    return None


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------

def is_mcp_enabled():

    return len(servers) > 0


def get_connected_servers():

    return list(servers.keys())


# ---------------------------------------------------------
# Shutdown
# ---------------------------------------------------------

async def shutdown_mcp():

    logger.info("Shutting down MCP servers")

    for name, server in servers.items():

        try:
            server.process.kill()
            logger.debug(f"Stopped MCP server {name}")
        except Exception as e:
            logger.error(f"Error stopping MCP server {name}: {e}")

    servers.clear()

    logger.info("MCP shutdown complete")