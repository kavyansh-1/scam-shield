import uuid

from fastapi import APIRouter, Depends

from ..core import rate_limit
from ..models.db import Feedback, SessionLocal
from ..models.schemas import AnalysisResult, EntityCheckReq, FeedbackReq
from ..services.alerts import load_analysis
from ..services.entity_check import check_entity

router = APIRouter(prefix="/api", tags=["check"])


@router.post("/check/entity", dependencies=[Depends(rate_limit)])
async def check(b: EntityCheckReq):
    """Is this phone / UPI ID / link safe? Offline heuristics + community blocklist."""
    return await check_entity(b.value, b.kind)


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str):
    result, _ = await load_analysis(analysis_id)
    return result


@router.post("/feedback")
async def feedback(b: FeedbackReq):
    """'This was wrong' button: stores the user's label so detection can be improved."""
    await load_analysis(b.analysis_id)
    async with SessionLocal() as s:
        s.add(Feedback(id=str(uuid.uuid4()), analysis_id=b.analysis_id, label=b.label, note=b.note))
        await s.commit()
    return {"saved": True}
