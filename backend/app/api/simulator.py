from fastapi import APIRouter, Depends

from ..agents import coach
from ..core import ApiErr, rate_limit
from ..models.schemas import SimStartReq, SimTurnReq

router = APIRouter(prefix="/api/simulator", tags=["simulator"], dependencies=[Depends(rate_limit)])


@router.post("/start")
async def start(b: SimStartReq):
    sid, msg = await coach.start(b.scenario, b.ui_lang)
    return {"session_id": sid, "scammer_message": msg}


@router.post("/turn")
async def turn(b: SimTurnReq):
    out = await coach.turn(b.session_id, b.user_message)
    if out is None:
        raise ApiErr(404, "session_not_found", "Practice session not found. Please start again.")
    return out
