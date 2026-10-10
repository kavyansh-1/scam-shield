"""Practice mode: a fictional scammer (LLM or scripted) + deterministic safety coaching."""
import asyncio
import json
import logging
import re
import uuid
from pathlib import Path

from ..llm.base import get_client
from ..models.db import SessionLocal, SimSession
from ..models.schemas import Bilingual, SimSay

log = logging.getLogger("scamshield.coach")
SIM_PROMPT = (Path(__file__).parent.parent / "llm" / "prompts" / "simulator.md").read_text(encoding="utf-8")
MAX_TURNS = 8

SCRIPTS = {
    "en": {
        "digital_arrest": ["Hello, I am Inspector Rao from the CBI cyber crime branch. A parcel in your name has illegal items.",
                           "A warrant is ready. You will be arrested unless you cooperate right now.",
                           "This is confidential. Do not tell anyone, and stay on this video call.",
                           "To clear your name, tell me the OTP you just received. It is only for verification.",
                           "Install the AnyDesk app so I can check your phone. Do it immediately.",
                           "Now transfer the verification deposit to the RBI safe account. It is refundable."],
        "fake_kyc": ["Hello sir, this is the bank KYC team. Your account will be blocked today.",
                     "Please share your Aadhaar and the OTP sent to your phone to update KYC.",
                     "This is urgent. The account will be frozen within 30 minutes.",
                     "Click the link I am sending and enter your card number and PIN.",
                     "Sir, only a small fee of Rs 10 is needed. Please pay now.",
                     "Last warning, sir. Share the OTP now or lose your account."],
        "upi_refund": ["Hello, your order is cancelled and a refund of Rs 4,999 is ready.",
                       "I have sent a collect request. Please approve it to receive the refund.",
                       "Enter your UPI PIN to receive the money. It is needed for credit.",
                       "The refund will expire soon. Please enter the PIN now.",
                       "Sir, tell me the OTP so I can complete your refund.",
                       "Last chance. Install QuickSupport so I can fix it for you."],
    },
    "hi": {
        "digital_arrest": ["नमस्ते, मैं CBI साइबर क्राइम से इंस्पेक्टर राव बोल रहा हूँ। आपके नाम के पार्सल में गैरकानूनी सामान मिला है।",
                           "आपके खिलाफ वारंट निकल चुका है। सहयोग नहीं किया तो गिरफ़्तारी होगी।",
                           "यह गोपनीय मामला है। किसी को मत बताना और वीडियो कॉल पर बने रहें।",
                           "नाम साफ़ करने के लिए अभी आया हुआ OTP बताइए।",
                           "AnyDesk ऐप डाउनलोड करें ताकि मैं आपका फोन जाँच सकूँ।",
                           "अब वेरिफिकेशन डिपॉजिट RBI सेफ अकाउंट में ट्रांसफर करें। यह रिफंडेबल है।"],
        "fake_kyc": ["नमस्ते, मैं बैंक KYC टीम से बोल रहा हूँ। आज आपका खाता ब्लॉक हो जाएगा।",
                     "KYC अपडेट के लिए अपना आधार और OTP बताइए।",
                     "यह ज़रूरी है। 30 मिनट के अंदर खाता बंद हो जाएगा।",
                     "मैं एक लिंक भेज रहा हूँ, उस पर कार्ड नंबर और PIN डालें।",
                     "सिर्फ़ 10 रुपये की फीस लगेगी, अभी भुगतान करें।",
                     "आखिरी चेतावनी। अभी OTP बताइए वरना खाता बंद।"],
        "upi_refund": ["नमस्ते, आपका ऑर्डर रद्द हुआ और 4,999 रुपये का रिफंड तैयार है।",
                       "मैंने कलेक्ट रिक्वेस्ट भेजी है, रिफंड पाने के लिए उसे मंज़ूर करें।",
                       "पैसे पाने के लिए अपना UPI पिन डालिए।",
                       "रिफंड जल्दी खत्म हो जाएगा, अभी पिन डालें।",
                       "OTP बताइए ताकि मैं रिफंड पूरा कर सकूँ।",
                       "आखिरी मौका। QuickSupport इंस्टॉल करें।"],
    },
}
HANGUP = re.compile(r"hang ?up|cut (?:the )?call|disconnect|\bbye\b|call kat|kaat raha|kat raha|phone rakh|band kar|कॉल काट|फोन रख|काट रहा|काट रही", re.I)
REFUSE = re.compile(r"\b(no|not|won'?t|wont|never|nahi|nahin|nhi|refuse|scam|fraud|fake|1930|cybercrime|report|police station)\b|नहीं|ठग|फ्रॉड|मना", re.I)
ASKID = re.compile(r"\b(id|badge|employee|which (?:station|office|branch)|verify|proof|identity|call back|visit)\b|पहचान|सबूत|वेरिफाई", re.I)
UNSAFE = re.compile(r"otp|\b\d{4,}\b|\bpin\b|cvv|anydesk|teamviewer|install|download|\byes sir\b|\bok sir\b|here is|ye lo|bhej raha|bhej rahi|sending|transfer|aadhaar|ओटीपी|पिन|डाउनलोड|भेज रहा|भेज रही|ट्रांसफर", re.I)

COACH = {
    "hang": Bilingual(en="Excellent. Hanging up is the safest move.", hi="बहुत बढ़िया। कॉल काट देना सबसे सुरक्षित है।"),
    "safe": Bilingual(en="Good. You refused or asked for proof. Real officers and banks never mind that.", hi="अच्छा। आपने मना किया या सबूत माँगा। असली अधिकारी या बैंक को इससे दिक्कत नहीं होती।"),
    "unsafe": Bilingual(en="Risky. Never share an OTP, PIN or Aadhaar, send money, or install an app for a caller.", hi="जोखिम। कॉल करने वाले को OTP, PIN, आधार न दें, पैसे न भेजें, और कोई ऐप इंस्टॉल न करें।"),
    "neutral": Bilingual(en="Careful. Do not go along with them. Say no, ask for ID, or hang up.", hi="सावधान। उनकी बात न मानें। मना करें, पहचान माँगें या कॉल काट दें।"),
}


def classify_reply(msg: str) -> str:
    if HANGUP.search(msg):
        return "hang"
    refused = bool(REFUSE.search(msg))
    if UNSAFE.search(msg) and not refused:
        return "unsafe"
    return "safe" if refused or ASKID.search(msg) else "neutral"


def _script(scenario: str, lang: str, i: int) -> str:
    lines = SCRIPTS[lang][scenario if scenario in SCRIPTS[lang] else "digital_arrest"]
    return lines[min(i, len(lines) - 1)]


async def _scammer_line(scenario: str, lang: str, history: list[dict], i: int) -> str:
    client = get_client()
    if client.name != "mock":
        try:
            convo = "\n".join(f"{'Scammer' if h['role'] == 'scammer' else 'User'}: {h['text']}" for h in history)
            out = await asyncio.wait_for(client.complete_json(
                SIM_PROMPT, f"Scenario: {scenario}\nLanguage: {lang}\nConversation so far:\n{convo}\n\nWrite the scammer's next message.",
                SimSay, timeout=10), 12)
            if out.scammer_message.strip():
                return out.scammer_message.strip()
        except Exception as e:  # noqa: BLE001
            log.warning("simulator LLM failed, scripted fallback: %s", e)
    return _script(scenario, lang, i)


async def start(scenario: str, ui_lang: str) -> tuple[str, str]:
    msg = await _scammer_line(scenario, ui_lang, [], 0)
    sid = str(uuid.uuid4())
    async with SessionLocal() as s:
        s.add(SimSession(id=sid, scenario=scenario, ui_lang=ui_lang, history_json=json.dumps([{"role": "scammer", "text": msg}])))
        await s.commit()
    return sid, msg


async def turn(session_id: str, user_message: str):
    async with SessionLocal() as s:
        row = await s.get(SimSession, session_id)
        if not row:
            return None
        hist = json.loads(row.history_json)
        if row.done:
            return {"scammer_message": "", "coach": None, "safe_so_far": row.unsafe == 0, "done": True, "final_score": _final(row, False)}
        hist.append({"role": "user", "text": user_message})
        kind = classify_reply(user_message)
        row.turns += 1
        if kind == "unsafe":
            row.unsafe += 1
        elif kind == "neutral":
            row.neutral += 1
        hung = kind == "hang"
        done = hung or row.turns >= MAX_TURNS or row.unsafe >= 2
        scammer = ""
        if not done:
            scammer = await _scammer_line(row.scenario, row.ui_lang, hist, row.turns)
            hist.append({"role": "scammer", "text": scammer})
        else:
            scammer = "(The call ended.)" if row.ui_lang == "en" else "(कॉल खत्म हो गई।)"
        row.done, row.history_json = done, json.dumps(hist)
        out = {"scammer_message": scammer, "coach": COACH[kind].model_dump(), "safe_so_far": row.unsafe == 0, "done": done}
        if done:
            out["final_score"] = _final(row, hung)
        await s.commit()
        return out


def _final(row: SimSession, hung: bool) -> int:
    return max(0, min(100, 100 - 35 * row.unsafe - 10 * row.neutral + (10 if hung else 0)))
