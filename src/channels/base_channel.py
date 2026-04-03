"""
Base Channel Adapter - Abstract interface for all messaging platforms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlatformMessage:
    """Normalized incoming message across all platforms"""
    text: str
    user_id: str                    # Unified user ID (after linking)
    platform_user_id: str           # Platform-specific ID
    platform: str                   # "slack", "telegram", "whatsapp"
    conversation_id: str            # Channel/group/chat ID
    message_id: str                 # Unique message ID
    timestamp: datetime
    reply_to_id: Optional[str] = None
    media_urls: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformResponse:
    """Response to send back to user"""
    text: str
    should_thread: bool = False
    reply_to_id: Optional[str] = None
    media_urls: List[str] = field(default_factory=list)
    formatting: Optional[Dict[str, Any]] = None  # Platform-specific formatting
    fallback_text: Optional[str] = None  # Plain text fallback


class BaseChannelAdapter(ABC):
    """Abstract base class for channel implementations"""

    platform_name: str  # "slack", "telegram", "whatsapp"

    # Platform capabilities
    supports_threads: bool = False
    supports_reactions: bool = False
    supports_rich_formatting: bool = False
    supports_media: bool = False
    max_message_length: int = 4096

    @abstractmethod
    async def start(self) -> None:
        """Start listening for events"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop listening and cleanup"""
        pass

    @abstractmethod
    async def normalize_event(self, raw_event: Any) -> Optional[PlatformMessage]:
        """Convert platform event to normalized PlatformMessage"""
        pass

    @abstractmethod
    async def send_response(
        self,
        response: PlatformResponse,
        context: Dict[str, Any]
    ) -> bool:
        """Send response back to user. Returns True if successful."""
        pass

    @abstractmethod
    async def get_user_info(self, platform_user_id: str) -> Dict[str, Any]:
        """Get user metadata from platform"""
        pass

    @abstractmethod
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[PlatformMessage]:
        """Get recent messages from conversation"""
        pass

    def create_session_id(
        self,
        user_id: str,
        conversation_id: str,
        reply_to_id: Optional[str] = None
    ) -> str:
        """Create unified session ID with platform prefix"""
        if reply_to_id:
            return f"thread:{self.platform_name}:{conversation_id}:{reply_to_id}"
        return f"conv:{self.platform_name}:{conversation_id}:{user_id}"