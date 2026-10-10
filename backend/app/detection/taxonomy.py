WEIGHTS = {
    "authority_impersonation": 20, "urgency_threat": 15, "isolation": 25, "remote_access": 25,
    "payment_demand": 25, "credential_request": 20, "suspicious_link_or_apk": 20,
    "upi_collect_trick": 30, "known_bad_entity": 30, "scam_lure": 20,
}
SAFE_MAX, SCAM_MIN = 35, 70


def verdict_for(score: int) -> str:
    return "SCAM" if score >= SCAM_MIN else "SUSPICIOUS" if score >= SAFE_MAX else "SAFE"
