import re

from ..models.schemas import Entities
from .rules import normalize

UPI_HANDLES = (
    "ybl ibl axl apl okaxis oksbi okhdfcbank okicici paytm upi sbi hdfcbank icici axisbank "
    "fbl yesbank barodampay pnb postbank airtel freecharge jupiter slice ikwik waaxis wahdfcbank "
    "waicici wasbi abfspay"
).split()

_PHONE = re.compile(r"(?<![\d])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?![\d])")
_UPI = re.compile(r"\b[a-z0-9][\w.\-]{1,}@(?:%s)\b" % "|".join(UPI_HANDLES), re.IGNORECASE)
_URL = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+|\b(?:bit\.ly|tinyurl\.com|t\.co|cutt\.ly|rb\.gy|goo\.gl|is\.gd|shorturl\.at)/[^\s<>\"']+|[^\s<>\"']+\.apk\b",
    re.IGNORECASE,
)
_APPS = re.compile(r"\b(anydesk|team ?viewer|quick ?support|rust ?desk|ammyy)\b", re.IGNORECASE)
_AMOUNT = re.compile(
    r"(?:\brs\.?|\binr|₹|\brupees?)\s*[\d,]+(?:\.\d+)?|[\d,]+(?:\.\d+)?\s*(?:rs\b|rupees\b|inr\b|/-)", re.IGNORECASE
)


def _uniq(items):
    out, seen = [], set()
    for i in items:
        k = i.lower()
        if k not in seen:
            seen.add(k)
            out.append(i)
    return out


def extract_entities(text: str) -> Entities:
    t = normalize(text)
    t_orig = text.translate(str.maketrans("०१२३४५६७८९", "0123456789"))
    phones = [re.sub(r"[\s-]", "", m.group(0)) for m in _PHONE.finditer(t)]
    upis = [m.group(0) for m in _UPI.finditer(t_orig)]
    urls = [m.group(0).rstrip(".,;:)!?") for m in _URL.finditer(t_orig)]
    upi_hosts = {u.split("@")[1].lower() for u in upis}
    urls = [u for u in urls if u.lower() not in upi_hosts]
    apps = [m.group(1).lower().replace(" ", "") for m in _APPS.finditer(t)]
    amounts = [m.group(0).strip() for m in _AMOUNT.finditer(t_orig)]
    return Entities(phones=_uniq(phones), upi_ids=_uniq(upis), urls=_uniq(urls), apps=_uniq(apps), amounts=_uniq(amounts))
