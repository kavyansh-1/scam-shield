"""FAST pass (<100 ms): regex rules for en / hi / hinglish with protective-context handling."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..models.schemas import Signal
from .taxonomy import WEIGHTS

_D = json.loads((Path(__file__).parent.parent / "data" / "scam_patterns.json").read_text(encoding="utf-8"))
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize(text: str) -> str:
    """Lowercase + Devanagari digits -> ASCII. Kept 1:1 in length so evidence stays verbatim."""
    return text.lower().translate(_DEVA_DIGITS)


def _compile(p: str) -> re.Pattern:
    p = p.replace(" ?", r"\s*").replace(" ", r"\s+")
    return re.compile(p, re.IGNORECASE)


_PATTERNS = {k: [_compile(p) for p in v] for k, v in _D["signals"].items()}
_PROTECT = [_compile(p) for p in _D["protective"]]
_CRED = re.compile(_D["cred_words"], re.IGNORECASE)
_INFO = [_compile(p) for p in _D["otp_informational"]]
_LURES = {k: re.compile(v, re.IGNORECASE) for k, v in _D["lures"].items()}
_FAMILIES = {k: {"type": v["scam_type"], "weight": v["weight"], "pats": [_compile(p) for p in v["patterns"]]}
             for k, v in _D["families"].items()}
_ITEMS = [(k, v["weight"], v["secret"], [_compile(p) for p in v["patterns"]]) for k, v in _D["credential_items"].items()]
_VERB = _compile(r"\b(?:share|send|give|provide|tell|submit|read out|forward|whatsapp|batao|bataiye|batayiye|bata do|bata dijiye|btao|bhejo|bhejiye|bhej do|bhej dijiye|dijiye|de do|dedo|dena|likho|likhiye|bolo|boliye|chahiye)\b|\b(?:confirm|verify|update) (?:your|ur|the)\b|बताइए|बताओ|बताएं|बताएँ|भेजिए|भेजो|दीजिए|दे दो|बोलिए|चाहिए")
_PROT_BEFORE = _compile(r"(?:do not|don'?t|dont|never|should not|shouldn'?t|kabhi|कभी)\s+(?:\w+\s+){0,2}?(?:share|disclose|reveal|give|tell|provide|send|batao|batayein|bataiye|बताएं|बताएँ|शेयर|साझा)\b[^.\n]{0,28}$|never (?:ask|asks|asked)\b[^.\n]{0,30}$|will not ask\b[^.\n]{0,30}$")
_PROT_AFTER = _compile(r"^[^.\n]{0,34}?\b(?:na|mat|nahi|nahin|न|नहीं|मत)\s+(?:karein|kare|karo|karna|batayein|batayen|bataiye|batana|share|dena|dein|dijiye|batao|bhejo)\b|^[^.\n]{0,34}?(?:साझा|शेयर) (?:न|नहीं|ना)\b")
_SENT = re.compile(r"[.!?\n]")
_PHONE_RX = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")
_AMOUNT_RX = re.compile(r"(?:\brs\.?|\binr|₹|\brupees?)\s*\d|\d[\d,]*\s*(?:rs\b|rupees\b|/-)")
_TIME_PRESSURE = re.compile(r"tonight|aaj raat|\btoday (?:night|itself)\b|\bat \d{1,2}[:.]?\d{0,2} ?(?:pm|am)\b|\bwithin \d+", re.I)


@dataclass
class RulesResult:
    score: int = 0
    floor: int = 0
    signals: list = field(default_factory=list)
    scam_type_guess: str = "none"
    lures: set = field(default_factory=set)


def _any(patterns, s: str) -> bool:
    return any(p.search(s) for p in patterns)


def _asked_items(norm: str) -> list:
    """Sensitive items someone is ASKING for (a request verb in the same sentence, no protective wording)."""
    found, seen = [], set()
    for key, w, secret, pats in _ITEMS:
        for p in pats:
            hit = None
            for m in p.finditer(norm):
                s, e = m.span()
                pre = _SENT.split(norm[max(0, s - 70):s])[-1]
                post = _SENT.split(norm[e:e + 45])[0]
                if not (_VERB.search(pre) or _VERB.search(post)):
                    continue
                if _PROT_BEFORE.search(pre) or _PROT_AFTER.search(post):
                    continue
                hit = (s, e)
                break
            if hit and key not in seen:
                seen.add(key)
                found.append((key, w, secret, hit[0], hit[1]))
                break
    return found


def run_rules(text: str) -> RulesResult:
    norm = normalize(text)
    same_len = len(norm) == len(text)
    signals: list[Signal] = []
    total = 0
    asked = _asked_items(norm)
    for stype, patterns in _PATTERNS.items():
        seen: set[str] = set()
        spans: list[tuple[int, int]] = []
        asked_score, n_asked = 0, 0
        if stype == "credential_request":
            for key, w, _secret, s, e in asked:
                ev = (text if same_len else norm)[s:e].strip()[:100]
                signals.append(Signal(type=stype, evidence=ev, weight=min(30, w)))
                seen.add(ev.lower())
                spans.append((s, e))
                asked_score += w
                n_asked += 1
        cands = sorted({m.span() for p in patterns for m in p.finditer(norm)}, key=lambda se: (-(se[1] - se[0]), se[0]))
        for s, e in cands:  # longest match first, so a full request phrase beats a bare keyword inside it
            if any(s < b and a < e for a, b in spans):
                continue
            window = norm[max(0, s - 60): e + 60]
            if stype == "credential_request" and (_any(_PROTECT, window) or _any(_INFO, window)):
                continue
            if stype == "isolation" and _any(_PROTECT, window) and _CRED.search(window):
                continue
            ev = (text if same_len else norm)[s:e].strip()[:100]
            if not ev or ev.lower() in seen:
                continue
            seen.add(ev.lower())
            spans.append((s, e))
            signals.append(Signal(type=stype, evidence=ev, weight=10 if stype == "credential_request" else WEIGHTS[stype]))
        if stype == "credential_request":
            total += min(100, asked_score) + (10 if len(seen) > n_asked else 0)  # bare mention = weak hint only
        elif seen:
            total += WEIGHTS[stype] + min(6, 3 * (len(seen) - 1))
    fam_hit: set[str] = set()
    for fam, cfg in _FAMILIES.items():
        for p in cfg["pats"]:
            m = p.search(norm)
            if m:
                ev = (text if same_len else norm)[m.start():m.end()].strip()[:100]
                signals.append(Signal(type="scam_lure", evidence=ev, weight=cfg["weight"]))
                total += cfg["weight"]
                fam_hit.add(fam)
                break
    types = {s.type for s in signals}
    lures = {k for k, p in _LURES.items() if p.search(norm)} | fam_hit
    n_cred = len(asked)  # number of different sensitive items being asked for
    has_phone, has_amount = bool(_PHONE_RX.search(norm)), bool(_AMOUNT_RX.search(norm))

    floor = 0

    def raise_floor(v: int, cond: bool = True) -> None:
        nonlocal floor
        if cond:
            floor = max(floor, v)

    raise_floor(85, {"remote_access", "payment_demand"} <= types)
    raise_floor(85, "authority_impersonation" in types and bool(types & {"isolation", "payment_demand"}))
    raise_floor(70, any(a[2] for a in asked))  # asking for OTP / PIN / CVV / card no. / password = scam
    raise_floor(75, {"credential_request", "urgency_threat"} <= types and n_cred >= 1)
    raise_floor(75, n_cred >= 1 and "authority_impersonation" in types)
    raise_floor(70, sum(1 for a in asked if a[1] >= 25) >= 2)  # asking for several credentials at once (card no + CVV + expiry ...)
    raise_floor(60, "bank" in lures and n_cred >= 1)
    raise_floor(75, "suspicious_link_or_apk" in types and bool(types & {"urgency_threat", "credential_request", "payment_demand"}))
    raise_floor(75, "upi_collect_trick" in types)
    raise_floor(75, "payment_demand" in types and bool(lures & {"lottery", "investment", "job_task", "loan"}))
    raise_floor(70, "job_task" in lures and "suspicious_link_or_apk" in types)
    raise_floor(70, "loan" in lures and "urgency_threat" in types)
    raise_floor(65, "sextortion" in lures)
    raise_floor(80, "sextortion" in lures and bool(types & {"payment_demand", "urgency_threat"}))
    raise_floor(70, "utility" in lures and (has_phone or bool(_TIME_PRESSURE.search(norm)) or "urgency_threat" in types))
    raise_floor(70, "family" in lures and has_amount)
    raise_floor(70, "army" in lures and bool(types & {"upi_collect_trick", "payment_demand"}))

    return RulesResult(
        score=min(100, max(total, floor)), floor=floor, signals=signals,
        scam_type_guess=_guess_type(types, lures, norm), lures=lures,
    )


_FAM_TYPE = {k: v["type"] for k, v in _FAMILIES.items()}
_FAM_ORDER = ["sextortion", "loan", "lottery", "job_task", "investment", "utility", "family"]


def _guess_type(types: set, lures: set, norm: str) -> str:
    if not types:
        return "none"
    if "authority_impersonation" in types and types & {"isolation", "payment_demand", "urgency_threat", "remote_access"}:
        return "digital_arrest"
    if "upi_collect_trick" in types:
        return "upi_collect"
    if "remote_access" in types:
        return "remote_access"
    for fam in _FAM_ORDER:
        if fam in lures:
            return _FAM_TYPE[fam]
    if "kyc" in lures or ("bank" in lures and types & {"credential_request", "suspicious_link_or_apk"}) \
            or (types & {"suspicious_link_or_apk", "credential_request"} and "bank" in norm):
        return "fake_kyc"
    if "courier" in lures:
        return "courier_parcel"
    return "other"
