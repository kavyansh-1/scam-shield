"""Telegram long-polling bot. With no token it runs in mock mode and only logs."""
import asyncio
import logging
from typing import Optional

import httpx
from sqlalchemy import select

from ..config import settings
from ..models.db import Alert, Guardian, SessionLocal, User

log = logging.getLogger("scamshield.telegram")


def is_live() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)


def deep_link(code: str) -> str:
    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME or 'ScamShieldBot'}?start={code}"


async def _call(client: httpx.AsyncClient, method: str, **payload):
    r = await client.post(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}", json=payload)
    return r.json()


async def send_alert(chat_id: str, text: str, alert_id: str) -> bool:
    if not is_live():
        log.info("[MOCK TELEGRAM] to=%s alert=%s\n%s", chat_id, alert_id, text)
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            res = await _call(c, "sendMessage", chat_id=chat_id, text=text,
                              reply_markup={"inline_keyboard": [[{"text": "I am calling them", "callback_data": f"ack:{alert_id}"}]]})
        return bool(res.get("ok"))
    except Exception as e:  # noqa: BLE001
        log.warning("telegram send failed: %s", e)
        return False


async def _handle(c: httpx.AsyncClient, upd: dict) -> None:
    msg = upd.get("message")
    if msg and str(msg.get("text", "")).startswith("/start"):
        chat_id = str(msg["chat"]["id"])
        parts = msg["text"].split()
        code = parts[1].strip().upper() if len(parts) > 1 else ""
        async with SessionLocal() as s:
            g = (await s.execute(select(Guardian).where(Guardian.link_code == code))).scalar_one_or_none() if code else None
            if g:
                g.chat_id, g.linked = chat_id, True
                u = await s.get(User, g.user_id)
                await s.commit()
                await _call(c, "sendMessage", chat_id=chat_id,
                            text=f"Linked. You will get an alert here if {u.name if u else 'your family member'} may be targeted by a scam.")
            else:
                await _call(c, "sendMessage", chat_id=chat_id, text="That code was not recognised. Ask for a new link in the Scam Shield app.")
    cb = upd.get("callback_query")
    if cb and str(cb.get("data", "")).startswith("ack:"):
        from .alerts import ack_alert
        await ack_alert(cb["data"][4:])
        await _call(c, "answerCallbackQuery", callback_query_id=cb["id"], text="Marked: you are calling them.")
        if cb.get("message"):
            await _call(c, "sendMessage", chat_id=cb["message"]["chat"]["id"], text="Thank you. Please call them now.")


async def poll_loop() -> None:
    if not is_live():
        log.info("Telegram: mock mode (no token)")
        return
    offset: Optional[int] = None
    async with httpx.AsyncClient(timeout=40) as c:
        while True:
            try:
                data = await _call(c, "getUpdates", timeout=25, offset=offset, allowed_updates=["message", "callback_query"])
                for upd in data.get("result", []):
                    offset = upd["update_id"] + 1
                    try:
                        await _handle(c, upd)
                    except Exception:  # noqa: BLE001
                        log.exception("telegram update failed")
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                log.warning("telegram poll error: %s", e)
                await asyncio.sleep(5)
