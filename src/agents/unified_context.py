"""
Unified Agent Context - Platform-agnostic context for agent processing.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class UnifiedAgentContext:
    """Platform-agnostic context passed to agent"""

    # Core identifiers
    session_id: str
    user_id: str                    # Unified user ID
    platform: str                   # "slack", "telegram", "whatsapp"
    conversation_id: str

    # User info
    user_name: str = "Unknown"
    user_language: str = "en"

    # Conversation context
    is_thread: bool = False
    reply_to_id: Optional[str] = None

    # User preferences (from database)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None

    # Platform capabilities
    supports_formatting: bool = False
    supports_media: bool = False
    max_message_length: int = 4096

    # Raw platform metadata
    platform_metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_legacy_context(cls, legacy_context) -> "UnifiedAgentContext":
        """Convert old AgentContext to UnifiedAgentContext for backward compat"""
        return cls(
            session_id=legacy_context.session_id,
            user_id=legacy_context.user_id,
            platform="slack",  # Default to Slack for legacy
            conversation_id=legacy_context.channel_id or "",
            user_name=legacy_context.user_name or "Unknown",
            is_thread=legacy_context.thread_ts is not None,
            reply_to_id=legacy_context.thread_ts,
            llm_provider=legacy_context.llm_provider,
            llm_model=legacy_context.llm_model,
            supports_formatting=True,  # Slack supports blocks
            platform_metadata={
                "channel_name": legacy_context.channel_name,
                "thread_ts": legacy_context.thread_ts,
            }
        )
