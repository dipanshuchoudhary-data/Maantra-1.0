# Maantra Multi-Channel AI Agent - Complete Implementation Plan

> **Last Updated:** 2026-03-25
> **Status:** Phase 0 Complete, Ready for Phase 1
> **Current Task:** Start Foundation Layer

---

## Quick Navigation

- [Current Progress](#current-progress)
- [Next Actions](#next-actions-do-this-now)
- [Phase 1: Foundation](#phase-1-foundation-weeks-1-2)
- [Phase 2: Slack Enhanced](#phase-2-slack-enhanced-week-3)
- [Phase 3: Telegram](#phase-3-telegram-weeks-4-5)
- [Phase 4: WhatsApp](#phase-4-whatsapp--polish-week-6)
- [Architecture](#architecture-overview)
- [Security & Error Handling](#security--error-handling)
- [Dependencies](#dependencies)

---

## Current Progress

```
[##########] Phase 0: Bug Fixes & Optimization     ✅ COMPLETE
[##########] Phase 1: Foundation Layer              ✅ COMPLETE
[          ] Phase 2: Slack Enhanced                ⬜ NOT STARTED
[          ] Phase 3: Telegram Integration          ⬜ NOT STARTED
[          ] Phase 4: WhatsApp & Polish             ⬜ NOT STARTED
```

### Completed Work (Phase 0)
- [x] Token optimization (21k → 500 tokens for simple queries)
- [x] Smart tool loading with keyword detection
- [x] Document dataclass fixes in indexer
- [x] LLM providers conditional tool sending

---

## Next Actions (DO THIS NOW)

### Start Phase 1.1: Create Base Channel Interface

**File to Create:** `src/channels/base_channel.py`

```bash
# Step 1: Create directory structure
mkdir -p src/channels/slack
mkdir -p src/channels/telegram
mkdir -p src/channels/whatsapp
mkdir -p src/features/slack

# Step 2: Create base_channel.py (see code below)
```

**Estimated Time:** 2 hours

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Core                            │
│  ┌──────────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐ │
│  │ LLM Provider │  │   RAG    │  │ Memory  │  │  Tools  │ │
│  └──────────────┘  └──────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↑
                    ┌───────┴───────┐
                    │ Channel Manager│
                    └───────┬───────┘
         ┌──────────────────┼──────────────────┐
         ↓                  ↓                  ↓
┌────────────────┐  ┌───────────────┐  ┌────────────────┐
│  Slack Adapter │  │Telegram Adapter│  │WhatsApp Adapter│
└────────────────┘  └───────────────┘  └────────────────┘
```

### Final Directory Structure

```
src/
├── channels/
│   ├── __init__.py
│   ├── base_channel.py          # Abstract base class
│   ├── channel_manager.py       # Orchestrator
│   ├── slack/
│   │   ├── __init__.py
│   │   ├── handler.py           # SlackChannelAdapter
│   │   ├── tools.py             # Slack-specific tools
│   │   └── formatter.py         # Block Kit formatting
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── handler.py           # TelegramChannelAdapter
│   │   ├── tools.py             # Telegram tools
│   │   └── formatter.py         # Markdown formatting
│   └── whatsapp/
│       ├── __init__.py
│       ├── handler.py           # WhatsAppChannelAdapter
│       ├── tools.py             # WhatsApp tools
│       └── templates.py         # Template messages
├── agents/
│   ├── agent.py                 # (Modified)
│   └── unified_context.py       # NEW: Platform-agnostic context
├── features/
│   └── slack/
│       ├── reactions.py         # Reaction workflows
│       ├── reminders.py         # Advanced reminders
│       └── analytics.py         # Channel analytics
├── tools/
│   ├── base_tools.py            # NEW: Abstract tool interface
│   └── [existing files...]
└── memory/
    └── database.py              # (Modified for unified identity)
```

---

## Phase 1: Foundation (Weeks 1-2)

### Task 1.1: Create Base Channel Interface
**Status:** ⬜ Not Started | **Time:** 2 hours

**File:** `src/channels/base_channel.py`

```python
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
```

**Checklist:**
- [ ] Create file `src/channels/base_channel.py`
- [ ] Create `src/channels/__init__.py`
- [ ] Test import works: `from src.channels.base_channel import BaseChannelAdapter`

---

### Task 1.2: Create Unified Context
**Status:** ⬜ Not Started | **Time:** 1 hour

**File:** `src/agents/unified_context.py`

```python
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
```

**Checklist:**
- [ ] Create file `src/agents/unified_context.py`
- [ ] Test import works

---

### Task 1.3: Create Channel Manager
**Status:** ⬜ Not Started | **Time:** 1.5 hours

**File:** `src/channels/channel_manager.py`

```python
"""
Channel Manager - Centralized orchestration of all channel adapters.
"""

from typing import Dict, Optional, List
from src.channels.base_channel import BaseChannelAdapter
from src.utils.logger import get_logger

logger = get_logger("channel-manager")


class ChannelManager:
    """Manages all channel adapters lifecycle and routing"""

    def __init__(self):
        self.channels: Dict[str, BaseChannelAdapter] = {}
        self._started = False

    def register(self, adapter: BaseChannelAdapter) -> None:
        """Register a channel adapter"""
        if adapter.platform_name in self.channels:
            logger.warning(f"Overwriting existing adapter: {adapter.platform_name}")
        self.channels[adapter.platform_name] = adapter
        logger.info(f"Registered channel adapter: {adapter.platform_name}")

    def get(self, platform: str) -> Optional[BaseChannelAdapter]:
        """Get adapter for specific platform"""
        return self.channels.get(platform)

    def list_platforms(self) -> List[str]:
        """List all registered platforms"""
        return list(self.channels.keys())

    async def start_all(self) -> None:
        """Start all registered channel adapters"""
        if self._started:
            logger.warning("Channel manager already started")
            return

        for name, adapter in self.channels.items():
            try:
                await adapter.start()
                logger.info(f"Started channel: {name}")
            except Exception as e:
                logger.error(f"Failed to start channel {name}: {e}")

        self._started = True

    async def stop_all(self) -> None:
        """Stop all channel adapters gracefully"""
        for name, adapter in self.channels.items():
            try:
                await adapter.stop()
                logger.info(f"Stopped channel: {name}")
            except Exception as e:
                logger.error(f"Error stopping channel {name}: {e}")

        self._started = False


# Global instance
channel_manager = ChannelManager()
```

**Checklist:**
- [ ] Create file `src/channels/channel_manager.py`
- [ ] Test import and basic functionality

---

### Task 1.4: Create Slack Channel Adapter
**Status:** ⬜ Not Started | **Time:** 4 hours

**File:** `src/channels/slack/handler.py`

This involves:
1. Moving existing `src/channels/slack.py` logic
2. Wrapping in `SlackChannelAdapter` class
3. Implementing all abstract methods

```python
"""
Slack Channel Adapter - Implements BaseChannelAdapter for Slack.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from src.channels.base_channel import (
    BaseChannelAdapter,
    PlatformMessage,
    PlatformResponse,
)
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("slack-adapter")


class SlackChannelAdapter(BaseChannelAdapter):
    """Slack implementation of channel adapter"""

    platform_name = "slack"
    supports_threads = True
    supports_reactions = True
    supports_rich_formatting = True
    supports_media = True
    max_message_length = 40000  # Slack limit

    def __init__(self):
        self.app = AsyncApp(token=settings.slack.bot_token)
        self.handler = None
        self.bot_id = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Register Slack event handlers"""

        @self.app.event("message")
        async def handle_message(event, say):
            # Delegate to unified message processing
            await self._process_message(event, say)

        @self.app.event("reaction_added")
        async def handle_reaction(event, say):
            await self._process_reaction(event, say)

    async def start(self) -> None:
        """Start Slack socket mode handler"""
        auth = await self.app.client.auth_test()
        self.bot_id = auth["user_id"]

        self.handler = AsyncSocketModeHandler(
            self.app,
            settings.slack.app_token
        )
        await self.handler.start_async()
        logger.info(f"Slack adapter started (bot_id={self.bot_id})")

    async def stop(self) -> None:
        """Stop Slack handler"""
        if self.handler:
            await self.handler.close_async()
        logger.info("Slack adapter stopped")

    async def normalize_event(self, raw_event: dict) -> Optional[PlatformMessage]:
        """Convert Slack event to PlatformMessage"""
        if raw_event.get("subtype"):
            return None  # Skip system messages

        if raw_event.get("user") == self.bot_id:
            return None  # Skip own messages

        return PlatformMessage(
            text=raw_event.get("text", ""),
            user_id=raw_event["user"],  # Will be resolved to unified ID
            platform_user_id=raw_event["user"],
            platform="slack",
            conversation_id=raw_event["channel"],
            message_id=raw_event["ts"],
            timestamp=datetime.fromtimestamp(float(raw_event["ts"])),
            reply_to_id=raw_event.get("thread_ts"),
            metadata={
                "channel_type": raw_event.get("channel_type"),
                "event_ts": raw_event.get("event_ts"),
            }
        )

    async def send_response(
        self,
        response: PlatformResponse,
        context: Dict[str, Any]
    ) -> bool:
        """Send response to Slack"""
        try:
            kwargs = {
                "channel": context["conversation_id"],
                "text": response.text,
            }

            if response.should_thread and context.get("reply_to_id"):
                kwargs["thread_ts"] = context["reply_to_id"]

            if response.formatting:
                kwargs["blocks"] = response.formatting.get("blocks")

            await self.app.client.chat_postMessage(**kwargs)
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    async def get_user_info(self, platform_user_id: str) -> Dict[str, Any]:
        """Get Slack user info"""
        try:
            result = await self.app.client.users_info(user=platform_user_id)
            user = result["user"]
            return {
                "id": user["id"],
                "name": user.get("real_name") or user.get("name"),
                "email": user.get("profile", {}).get("email"),
                "avatar": user.get("profile", {}).get("image_72"),
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {"id": platform_user_id, "name": "Unknown"}

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[PlatformMessage]:
        """Get Slack conversation history"""
        try:
            result = await self.app.client.conversations_history(
                channel=conversation_id,
                limit=limit
            )
            messages = []
            for msg in result.get("messages", []):
                normalized = await self.normalize_event(msg)
                if normalized:
                    messages.append(normalized)
            return messages
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    async def _process_message(self, event: dict, say) -> None:
        """Process incoming Slack message"""
        # This will be connected to the Agent
        # For now, just normalize and log
        message = await self.normalize_event(event)
        if message:
            logger.info(f"Received message: {message.text[:50]}...")
            # TODO: Connect to agent.process_message()

    async def _process_reaction(self, event: dict, say) -> None:
        """Process reaction events"""
        # TODO: Implement reaction workflows
        pass
```

**Checklist:**
- [ ] Create `src/channels/slack/__init__.py`
- [ ] Create `src/channels/slack/handler.py`
- [ ] Test Slack adapter starts correctly
- [ ] Test message normalization

---

### Task 1.5: Update Database for Unified Identity
**Status:** ⬜ Not Started | **Time:** 2 hours

**File:** `src/memory/database.py` (Add to existing)

```python
# Add these tables and functions to database.py

# New table for platform linking
USER_PLATFORM_LINKS_TABLE = """
CREATE TABLE IF NOT EXISTS user_platform_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    platform_username TEXT,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    UNIQUE(platform, platform_user_id)
)
"""

def init_platform_links_table():
    """Initialize platform links table"""
    with get_connection() as conn:
        conn.execute(USER_PLATFORM_LINKS_TABLE)
        conn.commit()


def link_platform_user(
    user_id: str,
    platform: str,
    platform_user_id: str,
    platform_username: str = None
) -> bool:
    """Link a platform account to primary user"""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO user_platform_links
                (user_id, platform, platform_user_id, platform_username, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (user_id, platform, platform_user_id, platform_username)
            )
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to link platform user: {e}")
        return False


def get_user_by_platform(platform: str, platform_user_id: str) -> Optional[str]:
    """Get unified user_id from platform identifier"""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT user_id FROM user_platform_links
            WHERE platform = ? AND platform_user_id = ? AND is_active = 1
            """,
            (platform, platform_user_id)
        )
        row = cursor.fetchone()
        return row[0] if row else None


def get_all_platform_identities(user_id: str) -> Dict[str, str]:
    """Get all platform user IDs for a given user"""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT platform, platform_user_id FROM user_platform_links
            WHERE user_id = ? AND is_active = 1
            """,
            (user_id,)
        )
        return {row[0]: row[1] for row in cursor.fetchall()}
```

**Checklist:**
- [ ] Add platform links table schema
- [ ] Add `link_platform_user()` function
- [ ] Add `get_user_by_platform()` function
- [ ] Add `get_all_platform_identities()` function
- [ ] Call `init_platform_links_table()` in app startup

---

### Task 1.6: Update main.py for Channel Manager
**Status:** ⬜ Not Started | **Time:** 1 hour

**File:** `src/main.py` (Modify existing)

```python
# Add to imports
from src.channels.channel_manager import channel_manager
from src.channels.slack.handler import SlackChannelAdapter

# In startup sequence, replace direct Slack init with:
async def startup():
    # ... existing init code ...

    # Initialize channels
    if settings.slack.bot_token:
        slack_adapter = SlackChannelAdapter()
        channel_manager.register(slack_adapter)

    # Start all registered channels
    await channel_manager.start_all()


async def shutdown():
    await channel_manager.stop_all()
    # ... existing cleanup ...
```

**Checklist:**
- [ ] Import channel manager in main.py
- [ ] Register Slack adapter
- [ ] Call `channel_manager.start_all()` on startup
- [ ] Call `channel_manager.stop_all()` on shutdown

---

## Phase 1 Summary Checklist

```
Phase 1: Foundation Layer
├── [x] 1.1 Create base_channel.py
├── [x] 1.2 Create unified_context.py
├── [x] 1.3 Create channel_manager.py
├── [x] 1.4 Create Slack adapter (handler.py)
├── [x] 1.5 Update database for unified identity
├── [x] 1.6 Update main.py
└── [x] 1.7 Test: Slack still works after refactor
```

**Estimated Time:** 12-15 hours
**Risk Level:** Medium (refactoring core components)

---

## Phase 2: Slack Enhanced (Week 3)

### Task 2.1: Message Formatter
**File:** `src/channels/slack/formatter.py`

```python
"""
Slack message formatting with Block Kit.
"""

from typing import List, Dict, Any, Optional


class SlackFormatter:
    """Format messages using Slack Block Kit"""

    @staticmethod
    def text_section(text: str) -> Dict[str, Any]:
        """Simple text section"""
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        }

    @staticmethod
    def code_block(code: str, language: str = "") -> Dict[str, Any]:
        """Format code with syntax highlighting"""
        formatted = f"```{language}\n{code}\n```"
        return SlackFormatter.text_section(formatted)

    @staticmethod
    def action_buttons(buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create action buttons"""
        return {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": btn["text"]},
                    "action_id": btn["action_id"],
                    "value": btn.get("value", btn["action_id"])
                }
                for btn in buttons
            ]
        }

    @staticmethod
    def divider() -> Dict[str, Any]:
        return {"type": "divider"}

    @staticmethod
    def header(text: str) -> Dict[str, Any]:
        return {
            "type": "header",
            "text": {"type": "plain_text", "text": text}
        }

    @staticmethod
    def build_message(
        text: str,
        sections: List[Dict[str, Any]] = None,
        actions: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Build complete Slack message with blocks"""
        blocks = []

        if text:
            blocks.append(SlackFormatter.text_section(text))

        if sections:
            blocks.extend(sections)

        if actions:
            blocks.append(SlackFormatter.action_buttons(actions))

        return {"blocks": blocks, "text": text}  # text is fallback
```

### Task 2.2: Reaction Workflows
**File:** `src/features/slack/reactions.py`

### Task 2.3: Advanced Reminders
**File:** `src/features/slack/reminders.py`

### Task 2.4: Channel Analytics
**File:** `src/features/slack/analytics.py`

---

## Phase 3: Telegram (Weeks 4-5)

### Task 3.1: Telegram Adapter
**File:** `src/channels/telegram/handler.py`

```python
"""
Telegram Channel Adapter
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters

from src.channels.base_channel import (
    BaseChannelAdapter,
    PlatformMessage,
    PlatformResponse,
)
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("telegram-adapter")


class TelegramChannelAdapter(BaseChannelAdapter):
    """Telegram implementation of channel adapter"""

    platform_name = "telegram"
    supports_threads = True  # Reply threads
    supports_reactions = False  # Limited
    supports_rich_formatting = True  # Markdown
    supports_media = True
    max_message_length = 4096

    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Register Telegram handlers"""
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_message
        ))
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("link", self._handle_link))

    async def start(self) -> None:
        """Start Telegram bot with webhook or polling"""
        await self.app.initialize()
        await self.app.start()

        # Use polling for development
        await self.app.updater.start_polling()
        logger.info("Telegram adapter started (polling mode)")

    async def stop(self) -> None:
        """Stop Telegram bot"""
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("Telegram adapter stopped")

    async def normalize_event(self, update: Update) -> Optional[PlatformMessage]:
        """Convert Telegram Update to PlatformMessage"""
        message = update.message
        if not message or not message.text:
            return None

        return PlatformMessage(
            text=message.text,
            user_id=str(message.from_user.id),  # Will resolve to unified
            platform_user_id=str(message.from_user.id),
            platform="telegram",
            conversation_id=str(message.chat_id),
            message_id=str(message.message_id),
            timestamp=message.date,
            reply_to_id=str(message.reply_to_message.message_id) if message.reply_to_message else None,
            metadata={
                "first_name": message.from_user.first_name,
                "username": message.from_user.username,
                "chat_type": message.chat.type,
            }
        )

    async def send_response(
        self,
        response: PlatformResponse,
        context: Dict[str, Any]
    ) -> bool:
        """Send response to Telegram"""
        try:
            await self.app.bot.send_message(
                chat_id=int(context["conversation_id"]),
                text=response.text,
                parse_mode="Markdown" if context.get("supports_formatting") else None,
                reply_to_message_id=int(context["reply_to_id"]) if response.should_thread and context.get("reply_to_id") else None
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def get_user_info(self, platform_user_id: str) -> Dict[str, Any]:
        """Get Telegram user info"""
        # Telegram doesn't have a direct user lookup API
        # Return basic info from cache or message context
        return {"id": platform_user_id, "name": "Telegram User"}

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[PlatformMessage]:
        """Telegram doesn't support history retrieval via bot API"""
        return []

    async def _handle_message(self, update: Update, context) -> None:
        """Handle incoming text message"""
        message = await self.normalize_event(update)
        if message:
            logger.info(f"Telegram message: {message.text[:50]}...")
            # TODO: Connect to agent

    async def _handle_start(self, update: Update, context) -> None:
        """Handle /start command"""
        await update.message.reply_text(
            "Hello! I'm your AI assistant. Send me a message to get started.\n\n"
            "Use /link <code> to link your Slack account."
        )

    async def _handle_link(self, update: Update, context) -> None:
        """Handle /link command for account linking"""
        # TODO: Implement account linking
        await update.message.reply_text("Account linking not yet implemented.")
```

### Task 3.2: Telegram Tools
**File:** `src/channels/telegram/tools.py`

### Task 3.3: Account Linking
**File:** `src/features/account_linking.py`

---

## Phase 4: WhatsApp & Polish (Week 6+)

### Task 4.1: WhatsApp Adapter
**File:** `src/channels/whatsapp/handler.py`

### Task 4.2: WhatsApp Templates
**File:** `src/channels/whatsapp/templates.py`

```python
"""
WhatsApp Template Messages (required for initiating conversations)
"""

TEMPLATES = {
    "reminder": {
        "name": "reminder_notification",
        "language": "en",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "{{1}}"},  # reminder text
                ]
            }
        ]
    },
    "notification": {
        "name": "general_notification",
        "language": "en",
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "{{1}}"},  # notification text
                ]
            }
        ]
    }
}
```

---

## Security & Error Handling

### Account Linking Security

```python
"""
Secure account linking with one-time codes.
File: src/features/account_linking.py
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

# In-memory store (use Redis in production)
_pending_links: Dict[str, Dict] = {}
LINK_CODE_EXPIRY = timedelta(minutes=5)


def generate_link_code(slack_user_id: str) -> str:
    """Generate one-time link code for account linking"""
    code = f"LINK-{secrets.token_hex(4).upper()}"
    _pending_links[code] = {
        "slack_user_id": slack_user_id,
        "created_at": datetime.now(),
    }
    return code


def verify_link_code(code: str, platform_user_id: str, platform: str) -> Optional[str]:
    """Verify link code and return Slack user_id if valid"""
    if code not in _pending_links:
        return None

    link_data = _pending_links[code]

    # Check expiry
    if datetime.now() - link_data["created_at"] > LINK_CODE_EXPIRY:
        del _pending_links[code]
        return None

    # Valid - remove code and return user_id
    slack_user_id = link_data["slack_user_id"]
    del _pending_links[code]

    return slack_user_id
```

### Rate Limiting

```python
"""
Rate limiting per platform.
File: src/utils/rate_limiter.py
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

# Rate limits per platform (messages per second)
RATE_LIMITS = {
    "slack": 1,      # 1 msg/sec per channel
    "telegram": 30,  # 30 msg/sec global
    "whatsapp": 80,  # 80 msg/sec (Business API)
}

_message_counts: Dict[str, list] = defaultdict(list)


async def check_rate_limit(platform: str, identifier: str) -> bool:
    """Check if we're within rate limits. Returns True if OK."""
    key = f"{platform}:{identifier}"
    limit = RATE_LIMITS.get(platform, 10)
    window = timedelta(seconds=1)

    now = datetime.now()
    cutoff = now - window

    # Clean old entries
    _message_counts[key] = [t for t in _message_counts[key] if t > cutoff]

    if len(_message_counts[key]) >= limit:
        return False

    _message_counts[key].append(now)
    return True
```

### Error Handling

```python
"""
Platform-specific error handling.
File: src/utils/error_handler.py
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PlatformError:
    platform: str
    error_code: str
    message: str
    is_retryable: bool
    severity: ErrorSeverity
    original_exception: Optional[Exception] = None


FALLBACK_MESSAGES = {
    "rate_limit": "I'm receiving too many messages right now. Please wait a moment.",
    "api_error": "I'm having trouble connecting. Please try again.",
    "timeout": "That's taking longer than expected. Please try again.",
    "unknown": "Something went wrong. Please try again later.",
}


async def handle_platform_error(error: PlatformError, context: dict) -> str:
    """Handle platform error and return user-friendly message"""
    # Log error
    logger.error(f"[{error.platform}] {error.error_code}: {error.message}")

    # Return appropriate fallback
    if "rate" in error.error_code.lower():
        return FALLBACK_MESSAGES["rate_limit"]
    elif "timeout" in error.error_code.lower():
        return FALLBACK_MESSAGES["timeout"]
    elif error.is_retryable:
        return FALLBACK_MESSAGES["api_error"]
    else:
        return FALLBACK_MESSAGES["unknown"]
```

---

## Dependencies

### Add to pyproject.toml

```toml
[project.dependencies]
# Existing...

# Telegram
python-telegram-bot = "^21.0"

# WhatsApp (Twilio)
twilio = "^9.0"

# Rate limiting (optional, for production)
redis = "^5.0"

# Webhook server (for production Telegram)
aiohttp = "^3.9"
```

### Install Command

```bash
uv add python-telegram-bot twilio
```

---

## Environment Variables

Add to `.env`:

```env
# Telegram
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# WhatsApp (Twilio)
WHATSAPP_ENABLED=false
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886
```

---

## Testing Checklist

### Phase 1 Tests
- [ ] Slack still works after refactor
- [ ] Session IDs include platform prefix
- [ ] Database tables created correctly
- [ ] Channel manager starts/stops cleanly

### Phase 2 Tests
- [ ] Block Kit messages render correctly
- [ ] Reactions trigger workflows
- [ ] Reminders are sent on time

### Phase 3 Tests
- [ ] Telegram bot responds to messages
- [ ] Account linking works
- [ ] Memory shared between Slack↔Telegram

### Phase 4 Tests
- [ ] WhatsApp messages received
- [ ] Template messages sent correctly
- [ ] 24-hour window handled

---

## Quick Reference

### Start Implementation

```bash
# 1. Create directories
mkdir -p src/channels/slack src/channels/telegram src/channels/whatsapp
mkdir -p src/features/slack

# 2. Start with Task 1.1
# Create src/channels/base_channel.py (copy from above)

# 3. Test import
python -c "from src.channels.base_channel import BaseChannelAdapter; print('OK')"
```

### Current Status Command

```bash
# Check what's implemented
ls -la src/channels/
ls -la src/features/
```

---

## Estimated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0: Bug Fixes | Done | ✅ Complete |
| Phase 1: Foundation | 2 weeks | ⬜ Ready to Start |
| Phase 2: Slack Enhanced | 1 week | ⬜ Pending |
| Phase 3: Telegram | 2 weeks | ⬜ Pending |
| Phase 4: WhatsApp | 1+ week | ⬜ Low Priority |

**Total:** 6-8 weeks

---

## Support

If stuck, check:
1. Existing `src/channels/slack.py` for reference
2. Slack Bolt docs: https://slack.dev/bolt-python/
3. python-telegram-bot docs: https://python-telegram-bot.org/
4. Twilio WhatsApp: https://www.twilio.com/docs/whatsapp
