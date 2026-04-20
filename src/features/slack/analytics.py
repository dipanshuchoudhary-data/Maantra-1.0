"""
Small channel statistics helpers for Slack.
"""

from collections import Counter
from typing import Any, Dict, List

from src.channels.slack.formatter import channel_stats_message


class SlackChannelAnalytics:
    """Build a lightweight activity summary from recent Slack messages."""

    COMMANDS = {"channel stats", "channel analytics", "stats"}

    def is_command(self, text: str) -> bool:
        return text.strip().lower() in self.COMMANDS

    async def build_report(
        self,
        *,
        client: Any,
        channel_id: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        result = await client.conversations_history(channel=channel_id, limit=limit)
        messages = result.get("messages", [])
        return channel_stats_message(calculate_channel_stats(messages))


def calculate_channel_stats(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    user_counts: Counter[str] = Counter()
    thread_replies = 0

    for message in messages:
        user_id = message.get("user")
        if user_id:
            user_counts[user_id] += 1

        if message.get("thread_ts") and message.get("thread_ts") != message.get("ts"):
            thread_replies += 1

    return {
        "messages_scanned": len(messages),
        "unique_users": len(user_counts),
        "thread_replies": thread_replies,
        "top_users": user_counts.most_common(5),
    }
