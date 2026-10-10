"""Deterministic offline LLM stand-in: derives its answer from the rules hint. Needs no API key."""
from ..detection.explain import explain
from ..models.schemas import LLMSignal, LLMVerdict, OcrOut
from .base import BaseLLM

MOCK_OCR_TEXT = (
    "Dear customer, your KYC is expired. Your account will be blocked today. "
    "Click http://bit.ly/kyc-update-now and share your OTP immediately."
)


class MockClient(BaseLLM):
    name = "mock"

    async def raw(self, system, user, image, timeout):  # not used
        return "{}"

    async def complete_json(self, system, user, schema, image=None, timeout=12, hint=None):
        if schema is OcrOut:
            return OcrOut(extracted_text=MOCK_OCR_TEXT)
        if schema is LLMVerdict:
            hint = hint or {}
            score = int(hint.get("score", 0))
            stype = hint.get("scam_type", "none")
            verdict = "SCAM" if score >= 70 else "SUSPICIOUS" if score >= 35 else "SAFE"
            exp, acts = explain(stype, verdict)
            sigs = [LLMSignal(type=s["type"], evidence=s["evidence"], weight=s["weight"]) for s in hint.get("signals", [])]
            return LLMVerdict(risk_score=score, scam_type=stype, signals=sigs, explanation=exp, actions=acts)
        raise ValueError("mock client does not support this schema")
