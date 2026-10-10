"""Guardian agent: alert the primary guardian, escalate to the secondary if nobody acks."""
import asyncio
import json
import logging

from sqlalchemy import select

from ..config import settings
from ..models.db import Alert, Guardian, SessionLocal, User
from ..models.schemas import AnalysisResult
from ..services import telegram
from ..services.alerts import load_analysis
from .events import bus

log = logging.getLogger("scamshield.guardian")


def alert_text(user_name: str, phone: str | None, r: AnalysisResult) -> str:
    quotes = "\n".join(f"  - \"{s.evidence}\"" for s in r.signals[:3]) or "  - (none)"
    return (f"SCAM ALERT for {user_name}" + (f" ({phone})" if phone else "") + "\n"
            f"Type: {r.scam_type.replace('_', ' ')}   Risk: {r.risk_score}/100\n"
            f"What was said:\n{quotes}\n\nPlease call them now.")


async def _notify(g: Guardian | None, text: str, alert_id: str, label: str) -> None:
    if g is None:
        bus.publish("guardian.skipped", alert=alert_id, who=label, reason="no guardian")
        return
    sent = bool(g.chat_id) and await telegram.send_alert(g.chat_id, text, alert_id)
    if not sent and not telegram.is_live():
        log.info("[MOCK TELEGRAM] %s guardian '%s' would receive:\n%s", label, g.name, text)
    bus.publish("guardian.notified", alert=alert_id, who=label, guardian=g.name, sent=sent)


async def dispatch(alert_id: str) -> None:
    async with SessionLocal() as s:
        a = await s.get(Alert, alert_id)
        if not a:
            return
        u = await s.get(User, a.user_id)
        gs = (await s.execute(select(Guardian).where(Guardian.user_id == a.user_id))).scalars().all()
        primary = next((g for g in gs if g.role == "primary"), None)
        secondary = next((g for g in gs if g.role == "secondary"), None)
        analysis_id = a.analysis_id
    try:
        result, _ = await load_analysis(analysis_id)
    except Exception:  # noqa: BLE001
        return
    text = alert_text(u.name if u else "Your family member", u.phone if u else None, result)
    await _notify(primary, text, alert_id, "primary")
    for _ in range(max(1, settings.ACK_TIMEOUT_S)):
        await asyncio.sleep(1)
        async with SessionLocal() as s:
            a = await s.get(Alert, alert_id)
            if a and a.acked:
                bus.publish("guardian.acked", alert=alert_id)
                return
    async with SessionLocal() as s:
        a = await s.get(Alert, alert_id)
        if a and not a.acked:
            a.escalated = True
            await s.commit()
    bus.publish("guardian.escalated", alert=alert_id)
    await _notify(secondary, text, alert_id, "secondary")
