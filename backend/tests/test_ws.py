import json
import time

UID = "33333333-3333-4333-8333-333333333333"


def _drain_until(ws, kinds, limit=60):
    seen = []
    for _ in range(limit):
        m = ws.receive_json()
        seen.append(m)
        if m["type"] in kinds:
            break
    return seen


def test_ws_flow_alert_exactly_once(client):
    calls = client.get("/api/demo/call?variant=hinglish").json()["turns"]
    msgs = []
    with client.websocket_connect(f"/ws/live?session_id=s1&user_id={UID}") as ws:
        for t in calls:
            ws.send_json({"type": "transcript", "text": t["text"], "is_final": True})
            m = ws.receive_json()
            msgs.append(m)
            while m["type"] != "risk_update":
                m = ws.receive_json()
                msgs.append(m)
        ws.send_json({"type": "end", "save_evidence": False})
        msgs += _drain_until(ws, {"session_summary"})
    alerts = [m for m in msgs if m["type"] == "scam_alert"]
    assert len(alerts) == 1 and alerts[0]["result"]["verdict"] == "SCAM"
    summ = [m for m in msgs if m["type"] == "session_summary"][0]
    assert summ["result"]["id"] == alerts[0]["result"]["id"]
    ups = [m for m in msgs if m["type"] == "risk_update"]
    assert ups[0]["risk_score"] <= ups[-1]["risk_score"] and ups[-1]["risk_score"] >= 70
    # replay timing: time (ms of replay) until the alert fires
    elapsed, fired = 0, None
    run = ""
    from app.detection.rules import run_rules
    for t in calls:
        elapsed += t["delay_ms"]
        run += " " + t["text"]
        if fired is None and run_rules(run).score >= 70:
            fired = elapsed
    print(f"\nalert fires {fired/1000:.1f}s into the replay")
    assert fired <= 25000
    assert any(a["escalated"] is not None for a in client.get(f"/api/alerts/{UID}").json()["alerts"])


def test_ws_benign_call_never_alerts(client):
    calls = client.get("/api/demo/call?variant=benign").json()["turns"]
    types = []
    with client.websocket_connect("/ws/live?session_id=s2&user_id=u2") as ws:
        for t in calls:
            ws.send_json({"type": "transcript", "text": t["text"], "is_final": True})
            m = ws.receive_json()
            types.append(m["type"])
            assert m["risk_score"] < 70
        ws.send_json({"type": "end", "save_evidence": False})
        m = _drain_until(ws, {"session_summary"})[-1]
    assert "scam_alert" not in types and m["result"]["verdict"] == "SAFE"
