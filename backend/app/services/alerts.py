import json
import uuid

from sqlalchemy import select

from ..core import ApiErr
from ..models.db import Alert, Analysis, Guardian, SessionLocal
from ..models.schemas import AnalysisResult


async def save_analysis(result: AnalysisResult, user_id: str | None = None, raw_text: str | None = None) -> None:
    """Upsert an analysis row. raw_text is stored only when the caller passes it (save_evidence=True)."""
    async with SessionLocal() as s:
        row = await s.get(Analysis, result.id)
        if row is None:
            row = Analysis(id=result.id, user_id=user_id, source=result.source, verdict=result.verdict,
                           scam_type=result.scam_type, language=result.language, result_json=result.model_dump_json())
            s.add(row)
        else:
            row.verdict, row.scam_type, row.language = result.verdict, result.scam_type, result.language
            row.result_json = result.model_dump_json()
            row.user_id = row.user_id or user_id
        if raw_text:
            row.raw_text = raw_text
        await s.commit()


async def load_analysis(analysis_id: str) -> tuple[AnalysisResult, str | None]:
    async with SessionLocal() as s:
        row = await s.get(Analysis, analysis_id)
        if not row:
            raise ApiErr(404, "analysis_not_found", "That analysis was not found.")
        return AnalysisResult.model_validate_json(row.result_json), row.raw_text


async def create_alert(user_id: str, result: AnalysisResult) -> str:
    aid = str(uuid.uuid4())
    async with SessionLocal() as s:
        s.add(Alert(id=aid, user_id=user_id, analysis_id=result.id, verdict=result.verdict, scam_type=result.scam_type,
                    risk_score=result.risk_score, summary_json=result.explanation.model_dump_json()))
        await s.commit()
    return aid


async def ack_alert(alert_id: str) -> None:
    async with SessionLocal() as s:
        a = await s.get(Alert, alert_id)
        if not a:
            raise ApiErr(404, "alert_not_found", "Alert not found.")
        a.acked = True
        await s.commit()
