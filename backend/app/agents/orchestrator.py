"""Live-call agent loop. Deterministic policy: the alert fires when the live score first reaches 70,
even if the LLM is down or slow. The LLM only refines the score and writes the explanation."""
import asyncio
import logging
import time
from typing import Optional

from fastapi import WebSocket

from ..core import spawn
from ..detection.entities import extract_entities
from ..detection.pipeline import analyze_text, llm_classify
from ..detection.rules import RulesResult, run_rules
from ..detection.scoring import final_score, verdict_for
from ..models.schemas import LLMVerdict
from ..services.alerts import create_alert, save_analysis
from .events import bus
from .guardian import dispatch

log = logging.getLogger("scamshield.live")
MAX_CHARS = 20000


class LiveSession:
    def __init__(self, ws: WebSocket, session_id: str, user_id: str):
        self.ws, self.session_id, self.user_id = ws, session_id, user_id
        self.chunks: list[str] = []
        self.sent: set[tuple[str, str]] = set()
        self.alerted = False
        self.analysis_id: Optional[str] = None
        self.llm: Optional[LLMVerdict] = None
        self._llm_task: Optional[asyncio.Task] = None
        self._finals_since_llm = 0
        self._last_llm = time.monotonic()
        self.closed = False

    async def _send(self, payload: dict) -> None:
        if self.closed:
            return
        try:
            await self.ws.send_json(payload)
        except Exception:  # noqa: BLE001
            self.closed = True

    def _score(self, rules: RulesResult) -> int:
        return final_score(rules.score, self.llm.risk_score if self.llm else None, rules.floor)

    async def handle(self, msg: dict) -> None:
        if msg.get("type") == "transcript":
            await self.on_transcript(str(msg.get("text", ""))[:2000], bool(msg.get("is_final", False)))
        elif msg.get("type") == "end":
            await self.on_end(bool(msg.get("save_evidence", False)))

    async def on_transcript(self, text: str, is_final: bool) -> None:
        text = text.strip()
        if not text or sum(map(len, self.chunks)) > MAX_CHARS:
            return
        if is_final:
            self.chunks.append(text)
            self._finals_since_llm += 1
        full = " ".join(self.chunks + ([] if is_final else [text]))
        rules = run_rules(full)
        score = self._score(rules)
        new = []
        for s in rules.signals:
            k = (s.type, s.evidence.lower())
            if k not in self.sent:
                self.sent.add(k)
                new.append(s.model_dump())
        await self._send({"type": "risk_update", "risk_score": score, "verdict": verdict_for(score), "new_signals": new})
        if score >= 70 and not self.alerted:
            self.alerted = True
            bus.publish("live.alert_decision", session=self.session_id, score=score, llm_used=self.llm is not None)
            await self._fire_alert(full)
        if is_final:
            self._maybe_refresh(full, rules)

    def _maybe_refresh(self, full: str, rules: RulesResult) -> None:
        if self._llm_task and not self._llm_task.done():
            return
        if self._finals_since_llm >= 2 or time.monotonic() - self._last_llm > 8:
            self._finals_since_llm, self._last_llm = 0, time.monotonic()
            self._llm_task = spawn(self._refresh(full, rules))

    async def _refresh(self, full: str, rules: RulesResult) -> None:
        v = await llm_classify(full, rules)
        if v:
            self.llm = v

    async def _fire_alert(self, full: str) -> None:
        result = await analyze_text(full, source="live", use_llm=False, llm=self.llm)
        self.analysis_id = result.id
        await save_analysis(result, user_id=self.user_id)
        alert_id = await create_alert(self.user_id, result)
        spawn(dispatch(alert_id))
        await self._send({"type": "scam_alert", "result": result.model_dump(), "alert_id": alert_id})

    async def on_end(self, save_evidence: bool) -> None:
        if self._llm_task:
            self._llm_task.cancel()
        full = " ".join(self.chunks)
        result = await analyze_text(full or " ", source="live", result_id=self.analysis_id)
        await save_analysis(result, user_id=self.user_id, raw_text=full if (save_evidence and full) else None)
        await self._send({"type": "session_summary", "result": result.model_dump(), "analysis_id": result.id})

    def close(self) -> None:
        self.closed = True
        if self._llm_task:
            self._llm_task.cancel()
