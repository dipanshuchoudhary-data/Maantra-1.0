"""
Memory Module

Unified interface for all long-term memory functionality.

This module wraps the mem0 client and exposes memory APIs
used by the agent.

Usage
-----

Initialize memory system:

    from src.memory_ai import initialize_memory
    await initialize_memory()

Store memories:

    from src.memory_ai import add_memory
    await add_memory(messages, user_id)

Retrieve memories:

    from src.memory_ai import search_memory, build_memory_context

    memories = await search_memory(query, user_id)
    context = build_memory_context(memories)
"""

from src.memory_ai.mem0_client import (
    initialize_memory,
    add_memory,
    search_memory,
    get_all_memories,
    delete_memory,
    delete_all_memories,
    build_memory_context,
    is_memory_enabled,
    get_memory_status,
    MemoryItem,
)

__all__ = [
    "initialize_memory",
    "add_memory",
    "search_memory",
    "get_all_memories",
    "delete_memory",
    "delete_all_memories",
    "build_memory_context",
    "is_memory_enabled",
    "get_memory_status",
    "MemoryItem",
]