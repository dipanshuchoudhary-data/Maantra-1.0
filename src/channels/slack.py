"""
Slack Channel Integration for Maantra

Handles:
- Slack events
- Slack messages
- Mentions
- Slash commands
- Thread summarization
"""

import asyncio
import re
from typing import Optional

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient

from src.config.settings import settings
from src.utils.logger import get_logger

from src.memory.database import (
    get_or_create_session,
    is_user_approved,
    generate_pairing_code,
    approve_pairing,
)

from src.agents.agent import Agent, AgentContext, summarize_thread
from src.tools.scheduler import task_scheduler

logger = get_logger("slack")

# ------------------------------------------------
# Slack App Initialization
# ------------------------------------------------

slack_app = AsyncApp(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret,
)

web_client: AsyncWebClient = slack_app.client

agent = Agent()

bot_user_id: Optional[str] = None
socket_handler: Optional[AsyncSocketModeHandler] = None


# ------------------------------------------------
# Utility Helpers
# ------------------------------------------------


async def get_bot_user_id() -> str:
    global bot_user_id

    if bot_user_id:
        return bot_user_id

    auth = await web_client.auth_test()

    bot_user_id = auth["user_id"]

    return bot_user_id


def is_bot_mentioned(text: str, bot_id: str) -> bool:
    return f"<@{bot_id}>" in text


def remove_bot_mention(text: str, bot_id: str) -> str:
    return re.sub(f"<@{bot_id}>\\s*", "", text).strip()


def is_direct_message(channel_id: str) -> bool:
    return channel_id.startswith("D")


async def get_user_info(user_id: str):

    try:

        res = await web_client.users_info(user=user_id)

        user = res["user"]

        return {
            "name": user.get("name", "unknown"),
            "real_name": user.get("real_name", "unknown"),
        }

    except Exception:

        return {"name": "unknown", "real_name": "unknown"}


async def get_channel_info(channel_id: str):

    try:

        res = await web_client.conversations_info(channel=channel_id)

        return {"name": res["channel"]["name"]}

    except Exception:

        return {"name": "unknown"}


# ------------------------------------------------
# Message Handler
# ------------------------------------------------


@slack_app.event("message")
async def handle_message(event, say):

    if event.get("subtype"):
        return

    text = event.get("text")
    user = event.get("user")
    channel = event.get("channel")
    ts = event.get("ts")
    thread_ts = event.get("thread_ts")

    if not text or not user:
        return

    bot_id = await get_bot_user_id()

    if user == bot_id:
        return

    logger.info(f"Message from {user} in {channel}")

    is_dm = is_direct_message(channel)

    # ------------------------------------------------
    # DM security policy
    # ------------------------------------------------

    if is_dm and settings.dm_policy != "open":

        if not is_user_approved(user):

            code = generate_pairing_code(user)

            await say(
                text=f"""
Before we chat, you must be approved.

Pairing code: `{code}`

Ask an admin to approve with:
/approve {code}
"""
            )

            return

    # ------------------------------------------------
    # Channel mention policy
    # ------------------------------------------------

    if not is_dm:

        if not is_bot_mentioned(text, bot_id):
            return

    clean_text = text if is_dm else remove_bot_mention(text, bot_id)

    # ------------------------------------------------
    # Help
    # ------------------------------------------------

    if clean_text.lower() in ["help", "/help"]:

        await say(
            text="""
Maantra Assistant

Commands:
• help
• summarize
• remind me
• my tasks
• cancel task [id]
• /reset
"""
        )

        return

    # ------------------------------------------------
    # Thread Summarization
    # ------------------------------------------------

    if "summarize" in clean_text.lower() or clean_text.lower() == "tldr":

        if thread_ts:

            replies = await web_client.conversations_replies(
                channel=channel,
                ts=thread_ts,
            )

            msgs = replies.get("messages", [])

            context = AgentContext(
                session_id=f"summary:{channel}:{thread_ts}",
                user_id=user,
                channel_id=channel,
                thread_ts=thread_ts,
            )

            summary = await summarize_thread(msgs, context)

            await say(
                text=f"*Thread Summary*\n\n{summary}",
                thread_ts=thread_ts,
            )

        else:

            await say(
                text="Use summarize inside a thread.",
                thread_ts=ts,
            )

        return

    # ------------------------------------------------
    # Agent Processing
    # ------------------------------------------------

    try:

        session = get_or_create_session(user, channel, thread_ts)

        user_info = await get_user_info(user)

        channel_info = {"name": "DM"} if is_dm else await get_channel_info(channel)

        context = AgentContext(
            session_id=session.id,
            user_id=user,
            channel_id=channel,
            thread_ts=thread_ts,
            user_name=user_info["real_name"],
            channel_name=channel_info["name"],
        )

        response = await agent.process_message(clean_text, context)

        await say(
            text=response.content,
            thread_ts=thread_ts or ts if response.should_thread else None,
        )

    except Exception as e:

        logger.error(f"Agent processing failed: {e}")

        await say(
            text="Sorry, something went wrong processing your message.",
            thread_ts=thread_ts or ts,
        )


# ------------------------------------------------
# Slash Commands
# ------------------------------------------------


@slack_app.command("/approve")
async def approve_command(ack, respond, command):

    await ack()

    code = command["text"].strip().upper()

    if not code:
        await respond("Usage: /approve CODE")
        return

    success = approve_pairing(code, command["user_id"])

    if success:
        await respond(f"Pairing code {code} approved")
    else:
        await respond(f"Invalid pairing code {code}")


# ------------------------------------------------
# Startup / Shutdown
# ------------------------------------------------


async def start_slack_app():

    global socket_handler

    socket_handler = AsyncSocketModeHandler(
        slack_app,
        settings.slack_app_token
    )

    await socket_handler.start_async()

    bot_id = await get_bot_user_id()

    logger.info(f"Slack bot started. Bot ID: {bot_id}")


async def stop_slack_app():

    if socket_handler:
        await socket_handler.close_async()

    logger.info("Slack bot stopped")