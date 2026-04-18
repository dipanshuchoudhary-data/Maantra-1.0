"""
Slack message formatting helpers.
"""

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
            "- `my tasks`\n"
            "- `cancel task task-id`\n\n"
            "*Reaction shortcuts*\n"
            "- Add `:memo:` or `:page_facing_up:` to summarize a message thread\n"
            "- Add `:bookmark:` to save a message"
        ),
        title="Maantra Assistant",
    )
