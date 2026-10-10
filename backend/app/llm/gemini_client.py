from ..config import settings
from .base import BaseLLM


class GeminiClient(BaseLLM):
    name = "gemini"

    def __init__(self):
        from google import genai
        self.genai = genai
        self.c = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def raw(self, system, user, image, timeout):
        parts = []
        if image:
            parts.append(self.genai.types.Part.from_bytes(data=image[0], mime_type=image[1]))
        parts.append(user)
        r = await self.c.aio.models.generate_content(
            model=settings.LLM_MODEL, contents=parts,
            config={"system_instruction": system, "response_mime_type": "application/json"})
        return r.text or ""
