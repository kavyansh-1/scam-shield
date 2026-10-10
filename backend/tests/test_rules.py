import time

import pytest

from app.detection.lang import detect_language
from app.detection.rules import run_rules
from app.detection.taxonomy import verdict_for

SCAM = [
    "I am calling from CBI. There is an arrest warrant against you. Do not tell anyone.",
    "Your parcel has drugs. Download AnyDesk and transfer the amount to the RBI safe account.",
    "Aapke khilaaf arrest warrant hai, kisi ko mat batana, CBI officer bol raha hoon.",
    "Turant AnyDesk download karo aur verification deposit safe account mein transfer karo.",
    "मैं सीबीआई से बोल रहा हूँ। आपके खिलाफ वारंट है, किसी को मत बताना।",
    "आपका खाता तुरंत बंद हो जाएगा। अपना ओटीपी बताइए।",
    "Your KYC is expired, account will be blocked. Click http://bit.ly/abc123 and share OTP immediately.",
    "Share your OTP immediately or your account will be blocked today.",
    "Refund ke liye apna UPI PIN enter karo. Collect request approve karo.",
    "Enter your UPI PIN to receive the money. Approve the collect request.",
    "Congratulations! You have won the KBC lottery. Pay processing fee Rs 5000 to claim the prize.",
    "Guaranteed returns of 40% monthly. Double your money. Pay the registration fee now.",
    "Install this APK file http://kyc-update.xyz/bank.apk to keep your account active. Account will be blocked immediately.",
    "Stay on the video call, do not disconnect. Customs officer here. Pay a fine or you will face arrest.",
    "TRAI se bol raha hoon, aapka sim band hoga. Police case hai, kisi ko mat batana.",
]
SAFE = [
    "123456 is your OTP for transaction of Rs 500. Do not share this OTP with anyone.",
    "Your OTP for login is 4821. Valid for 10 minutes. Never share it with anyone.",
    "Dear customer, bank will never ask for your OTP or PIN. Do not share it.",
    "Aapka OTP 5521 hai. Ye OTP kisi ke saath share na karein. Bank kabhi OTP nahi maangta.",
    "आपका ओटीपी 4455 है। इसे किसी से साझा न करें।",
    "Your package from the courier has been delivered. Thank you for shopping.",
    "Hi beta, I sent you Rs 2000 for the fees. Call me when you reach home.",
    "Your KYC is due next month. Please visit your branch with documents. No action needed now.",
    "Thanks for contacting customer care. Your complaint is resolved.",
    "Mom, dinner at 8 tonight. Don't forget to bring the vegetables.",
]


@pytest.mark.parametrize("text", SCAM)
def test_scam_texts_flagged(text):
    r = run_rules(text)
    assert verdict_for(r.score) in ("SCAM", "SUSPICIOUS"), (text, r.score)
    assert r.signals


@pytest.mark.parametrize("text", SAFE)
def test_safe_texts_not_scam(text):
    r = run_rules(text)
    assert verdict_for(r.score) == "SAFE", (text, r.score, [s.type for s in r.signals])


@pytest.mark.parametrize("text", SCAM[:10] + SCAM[12:])
def test_strong_scams_are_scam(text):
    assert run_rules(text).score >= 70, text


def test_protective_otp_has_no_credential_signal():
    r = run_rules("Do not share your OTP with anyone. Never share your PIN.")
    assert not [s for s in r.signals if s.type == "credential_request"]


def test_floors():
    assert run_rules("download anydesk and transfer to safe account").score >= 85
    assert run_rules("CBI officer. kisi ko mat batana").score >= 85
    assert run_rules("share otp immediately").score >= 75


def test_evidence_is_verbatim():
    t = "Main CBI Officer bol raha hoon. KISI KO MAT BATANA."
    for s in run_rules(t).signals:
        assert s.evidence.lower() in t.lower()


def test_devanagari_digits_and_language():
    assert detect_language("hello this is a normal message") == "en"
    assert detect_language("आपका खाता बंद हो जाएगा") == "hi"
    assert detect_language("aapka account band ho jayega, abhi OTP bhejiye") == "hinglish"


def test_rules_are_fast():
    text = open("tests/fixtures/digital_arrest.txt", encoding="utf-8").read() * 8
    t0 = time.perf_counter()
    for _ in range(5):
        run_rules(text)
    assert (time.perf_counter() - t0) / 5 < 0.1
