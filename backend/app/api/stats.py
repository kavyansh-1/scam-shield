from collections import Counter
from datetime import timedelta

from fastapi import APIRouter
from sqlalchemy import select

from ..config import settings
from ..core import utcnow
from ..models.db import Analysis, SessionLocal

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
async def stats():
    async with SessionLocal() as s:
        rows = (await s.execute(select(Analysis.verdict, Analysis.scam_type, Analysis.language, Analysis.created_at))).all()
    scams = [r for r in rows if r.verdict == "SCAM"]
    susp = [r for r in rows if r.verdict == "SUSPICIOUS"]
    flagged = scams + susp
    today = utcnow().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    per_day = Counter(r.created_at.date() for r in flagged)
    return {
        "scams_caught": len(scams), "suspicious_flagged": len(susp),
        "est_money_saved_inr": len(scams) * settings.AVG_LOSS_PREVENTED_INR, "is_estimate": True,
        "by_type": [{"scam_type": k, "count": v} for k, v in Counter(r.scam_type for r in flagged).most_common()],
        "by_day": [{"date": d.isoformat(), "count": per_day.get(d, 0)} for d in days],
        "by_language": [{"language": k, "count": v} for k, v in Counter(r.language for r in flagged).most_common()],
    }
