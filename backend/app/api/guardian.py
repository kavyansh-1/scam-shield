import random
import uuid

from fastapi import APIRouter
from sqlalchemy import delete, select

from ..core import ApiErr
from ..models.db import Guardian, SessionLocal, User
from ..models.schemas import GuardianLinkReq
from ..services import telegram

router = APIRouter(prefix="/api/guardian", tags=["guardian"])
_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _code() -> str:
    return "".join(random.choice(_ALPHA) for _ in range(6))


@router.post("/link")
async def link(b: GuardianLinkReq):
    uid = b.user_id or str(uuid.uuid4())
    mock = not telegram.is_live()  # no bot token: auto-link so the demo flow completes
    async with SessionLocal() as s:
        u = await s.get(User, uid)
        if u:
            u.name, u.phone = b.user_name, b.user_phone
        else:
            s.add(User(id=uid, name=b.user_name, phone=b.user_phone))
        await s.execute(delete(Guardian).where(Guardian.user_id == uid))
        gid, code = str(uuid.uuid4()), _code()
        s.add(Guardian(id=gid, user_id=uid, name=b.guardian_name, relation=b.relationship, role="primary", link_code=code, linked=mock))
        code2 = None
        if b.secondary:
            code2 = _code()
            s.add(Guardian(id=str(uuid.uuid4()), user_id=uid, name=b.secondary.name, relation=b.secondary.relationship,
                           role="secondary", link_code=code2, linked=mock))
        await s.commit()
    out = {"user_id": uid, "guardian_id": gid, "link_code": code, "telegram_deep_link": telegram.deep_link(code)}
    if code2:
        out["secondary_link_code"] = code2
    return out


@router.get("/{user_id}")
async def get_guardians(user_id: str):
    async with SessionLocal() as s:
        rows = (await s.execute(select(Guardian).where(Guardian.user_id == user_id).order_by(Guardian.role))).scalars().all()
    return {"guardians": [{"id": g.id, "name": g.name, "relationship": g.relation, "linked": g.linked, "role": g.role} for g in rows]}
