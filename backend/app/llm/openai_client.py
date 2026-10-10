import base64

from ..config import settings
from .base import BaseLLM


class OpenAIClient(BaseLLM):
    name = "openai"

    def __init__(self):
        from openai import AsyncOpenAI
        self.c = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def raw(self, system, user, image, timeout):
        content = [{"type": "text", "text": user}]
        if image:
            url = f"data:{image[1]};base64,{base64.b64encode(image[0]).decode()}"
            content.append({"type": "image_url", "image_url": {"url": url}})
        r = await self.c.chat.completions.create(
            model=settings.LLM_MODEL, response_format={"type": "json_object"}, timeout=timeout,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": content}])
        return r.choices[0].message.content or ""
