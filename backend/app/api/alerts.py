import json

from fastapi import APIRouter
from sqlalchemy import select

from ..agents.guardian import dispatch
from ..core import ApiErr, iso, spawn
from ..models.db import Alert, SessionLocal, User
from ..models.schemas import AlertSendReq
from ..services.alerts import ack_alert, create_alert, load_analysis

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post("/send")
async def send(b: AlertSendReq):
    result, _ = await load_analysis(b.analysis_id)
    async with SessionLocal() as s:
        if not await s.get(User, b.user_id):
            s.add(User(id=b.user_id, name="Family member"))
            await s.commit()
    alert_id = await create_alert(b.user_id, result)
    spawn(dispatch(alert_id))
    return {"alert_id": alert_id}


@router.get("/{user_id}")
async def list_alerts(user_id: str):
    async with SessionLocal() as s:
        rows = (await s.execute(select(Alert).where(Alert.user_id == user_id).order_by(Alert.created_at.desc()).limit(50))).scalars().all()
    return {"alerts": [{"id": a.id, "created_at": iso(a.created_at), "verdict": a.verdict, "scam_type": a.scam_type,
                        "risk_score": a.risk_score, "summary": json.loads(a.summary_json), "acked": a.acked,
                        "escalated": a.escalated} for a in rows]}


@router.post("/{alert_id}/ack")
async def ack(alert_id: str):
    await ack_alert(alert_id)
    return {"acked": True}
