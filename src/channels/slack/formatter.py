"""
Slack message formatting helpers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class SlackFormatter:
    """Build Slack Block Kit payloads."""

    MAX_SECTION_TEXT = 3000

    @staticmethod
    def _trim(text: str, limit: int = MAX_SECTION_TEXT) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 15].rstrip() + "\n...[truncated]"

    @staticmethod
    def text_section(text: str) -> Dict[str, Any]:
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": SlackFormatter._trim(text)},
        }

    @staticmethod
    def context(text: str) -> Dict[str, Any]:
        return {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": SlackFormatter._trim(text, 2000)}],
        }

    @staticmethod
    def header(text: str) -> Dict[str, Any]:
        return {
            "type": "header",
            "text": {"type": "plain_text", "text": SlackFormatter._trim(text, 150)},
        }

    @staticmethod
    def divider() -> Dict[str, Any]:
        return {"type": "divider"}

    @staticmethod
    def code_block(code: str, language: str = "") -> Dict[str, Any]:
        language_hint = language.strip()
        formatted = f"```{language_hint}\n{code}\n```" if language_hint else f"```\n{code}\n```"
        return SlackFormatter.text_section(formatted)

    @staticmethod
    def action_buttons(buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": button["text"]},
                    "action_id": button["action_id"],
                    "value": button.get("value", button["action_id"]),
                }
                for button in buttons
            ],
        }

    @staticmethod
    def build_message(
        text: str,
        *,
        title: Optional[str] = None,
        sections: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        footer: Optional[str] = None,
    ) -> Dict[str, Any]:
        blocks: List[Dict[str, Any]] = []

        if title:
            blocks.append(SlackFormatter.header(title))

        if text:
            blocks.append(SlackFormatter.text_section(text))

        if sections:
            blocks.extend(sections)

        if actions:
            blocks.append(SlackFormatter.action_buttons(actions))

        if footer:
            blocks.append(SlackFormatter.context(footer))

        return {"text": text or title or "Maantra", "blocks": blocks}


def task_list_message(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not tasks:
        return SlackFormatter.build_message(
            "No pending tasks found.",
            title="Tasks",
        )

    lines = []
    for task in tasks:
        task_id = task.get("id")
        description = task.get("task_description") or "Untitled task"
        status = task.get("status") or "pending"
        when = _format_task_when(task)
        lines.append(f"- `#{task_id}` {description} ({status}, {when})")

    return SlackFormatter.build_message(
        "\n".join(lines),
        title="Tasks",
        footer="Use `cancel task task-id` to cancel a pending task.",
    )


def task_cancel_message(task_id: int, cancelled: bool) -> Dict[str, Any]:
    if cancelled:
        text = f"Cancelled task `#{task_id}`."
    else:
        text = f"Task `#{task_id}` was not found or is no longer pending."

    return SlackFormatter.build_message(text, title="Tasks")


def reminder_created_message(
    *,
    task_id: int,
    description: str,
    scheduled_time: Optional[datetime],
    cron_expression: Optional[str],
) -> Dict[str, Any]:
    if cron_expression:
        timing = f"Recurring schedule: `{cron_expression}`"
    elif scheduled_time:
        timing = f"Scheduled for: `{scheduled_time.strftime('%Y-%m-%d %H:%M')}`"
    else:
        timing = "Scheduled"

    text = f"Created reminder `#{task_id}`\n- {description}\n- {timing}"
    return SlackFormatter.build_message(text, title="Reminder")


def reminder_parse_error_message() -> Dict[str, Any]:
    return SlackFormatter.build_message(
        (
            "Could not parse reminder command.\n\n"
            "Examples:\n"
            "- `remind me to submit report in 2 hours`\n"
            "- `remind me standup update every weekday`\n"
            "- `remind me deploy check at 5pm`\n"
            "- `remind me status update tomorrow 9:30am`"
        ),
        title="Reminder",
    )


def _format_task_when(task: Dict[str, Any]) -> str:
    scheduled_time = task.get("scheduled_time")
    cron_expression = task.get("cron_expression")
    if scheduled_time:
        try:
            dt = datetime.fromtimestamp(int(scheduled_time))
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(scheduled_time)
    if cron_expression:
        return str(cron_expression)
    return "unscheduled"


def channel_stats_message(stats: Dict[str, Any]) -> Dict[str, Any]:
    top_users = stats.get("top_users") or []
    top_user_lines = [
        f"- `<@{user_id}>`: {count} messages"
        for user_id, count in top_users[:5]
    ]
    top_users_text = "\n".join(top_user_lines) if top_user_lines else "- No user messages found"

    text = (
        f"*Messages scanned:* {stats.get('messages_scanned', 0)}\n"
        f"*Unique users:* {stats.get('unique_users', 0)}\n"
        f"*Thread replies:* {stats.get('thread_replies', 0)}\n\n"
        f"*Most active users*\n{top_users_text}"
    )

    return SlackFormatter.build_message(text, title="Channel Stats")


def help_message() -> Dict[str, Any]:
    return SlackFormatter.build_message(
        (
            "*Commands*\n"
            "- `help`\n"
            "- `summarize` or `tldr` inside a thread\n"
            "- `llm options`\n"
            "- `llm show`\n"
            "- `set provider openai|openrouter|gemini|grok`\n"
            "- `set model model-id`\n"
            "- `remind me ...`\n"
            "- `remind me ... at 5pm`\n"
            "- `remind me ... tomorrow 9am`\n"
            "- `my tasks`\n"
            "- `cancel task task-id`\n\n"
            "*Channel*\n"
            "- `channel stats`\n\n"
            "*Reaction shortcuts*\n"
            "- Add `:memo:` or `:page_facing_up:` to summarize a message thread\n"
            "- Add `:bookmark:` to save a message"
        ),
        title="Maantra Assistant",
    )
