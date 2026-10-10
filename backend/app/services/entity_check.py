"""Check a single phone number / UPI ID / link before the user trusts or pays it."""
import re

from ..core import ApiErr
from ..detection.entities import UPI_HANDLES, extract_entities
from ..detection.taxonomy import verdict_for
from ..detection.urlcheck import assess_url
from ..models.schemas import Bilingual, Entities
from .blocklist import check_entities, normalize_value

_SCAMMY_NAME = re.compile(r"cbi|police|rbi|refund|kyc|support|helpdesk|care|prize|lottery|officer|customs|reward|cashback|claim", re.I)
_B = Bilingual


def _guess_kind(v: str) -> str:
    e = extract_entities(v)
    if e.upi_ids:
        return "upi"
    if e.urls:
        return "url"
    digits = re.sub(r"\D", "", v)
    if len(digits) >= 8 and re.fullmatch(r"[+\d\s()-]+", v.strip()):
        return "phone"
    if "@" in v:
        return "upi"
    if "." in v:
        return "url"
    raise ApiErr(422, "unknown_kind", "Could not tell if this is a phone number, UPI ID or link.")


async def check_entity(value: str, kind: str | None) -> dict:
    value = value.strip()
    kind = kind or _guess_kind(value)
    pts, why = 0, []

    def add(p: int, en: str, hi: str) -> None:
        nonlocal pts
        pts = max(pts, p)
        why.append(_B(en=en, hi=hi))

    if kind == "phone":
        digits = re.sub(r"\D", "", value)
        if value.startswith("+") and not value.startswith("+91"):
            add(45, "International number. Officers and banks in India do not call from abroad.", "विदेशी नंबर। भारत के अधिकारी या बैंक विदेश से कॉल नहीं करते।")
        else:
            ten = digits[-10:]
            if len(ten) != 10 or ten[0] not in "6789":
                add(30, "This is not a normal Indian mobile number.", "यह सामान्य भारतीय मोबाइल नंबर नहीं है।")
        ent = Entities(phones=[value])
    elif kind == "upi":
        handle = value.split("@")[-1].lower() if "@" in value else ""
        if handle not in UPI_HANDLES:
            add(25, "Unknown UPI handle.", "अज्ञात UPI हैंडल।")
        if _SCAMMY_NAME.search(value.split("@")[0]):
            add(40, "The name uses words like police, refund, KYC or support. Scammers pick such names.", "नाम में पुलिस, रिफंड, KYC या सपोर्ट जैसे शब्द हैं। ठग ऐसे नाम चुनते हैं।")
        ent = Entities(upi_ids=[value])
    else:
        p, w = assess_url(value)
        if p:
            pts, why = p, list(w)
        ent = Entities(urls=[value])

    hits = await check_entities(ent)
    reports = hits[0].reports if hits else 0
    if reports:
        add(90 if reports >= 10 else 70 if reports >= 3 else 45,
            f"Reported by {reports} other user(s) in the community blocklist.", f"समुदाय की ब्लॉकलिस्ट में {reports} उपयोगकर्ताओं ने रिपोर्ट किया है।")
    if not why:
        why.append(_B(en="No warning signs found. This is not a guarantee. Stay careful.", hi="कोई चेतावनी संकेत नहीं मिला। यह गारंटी नहीं है, सावधान रहें।"))
    return {"value": value, "kind": kind, "verdict": verdict_for(pts), "risk_score": pts,
            "reports": reports, "reasons": [r.model_dump() for r in why]}
