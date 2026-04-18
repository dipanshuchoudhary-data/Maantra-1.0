#!/usr/bin/env python3
"""
Checks Slack formatting helpers and reaction routing.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.channels.slack.formatter import help_message  # noqa: E402
from src.features.slack.reactions import SlackReactionWorkflow  # noqa: E402


async def main() -> int:
    payload = help_message()
    if not payload.get("text"):
        print("[FAILED] Help formatter missing fallback text")
        return 1

    blocks = payload.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        print("[FAILED] Help formatter missing Slack blocks")
        return 1

    workflow = SlackReactionWorkflow()
    handled = await workflow.handle(
        event={
            "reaction": "thumbsup",
            "user": "U_SLACK_CHECK",
            "item": {"type": "message", "channel": "C_SLACK_CHECK", "ts": "1.23"},
        },
        client=object(),
        bot_user_id="U_BOT",
    )
    if handled:
        print("[FAILED] Unrelated reaction should not be handled")
        return 1

    print("[SUCCESS] Slack feature checks passed")
    print(f"Help message blocks: {len(blocks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
