"""
MCP (Model Context Protocol) Module

Unified interface for MCP integration.

Provides:

• MCP server lifecycle management
• Tool discovery
• Tool execution
• Tool schema conversion
• Configuration loading

Example usage:

    from src.mcp import initialize_mcp, get_all_mcp_tools

    await initialize_mcp()

    tools = get_all_mcp_tools()
"""

# ---------------------------------------------------
# Client exports
# ---------------------------------------------------

from src.mcp.client import (
    initialize_mcp,
    shutdown_mcp,
    get_all_mcp_tools,
    execute_mcp_tool,
    parse_tool_name,
    is_mcp_enabled,
    get_connected_servers,
    MCPTool,
)

# ---------------------------------------------------
# Configuration exports
# ---------------------------------------------------

from src.mcp.config import (
    load_mcp_config,
    validate_mcp_config,
    MCPServerConfig,
    MCPConfig,
)

# ---------------------------------------------------
# Tool conversion exports
# ---------------------------------------------------

from src.mcp.tool_converter import (
    mcp_tool_to_openai,
    mcp_tools_to_openai,
    format_mcp_result,
)

# ---------------------------------------------------
# Public module API
# ---------------------------------------------------

__all__ = [
    # Client
    "initialize_mcp",
    "shutdown_mcp",
    "get_all_mcp_tools",
    "execute_mcp_tool",
    "parse_tool_name",
    "is_mcp_enabled",
    "get_connected_servers",
    "MCPTool",

    # Config
    "load_mcp_config",
    "validate_mcp_config",
    "MCPServerConfig",
    "MCPConfig",

    # Tool conversion
    "mcp_tool_to_openai",
    "mcp_tools_to_openai",
    "format_mcp_result",
]