"""
Channels package - Multi-platform messaging channel adapters.
"""

from src.channels.base_channel import (
    BaseChannelAdapter,
    PlatformMessage,
    PlatformResponse,
)
from src.channels.channel_manager import ChannelManager, channel_manager

__all__ = [
    "BaseChannelAdapter",
    "PlatformMessage",
    "PlatformResponse",
    "ChannelManager",
    "channel_manager",
]
