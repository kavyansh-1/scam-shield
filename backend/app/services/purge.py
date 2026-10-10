import asyncio
import logging
from datetime import timedelta

from sqlalchemy import delete, update

from ..config import settings
from ..core import utcnow
from ..models.db import Analysis, SessionLocal, SimSession

log = logging.getLogger("scamshield.purge")


async def purge_once() -> int:
    """Delete raw text / transcripts / practice chats older than DATA_TTL_HOURS."""
    cutoff = utcnow() - timedelta(hours=settings.DATA_TTL_HOURS)
    async with SessionLocal() as s:
        r = await s.execute(update(Analysis).where(Analysis.raw_text.is_not(None), Analysis.created_at < cutoff)
                            .values(raw_text=None))
        await s.execute(delete(SimSession).where(SimSession.created_at < cutoff))
        await s.commit()
        return r.rowcount or 0


async def purge_loop() -> None:
    while True:
        try:
            n = await purge_once()
            if n:
                log.info("purged raw text from %s analyses", n)
        except Exception:  # noqa: BLE001
            log.exception("purge failed")
        await asyncio.sleep(1800)
