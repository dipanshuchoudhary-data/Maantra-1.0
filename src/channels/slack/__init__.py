"""
Slack Channel Adapter

Exports:
- SlackChannelAdapter: Main adapter class for Slack integration
"""

__all__ = ["SlackChannelAdapter"]


def __getattr__(name: str):
    if name == "SlackChannelAdapter":
        from src.channels.slack.handler import SlackChannelAdapter

        return SlackChannelAdapter
    raise AttributeError(name)
