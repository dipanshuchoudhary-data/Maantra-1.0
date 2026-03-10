import os
import google.generativeai as genai

from src.llm.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY missing")

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(
            os.getenv("MODEL_NAME", "gemini-1.5-pro")
        )

    async def chat(self, messages, tools=None):

        prompt = "\n".join([m["content"] for m in messages if m.get("content")])

        response = await self.model.generate_content_async(prompt)

        return {
            "message": {
                "role": "assistant",
                "content": response.text,
            },
            "tool_calls": [],
        }