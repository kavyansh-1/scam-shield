import logging

from ..core import ApiErr
from ..detection.pipeline import analyze_text
from ..llm.base import get_client
from ..llm.mock_client import MOCK_OCR_TEXT
from ..models.schemas import AnalysisResult, OcrOut

log = logging.getLogger("scamshield.ocr")
OCR_SYSTEM = "You transcribe text from screenshots of messages, chats and call logs. Return every visible piece of text exactly as written, in its original language and script."


async def analyze_image(data: bytes, mime: str) -> AnalysisResult:
    client = get_client()
    if client.name == "mock":
        text = MOCK_OCR_TEXT
    else:
        try:
            out = await client.complete_json(OCR_SYSTEM, "Transcribe all text in this image.", OcrOut,
                                             image=(data, mime), timeout=25)
            text = out.extracted_text
        except Exception as e:  # noqa: BLE001
            log.warning("OCR failed: %s", e)
            raise ApiErr(502, "ocr_failed", "Could not read the image. Please paste the text instead.")
    if not text.strip():
        raise ApiErr(422, "no_text", "No text was found in the image.")
    return await analyze_text(text, source="image", extracted_text=text)
