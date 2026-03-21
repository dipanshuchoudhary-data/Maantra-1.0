import os
from openai import AsyncOpenAI

from src.llm.base_provider import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):

    def __init__(self):

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY missing")

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        self.model = os.getenv(
            "MODEL_NAME",
            os.getenv(
                "DEFAULT_MODEL",
                "meta-llama/llama-3.1-8b-instruct",
            ),
        )

    async def chat(self, messages, tools=None):

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )

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
