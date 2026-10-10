"""Offline link heuristics: lookalike bank sites, APKs, shorteners, odd TLDs. No network needed."""
import re
from urllib.parse import urlparse

from ..models.schemas import Bilingual

OFFICIAL = {
    "sbi.co.in", "onlinesbi.sbi", "sbi.bank.in", "hdfcbank.com", "icicibank.com", "axisbank.com", "pnbindia.in",
    "bankofbaroda.in", "kotak.com", "paytm.com", "phonepe.com", "npci.org.in", "uidai.gov.in", "incometax.gov.in",
    "cybercrime.gov.in", "india.gov.in", "irctc.co.in", "rbi.org.in", "amazon.in", "amazon.com", "flipkart.com",
    "google.com", "pay.google.com", "airtel.in", "jio.com", "fedex.com", "dhl.com", "trai.gov.in", "cbi.gov.in",
}
BRANDS = {"sbi", "hdfc", "icici", "axis", "pnb", "kotak", "paytm", "phonepe", "npci", "uidai", "aadhaar", "aadhar",
          "incometax", "irctc", "rbi", "amazon", "flipkart", "fedex", "dhl", "airtel", "jio", "gpay", "bhim", "cbi", "trai"}
SHORT = {"bit.ly", "tinyurl.com", "t.co", "cutt.ly", "rb.gy", "goo.gl", "is.gd", "shorturl.at", "tiny.cc", "wa.me"}
BAD_TLD = {"xyz", "top", "club", "online", "site", "icu", "live", "vip", "cc", "tk", "ml", "ga", "cf", "gq", "click",
           "link", "rest", "work", "buzz", "monster", "cfd", "sbs", "fit", "cyou"}
KEYWORDS = re.compile(r"kyc|update|verif|refund|claim|reward|prize|login|secure|support|helpdesk|care|apk|cashback|lucky|bonus|challan|fastag")


def host_of(url: str) -> str:
    u = url if "://" in url else "http://" + url
    return (urlparse(u).hostname or "").lower().removeprefix("www.")


def is_trusted(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def assess_url(url: str) -> tuple[int, list[Bilingual]]:
    """Returns (risk points 0-100, bilingual reasons)."""
    host = host_of(url)
    if not host or is_trusted(host):
        return 0, []
    low = url.lower()
    pts, why = 0, []

    def add(p: int, en: str, hi: str) -> None:
        nonlocal pts
        pts += p
        why.append(Bilingual(en=en, hi=hi))

    toks = [t for t in re.split(r"[^a-z0-9]+", host) if t]
    brand = next((b for b in BRANDS if any(t == b or (len(b) >= 4 and b in t) for t in toks)), None)
    if brand:
        add(60, f"Pretends to be '{brand}' but is not its official website.", f"'{brand}' बनने की कोशिश है, पर यह उसकी असली वेबसाइट नहीं है।")
    if ".apk" in low:
        add(60, "Links to an APK app file. Real banks never send apps by link.", "APK ऐप फ़ाइल का लिंक है। असली बैंक लिंक से ऐप नहीं भेजते।")
    if host in SHORT:
        add(35, "Shortened link hides the real website.", "छोटा लिंक असली वेबसाइट छुपाता है।")
    if host.rsplit(".", 1)[-1] in BAD_TLD:
        add(30, "Uses a cheap website ending often used for scams.", "ऐसी वेबसाइट का अंत जो अक्सर ठगी में इस्तेमाल होता है।")
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        add(40, "Uses a raw IP address instead of a website name.", "वेबसाइट नाम की जगह IP पता इस्तेमाल हुआ है।")
    if "xn--" in host:
        add(40, "Uses look-alike characters in the website name.", "वेबसाइट के नाम में मिलते-जुलते अक्षर हैं।")
    if "@" in url.split("//", 1)[-1].split("/", 1)[0]:
        add(40, "Hides the real website behind an @ sign.", "@ चिह्न के पीछे असली वेबसाइट छुपाई गई है।")
    if pts and KEYWORDS.search(host + urlparse(url if "://" in url else "http://" + url).path.lower()):
        add(15, "Asks you to verify, update or claim something.", "वेरिफाई, अपडेट या क्लेम करने को कहता है।")
    if pts and host.count("-") >= 3:
        add(15, "Very long, hyphenated website name.", "बहुत लंबा और हाइफ़न वाला वेबसाइट नाम।")
    if pts and low.startswith("http://"):
        add(10, "Not a secure (https) website.", "सुरक्षित (https) वेबसाइट नहीं है।")
    return min(100, pts), why
