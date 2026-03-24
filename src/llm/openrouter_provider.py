import os
from openai import AsyncOpenAI

from src.llm.base_provider import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):

    def __init__(self, model_name: str | None = None):

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY missing")

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        self.model = model_name or os.getenv(
            "MODEL_NAME",
            os.getenv(
                "DEFAULT_MODEL",
                "meta-llama/llama-3.1-8b-instruct",
            ),
        )

    async def chat(self, messages, tools=None):

        # Build request kwargs - only include tools if provided
        kwargs = {
            "model": self.model,
            "messages": messages,
        }

        # Only add tools if provided (saves tokens)
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)

        msg = response.choices[0].message

        tool_calls = []

        if msg.tool_calls:

            for call in msg.tool_calls:

                tool_calls.append(
                    {
                        "id": call.id,
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    }
                )

        return {
            "message": {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": tool_calls,
            },
            "tool_calls": tool_calls,
        }
