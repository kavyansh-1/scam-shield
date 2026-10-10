from typing import Literal, Optional

from pydantic import BaseModel, Field

Verdict = Literal["SAFE", "SUSPICIOUS", "SCAM"]
Language = Literal["en", "hi", "hinglish"]
ScamType = Literal[
    "digital_arrest", "fake_kyc", "upi_collect", "remote_access", "courier_parcel",
    "lottery_prize", "investment", "job_task", "utility_disconnect", "family_emergency", "sextortion",
    "loan_app", "other", "none",
]
SignalType = Literal[
    "authority_impersonation", "urgency_threat", "isolation", "remote_access", "payment_demand",
    "credential_request", "suspicious_link_or_apk", "upi_collect_trick", "known_bad_entity", "scam_lure",
]
SCAM_TYPES = set(ScamType.__args__)  # type: ignore[attr-defined]
SIGNAL_TYPES = set(SignalType.__args__)  # type: ignore[attr-defined]


class Bilingual(BaseModel):
    en: str
    hi: str


class Signal(BaseModel):
    type: SignalType
    evidence: str
    weight: int = Field(ge=1, le=30)


class Entities(BaseModel):
    phones: list[str] = Field(default_factory=list)
    upi_ids: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    apps: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)


class BlocklistHit(BaseModel):
    value: str
    kind: Literal["phone", "upi", "url"]
    reports: int


class AnalysisResult(BaseModel):
    id: str
    source: Literal["text", "image", "live"]
    risk_score: int = Field(ge=0, le=100)
    verdict: Verdict
    scam_type: ScamType
    language: Language
    signals: list[Signal]
    explanation: Bilingual
    actions: list[Bilingual]
    entities: Entities
    blocklist_hits: list[BlocklistHit]
    extracted_text: Optional[str] = None
    created_at: str


# ---- requests ----
class AnalyzeTextReq(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    save_evidence: bool = False


class SecondaryIn(BaseModel):
    name: str
    relationship: str


class GuardianLinkReq(BaseModel):
    user_id: Optional[str] = None
    user_name: str
    user_phone: Optional[str] = None
    guardian_name: str
    relationship: str
    secondary: Optional[SecondaryIn] = None


class AlertSendReq(BaseModel):
    user_id: str
    analysis_id: str


class BlocklistReportReq(BaseModel):
    value: str = Field(min_length=3, max_length=300)
    kind: Literal["phone", "upi", "url"]


class ReportGenReq(BaseModel):
    analysis_id: str


class SimStartReq(BaseModel):
    scenario: Literal["digital_arrest", "fake_kyc", "upi_refund"]
    ui_lang: Literal["en", "hi"] = "en"


class SimTurnReq(BaseModel):
    session_id: str
    user_message: str = Field(min_length=1, max_length=1000)


# ---- LLM output schemas (lenient: validated and filtered afterwards) ----
class LLMSignal(BaseModel):
    type: str
    evidence: str
    weight: int = 10


class LLMVerdict(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    scam_type: str = "other"
    signals: list[LLMSignal] = Field(default_factory=list)
    explanation: Bilingual
    actions: list[Bilingual] = Field(default_factory=list)


class OcrOut(BaseModel):
    extracted_text: str


class SimSay(BaseModel):
    scammer_message: str


class EntityCheckReq(BaseModel):
    value: str = Field(min_length=3, max_length=500)
    kind: Optional[Literal["phone", "upi", "url"]] = None


class FeedbackReq(BaseModel):
    analysis_id: str
    label: Literal["scam", "safe"]
    note: Optional[str] = Field(default=None, max_length=300)
