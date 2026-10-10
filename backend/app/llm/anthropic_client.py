import base64

from ..config import settings
from .base import BaseLLM


class AnthropicClient(BaseLLM):
    name = "anthropic"

    def __init__(self):
        from anthropic import AsyncAnthropic
        self.c = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def raw(self, system, user, image, timeout):
        content = []
        if image:
            content.append({"type": "image", "source": {"type": "base64", "media_type": image[1],
                                                       "data": base64.b64encode(image[0]).decode()}})
        content.append({"type": "text", "text": user})
        r = await self.c.messages.create(model=settings.LLM_MODEL, max_tokens=1500, system=system,
                                         messages=[{"role": "user", "content": content}], timeout=timeout)
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
