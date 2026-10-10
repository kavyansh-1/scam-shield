"""Deterministic bilingual explanations / actions (used when the LLM is mock or unavailable)."""
from ..models.schemas import Bilingual

_B = Bilingual
EXPLAIN = {
    "digital_arrest": _B(en="This is a digital-arrest scam. Real police or CBI never arrest anyone on a call or ask for money.",
                         hi="यह डिजिटल अरेस्ट ठगी है। असली पुलिस या CBI फोन पर गिरफ़्तारी या पैसे की माँग नहीं करती।"),
    "fake_kyc": _B(en="This looks like a fake KYC or bank message. Banks never ask for OTP or PIN, or send update links.",
                   hi="यह नकली KYC या बैंक संदेश लगता है। बैंक कभी OTP, PIN या अपडेट लिंक नहीं भेजते।"),
    "upi_collect": _B(en="This is a UPI trick. You never need to enter a PIN to receive money.",
                      hi="यह UPI की ठगी है। पैसे पाने के लिए कभी PIN नहीं डालना पड़ता।"),
    "remote_access": _B(en="The caller wants control of your phone. Never install AnyDesk or similar apps for a stranger.",
                        hi="कॉल करने वाला आपके फोन का कंट्रोल चाहता है। अजनबी के कहने पर AnyDesk जैसे ऐप कभी इंस्टॉल न करें।"),
    "courier_parcel": _B(en="This looks like a fake parcel or courier scare. Do not pay or share details.",
                         hi="यह नकली पार्सल या कूरियर की धमकी लगती है। पैसे न दें और जानकारी न बताएँ।"),
    "lottery_prize": _B(en="This is a fake prize message. Real prizes never ask you to pay a fee first.",
                        hi="यह नकली इनाम का संदेश है। असली इनाम के लिए पहले फीस नहीं माँगी जाती।"),
    "investment": _B(en="This looks like an investment scam. No one can guarantee high returns.",
                     hi="यह निवेश की ठगी लगती है। कोई भी ऊँचे मुनाफ़े की गारंटी नहीं दे सकता।"),
    "job_task": _B(en="This is a fake online job or task scam. Real jobs never ask you to pay or deposit money first.",
                   hi="यह नकली ऑनलाइन नौकरी या टास्क की ठगी है। असली नौकरी में पहले पैसे नहीं माँगे जाते।"),
    "utility_disconnect": _B(en="This is a fake bill-disconnection threat. Check your bill on the official app or office, not this number.",
                             hi="यह बिल कटने की नकली धमकी है। बिल आधिकारिक ऐप या दफ़्तर से जाँचें, इस नंबर से नहीं।"),
    "family_emergency": _B(en="This may be someone pretending to be your relative. Call your family member on their old number before sending money.",
                           hi="कोई आपका रिश्तेदार बनकर ठग सकता है। पैसे भेजने से पहले उनके पुराने नंबर पर कॉल करके पूछें।"),
    "sextortion": _B(en="This is blackmail with a fake video threat. Do not pay. Stop talking to them and report it.",
                     hi="यह नकली वीडियो की धमकी देकर ब्लैकमेल है। पैसे न दें, बात बंद करें और रिपोर्ट करें।"),
    "loan_app": _B(en="This looks like a loan-app scam. Real lenders do not take a fee first or use your contacts to threaten you.",
                   hi="यह लोन ऐप की ठगी लगती है। असली कंपनी पहले फीस नहीं लेती और आपके कॉन्टैक्ट से धमकाती नहीं।"),
    "other": _B(en="This message has warning signs of a scam. Do not act on it before checking.",
                hi="इस संदेश में ठगी के संकेत हैं। जाँचे बिना कुछ न करें।"),
    "none": _B(en="No clear scam signs found. Still, never share your OTP or PIN with anyone.",
               hi="ठगी के साफ़ संकेत नहीं मिले। फिर भी OTP या PIN किसी को न बताएँ।"),
}
ACTIONS_SCAM = [
    _B(en="Cut the call or stop replying now.", hi="कॉल अभी काट दें या जवाब देना बंद करें।"),
    _B(en="Do not send money or share OTP, PIN or Aadhaar.", hi="पैसे न भेजें, OTP, PIN या आधार न बताएँ।"),
    _B(en="Tell a family member you trust.", hi="किसी भरोसेमंद परिवारजन को बताएँ।"),
    _B(en="Call 1930 and report at cybercrime.gov.in.", hi="1930 पर कॉल करें और cybercrime.gov.in पर रिपोर्ट करें।"),
]
ACTIONS_SUSPICIOUS = [
    _B(en="Do not click links or share any code.", hi="किसी लिंक पर क्लिक न करें, कोई कोड न बताएँ।"),
    _B(en="Call your bank on the number printed on your card.", hi="अपने कार्ड पर छपे नंबर से बैंक को कॉल करें।"),
    _B(en="Ask a family member before you act.", hi="कुछ करने से पहले परिवार से पूछें।"),
]
ACTIONS_SAFE = [
    _B(en="No action needed.", hi="कुछ करने की ज़रूरत नहीं।"),
    _B(en="Never share your OTP or PIN.", hi="OTP या PIN कभी किसी को न बताएँ।"),
]


def explain(scam_type: str, verdict: str) -> tuple[Bilingual, list[Bilingual]]:
    if verdict == "SAFE":
        return EXPLAIN["none"], ACTIONS_SAFE
    exp = EXPLAIN.get(scam_type, EXPLAIN["other"])
    return exp, (ACTIONS_SCAM if verdict == "SCAM" else ACTIONS_SUSPICIOUS)
