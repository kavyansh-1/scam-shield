import pytest

from app.detection.rules import run_rules
from app.detection.urlcheck import assess_url

# (text, expected scam_type)
CRED_SCAMS = [
    "Sir your account will be closed. Please share your account number, IFSC and debit card number for verification.",
    "Dear customer, SBI KYC update pending. Send your card number, expiry date and CVV immediately.",
    "Bank officer bol raha hoon. Apna account number aur card details batao, warna account band ho jayega.",
    "आपका खाता बंद हो जाएगा। अपना कार्ड नंबर बताइए और अकाउंट नंबर भेजिए।",
    "CBI officer here. Send a photo of your Aadhaar and PAN card now.",
    "Please confirm your net banking password and customer ID to avoid account block.",
    "Share your bank details and ATM PIN so we can deposit the refund.",
]
FAMILIES = [
    ("Work from home part time job! Earn Rs 5000 per day. Pay registration fee Rs 999 to start tasks.", "job_task"),
    ("Congratulations you have won the lottery prize money. Pay processing fee Rs 4500 to claim.", "lottery_prize"),
    ("Guaranteed returns 30% monthly. Join our VIP telegram group for trading tips. Deposit now.", "investment"),
    ("Your electricity bill is unpaid, connection will be disconnected tonight. Call 9876501234 immediately.", "utility_disconnect"),
    ("Hi mom this is my new number. My phone is broken. Please send Rs 15000 urgently to this account.", "family_emergency"),
    ("We have your nude video. Pay Rs 20000 or we will make it viral and send to your contacts.", "sextortion"),
    ("Instant loan app no documents. Pay processing fee Rs 1500 to release your loan today.", "loan_app"),
]
SAFE = [
    "Your electricity bill of Rs 800 is due on the 15th. Pay on the official app to avoid late fee.",
    "Dear customer, your account number ending 4321 was credited with Rs 5000.",
    "Mom, I will send the money tomorrow. Dinner at 8.",
    "Please visit your bank branch with your passbook and Aadhaar for KYC update.",
    "Never share your card number, CVV or expiry date with anyone. Bank will never ask.",
    "We are hiring. Apply at the company careers page. Interview at our office.",
    "Your income tax return is filed. Refund will be credited to your bank directly.",
]


@pytest.mark.parametrize("text", CRED_SCAMS)
def test_bank_detail_requests_are_credential_scams(text):
    r = run_rules(text)
    assert any(s.type == "credential_request" for s in r.signals), text
    assert r.score >= 60, (text, r.score)


@pytest.mark.parametrize("text,stype", FAMILIES)
def test_scam_families(text, stype):
    r = run_rules(text)
    assert r.score >= 70 and r.scam_type_guess == stype, (text, r.score, r.scam_type_guess)


@pytest.mark.parametrize("text", SAFE)
def test_new_patterns_do_not_flag_genuine(text):
    r = run_rules(text)
    assert r.score < 35, (text, r.score, [(s.type, s.evidence) for s in r.signals])


def test_multiple_credentials_floor():
    assert run_rules("send your card number and cvv").score >= 70


def test_obfuscated_otp_and_cbi():
    r = run_rules("C.B.I officer. Share O T P now or arrest.")
    assert {s.type for s in r.signals} >= {"authority_impersonation", "credential_request"}


def test_url_heuristics():
    assert assess_url("http://sbi-kyc-update.xyz/login")[0] >= 60
    assert assess_url("https://www.onlinesbi.sbi/login")[0] == 0
    assert assess_url("http://example.com/kyc.apk")[0] >= 60
    assert assess_url("https://bit.ly/abc")[0] >= 35
    assert assess_url("https://www.wikipedia.org/wiki/India")[0] == 0


def test_fake_bank_link_alone_is_scam(client):
    r = client.post("/api/analyze/text", json={"text": "Update here http://hdfc-secure-login.top/verify"}).json()
    assert r["verdict"] == "SCAM" and any(s["type"] == "suspicious_link_or_apk" for s in r["signals"])


def test_new_types_through_api(client):
    r = client.post("/api/analyze/text", json={"text": FAMILIES[0][0]}).json()
    assert r["scam_type"] == "job_task" and r["verdict"] == "SCAM" and r["explanation"]["hi"]


def test_entity_checker(client):
    c = lambda **k: client.post("/api/check/entity", json=k).json()  # noqa: E731
    assert c(value="9999900001")["verdict"] in ("SUSPICIOUS", "SCAM") and c(value="9999900001")["reports"] >= 12
    assert c(value="+923001234567")["verdict"] != "SAFE"
    assert c(value="cbi.officer.test@ybl")["verdict"] == "SCAM"
    assert c(value="police.refund@oksbi")["verdict"] != "SAFE"
    assert c(value="http://sbi-kyc-update.xyz")["verdict"] == "SCAM"
    ok = c(value="https://www.onlinesbi.sbi")
    assert ok["verdict"] == "SAFE" and ok["reasons"] and ok["reasons"][0]["hi"]
    assert client.post("/api/check/entity", json={"value": "hello world"}).status_code == 422


def test_feedback_and_get_analysis(client):
    a = client.post("/api/analyze/text", json={"text": CRED_SCAMS[0]}).json()
    assert client.get(f"/api/analysis/{a['id']}").json()["id"] == a["id"]
    assert client.post("/api/feedback", json={"analysis_id": a["id"], "label": "scam"}).json() == {"saved": True}
    assert client.post("/api/feedback", json={"analysis_id": "nope", "label": "safe"}).status_code == 404


# ---- weighted "ask" detection: what is being ASKED for decides the score ----
@pytest.mark.parametrize("text", [
    "give me your otp and bank details",
    "Please give me OTP, do not tell anyone",
    "tell me the otp sent to your phone",
    "aapka cvv aur card number bhejo",
    "apna UPI PIN batao",
    "OTP chahiye abhi",
    "आपका ओटीपी बताइए",
    "Share your net banking password",
])
def test_asking_for_secrets_is_scam(text):
    assert run_rules(text).score >= 70, text


@pytest.mark.parametrize("text", [
    "Do not share your OTP with anyone", "OTP kisi ko mat bataiye", "Bank will never ask you to share your PIN",
    "Your OTP is 4821. Do not share it.", "Bring your Aadhaar to the branch for KYC update",
    "Aapka OTP 5521 hai. Ye OTP kisi ke saath share na karein.",
])
def test_not_asking_is_not_scam(text):
    assert run_rules(text).score < 35, text


def test_weak_items_alone_are_only_suspicious():
    s = run_rules("Please share your account number and IFSC").score
    assert 35 <= s < 70


def test_score_grows_with_more_items_asked():
    a = run_rules("share your account number").score
    b = run_rules("share your account number and card number").score
    c = run_rules("share your account number, card number, cvv and expiry date").score
    assert a < b < c
