"""Rules + entities + blocklist + (optional) LLM -> AnalysisResult. The LLM is never required."""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

from ..core import iso, utcnow
from ..llm.base import get_client
from ..models.schemas import (SCAM_TYPES, SIGNAL_TYPES, AnalysisResult, Entities, LLMVerdict, Signal)
from ..services.blocklist import check_entities
from .entities import extract_entities
from .explain import explain
from .lang import detect_language
from .rules import RulesResult, run_rules
from .scoring import final_score, verdict_for
from .urlcheck import assess_url

log = logging.getLogger("scamshield.pipeline")
CLASSIFY_PROMPT = (Path(__file__).parent.parent / "llm" / "prompts" / "classify.md").read_text(encoding="utf-8")


async def llm_classify(text: str, rules: RulesResult, timeout: float = 12) -> Optional[LLMVerdict]:
    """Returns None on ANY failure so callers fall back to rules-only."""
    try:
        hint = {"score": rules.score, "scam_type": rules.scam_type_guess,
                "signals": [s.model_dump() for s in rules.signals]}
        return await asyncio.wait_for(
            get_client().complete_json(CLASSIFY_PROMPT, f"Analyse this content:\n<<<\n{text[:8000]}\n>>>",
                                       LLMVerdict, timeout=timeout, hint=hint), timeout + 3)
    except Exception as e:  # noqa: BLE001
        log.warning("LLM classify failed, rules-only: %s", e)
        return None


def build_result(text: str, rules: RulesResult, ent: Entities, hits, llm: Optional[LLMVerdict],
                 source: str = "text", result_id: Optional[str] = None,
                 extracted_text: Optional[str] = None) -> AnalysisResult:
    sigs = list(rules.signals)
    rscore, floor = rules.score, rules.floor
    for h in hits:
        sigs.append(Signal(type="known_bad_entity", evidence=h.value, weight=30))
    if hits:
        rscore, floor = min(100, rscore + 30), max(floor, 70)
    for u in ent.urls:  # offline link heuristics (lookalike bank sites, APKs, shorteners ...)
        pts, _ = assess_url(u)
        if pts >= 35:
            w = 25 if pts >= 60 else 15
            if not any(s.type == "suspicious_link_or_apk" and (s.evidence.lower() in u.lower() or u.lower() in s.evidence.lower()) for s in sigs):
                sigs.append(Signal(type="suspicious_link_or_apk", evidence=u[:100], weight=w))
                rscore = min(100, rscore + w)
            if pts >= 60:
                floor = max(floor, 70)
    low = text.lower()
    if llm:
        have = {(s.type, s.evidence.lower()) for s in sigs}
        for s in llm.signals:
            ev = s.evidence.strip()
            if s.type in SIGNAL_TYPES and ev and ev.lower() in low and (s.type, ev.lower()) not in have:
                sigs.append(Signal(type=s.type, evidence=ev[:100], weight=max(1, min(30, s.weight))))
    score = final_score(rscore, llm.risk_score if llm else None, floor)
    verdict = verdict_for(score)
    if verdict == "SAFE":
        stype = "none"
    elif llm and llm.scam_type in SCAM_TYPES and llm.scam_type != "none":
        stype = llm.scam_type
    else:
        stype = rules.scam_type_guess if rules.scam_type_guess != "none" else "other"
    exp, acts = explain(stype, verdict)
    if llm and llm.explanation.en.strip() and llm.explanation.hi.strip():
        exp = llm.explanation
    if llm and len(llm.actions) >= 2:
        acts = llm.actions[:4]
    sigs.sort(key=lambda s: -s.weight)
    return AnalysisResult(
        id=result_id or str(uuid.uuid4()), source=source, risk_score=score, verdict=verdict, scam_type=stype,
        language=detect_language(text), signals=sigs[:12], explanation=exp, actions=acts[:4], entities=ent,
        blocklist_hits=list(hits), extracted_text=extracted_text, created_at=iso(utcnow()),
    )


async def analyze_text(text: str, source: str = "text", use_llm: bool = True, llm: Optional[LLMVerdict] = None,
                       result_id: Optional[str] = None, extracted_text: Optional[str] = None) -> AnalysisResult:
    rules = run_rules(text)
    ent = extract_entities(text)
    hits = await check_entities(ent)
    if llm is None and use_llm:
        llm = await llm_classify(text, rules)
    return build_result(text, rules, ent, hits, llm, source, result_id, extracted_text)
