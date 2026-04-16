#!/usr/bin/env python3
"""
Phase 1 validation script:
- Unified user linking for Slack IDs
- Platform-prefixed session IDs
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import (  # noqa: E402
    initialize_database,
    get_or_create_unified_user,
    get_or_create_session,
)


def main() -> int:
    initialize_database()

    platform = "slack"
    platform_user_id = "U_PHASE1_TEST"
    channel_id = "C_PHASE1_TEST"
    thread_ts = "12345.6789"

    unified_user_id = get_or_create_unified_user(platform, platform_user_id, "phase1-user")
    if unified_user_id != f"{platform}:{platform_user_id}":
        print(f"[FAILED] Unexpected unified user id: {unified_user_id}")
        return 1

    dm_session = get_or_create_session(
        unified_user_id,
        channel_id=None,
        thread_ts=None,
        platform=platform,
    )
    if not dm_session["id"].startswith("dm:slack:"):
        print(f"[FAILED] DM session id missing platform prefix: {dm_session['id']}")
        return 1

    channel_session = get_or_create_session(
        unified_user_id,
        channel_id=channel_id,
        thread_ts=None,
        platform=platform,
    )
    if not channel_session["id"].startswith("channel:slack:"):
        print(f"[FAILED] Channel session id missing platform prefix: {channel_session['id']}")
        return 1

    thread_session = get_or_create_session(
        unified_user_id,
        channel_id=channel_id,
        thread_ts=thread_ts,
        platform=platform,
    )
    if not thread_session["id"].startswith("thread:slack:"):
        print(f"[FAILED] Thread session id missing platform prefix: {thread_session['id']}")
        return 1

    print("[SUCCESS] Phase 1 unified identity validation passed")
    print(f"Unified user id: {unified_user_id}")
    print(f"DM session id: {dm_session['id']}")
    print(f"Channel session id: {channel_session['id']}")
    print(f"Thread session id: {thread_session['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
