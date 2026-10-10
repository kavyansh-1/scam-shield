import re

_HINGLISH = set(
    "hai hain nahi nahin ka ki ke ko se mein me par pe aap aapka aapke aapki main mera meri hum tum ye yeh "
    "wo woh kya kyun kaise karo kijiye kare karein kiya hoga hoon ho tha thi abhi turant warna lekin aur "
    "bhi toh sir ji paisa paise bata batana batao bhej bhejo rakho dena lena liya wala wali jaldi "
    "giraftar khata khate band sahi theek".split()
)
_DEVA = re.compile(r"[\u0900-\u097F]")
_LATIN = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> str:
    deva = len(_DEVA.findall(text))
    latin = len(_LATIN.findall(text))
    if deva + latin == 0:
        return "en"
    ratio = deva / (deva + latin)
    if ratio >= 0.7:
        return "hi"
    if ratio >= 0.1:
        return "hinglish"
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return "en"
    hits = sum(1 for w in words if w in _HINGLISH)
    return "hinglish" if hits >= 2 and hits / len(words) >= 0.1 else "en"
