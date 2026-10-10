import json
import time

import pytest

FIX = open("tests/fixtures/digital_arrest.txt", encoding="utf-8").read()
UID = "11111111-1111-4111-8111-111111111111"


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "llm": "mock", "telegram": "mock"}


def test_analyze_digital_arrest(client):
    r = client.post("/api/analyze/text", json={"text": FIX}).json()
    assert r["verdict"] == "SCAM" and len(r["signals"]) >= 3 and r["scam_type"] == "digital_arrest"
    assert r["explanation"]["en"] and r["explanation"]["hi"]


def test_genuine_otp_is_safe(client):
    r = client.post("/api/analyze/text", json={"text": "123456 is your OTP. Do not share this OTP with anyone."}).json()
    assert r["verdict"] == "SAFE"


def test_validation_and_error_shape(client):
    r = client.post("/api/analyze/text", json={"text": "x" * 8001})
    assert r.status_code == 422 and set(r.json()) == {"error", "code"}
    assert client.post("/api/analyze/image", files={"file": ("a.gif", b"GIF89a", "image/gif")}).status_code == 415


def test_blocklist_hit_and_report(client):
    r = client.post("/api/analyze/text", json={"text": "Send money to cbi.officer.test@ybl now"}).json()
    assert r["blocklist_hits"] and r["blocklist_hits"][0]["reports"] >= 7
    n = client.post("/api/blocklist/report", json={"value": "9123456789", "kind": "phone"}).json()["reports"]
    assert client.post("/api/blocklist/report", json={"value": "9123456789", "kind": "phone"}).json()["reports"] == n + 1


def test_image_analysis_mock(client):
    r = client.post("/api/analyze/image", files={"file": ("s.png", b"\x89PNG\r\n", "image/png")}).json()
    assert r["source"] == "image" and r["extracted_text"] and r["verdict"] == "SCAM"


def test_guardian_alert_ack_report_stats(client):
    link = client.post("/api/guardian/link", json={"user_id": UID, "user_name": "Asha", "guardian_name": "Ravi", "relationship": "Son",
                                                    "secondary": {"name": "Meena", "relationship": "Daughter"}}).json()
    assert len(link["link_code"]) == 6 and link["secondary_link_code"]
    gs = client.get(f"/api/guardian/{UID}").json()["guardians"]
    assert {g["role"] for g in gs} == {"primary", "secondary"}
    a = client.post("/api/analyze/text", json={"text": FIX, "save_evidence": True}).json()
    alert = client.post("/api/alerts/send", json={"user_id": UID, "analysis_id": a["id"]}).json()["alert_id"]
    assert client.get(f"/api/alerts/{UID}").json()["alerts"][0]["acked"] is False
    assert client.post(f"/api/alerts/{alert}/ack").json() == {"acked": True}
    assert client.get(f"/api/alerts/{UID}").json()["alerts"][0]["acked"] is True
    rep = client.post("/api/report/generate", json={"analysis_id": a["id"]}).json()
    pdf = client.get(rep["pdf_url"])
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    s = client.get("/api/stats").json()
    assert s["scams_caught"] >= 1 and s["is_estimate"] is True and len(s["by_day"]) == 7


def test_unacked_alert_escalates(client):
    u2 = "22222222-2222-4222-8222-222222222222"
    client.post("/api/guardian/link", json={"user_id": u2, "user_name": "B", "guardian_name": "G", "relationship": "Son"})
    a = client.post("/api/analyze/text", json={"text": FIX}).json()
    client.post("/api/alerts/send", json={"user_id": u2, "analysis_id": a["id"]})
    for _ in range(12):
        al = client.get(f"/api/alerts/{u2}").json()["alerts"][0]
        if al["escalated"]:
            break
        time.sleep(0.5)
    assert al["escalated"] is True


def test_demo_calls(client):
    for v in ("hinglish", "english", "benign"):
        turns = client.get(f"/api/demo/call?variant={v}").json()["turns"]
        assert turns and {"delay_ms", "speaker", "text"} <= set(turns[0])
    assert len(client.get("/api/demo/call?variant=hinglish").json()["turns"]) >= 25


def test_simulator_flow(client):
    s = client.post("/api/simulator/start", json={"scenario": "digital_arrest", "ui_lang": "en"}).json()
    t1 = client.post("/api/simulator/turn", json={"session_id": s["session_id"], "user_message": "Here is my OTP 482913"}).json()
    assert t1["safe_so_far"] is False and t1["coach"]["en"] and not t1["done"]
    t2 = client.post("/api/simulator/turn", json={"session_id": s["session_id"], "user_message": "I will hang up and call 1930"}).json()
    assert t2["done"] is True and 0 <= t2["final_score"] <= 100
    assert client.post("/api/simulator/turn", json={"session_id": "nope", "user_message": "hi"}).status_code == 404


def test_privacy_raw_text_only_if_saved_and_purged(client):
    import asyncio
    from sqlalchemy import select
    from app.models.db import Analysis, SessionLocal
    from app.core import utcnow
    from app.services.purge import purge_once

    a = client.post("/api/analyze/text", json={"text": FIX}).json()
    b = client.post("/api/analyze/text", json={"text": FIX + " saved", "save_evidence": True}).json()

    async def check():
        async with SessionLocal() as s:
            ra, rb = await s.get(Analysis, a["id"]), await s.get(Analysis, b["id"])
            assert ra.raw_text is None and rb.raw_text
            rb.created_at = utcnow().replace(year=2020)
            await s.commit()
        await purge_once()
        async with SessionLocal() as s:
            assert (await s.get(Analysis, b["id"])).raw_text is None

    asyncio.run(check()) if False else client.portal.call(check)
