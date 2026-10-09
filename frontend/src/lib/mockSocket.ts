import type { ClientMsg, ServerMsg, Signal } from "./types";
import { mockResult, mockSignals, uuid } from "./api";

/** Offline stand-in for WS /ws/live, used when NEXT_PUBLIC_MOCK=1. */
export class MockSocket {
  private score = 0;
  private seen = new Set<string>();
  private alerted = false;
  private all = "";
  constructor(private emit: (m: ServerMsg) => void) {}
  send(m: ClientMsg): void {
    if (m.type === "transcript") {
      this.all += " " + m.text;
      const fresh: Signal[] = mockSignals.filter(
        (s) => !this.seen.has(s.type) && this.all.toLowerCase().includes(s.evidence.toLowerCase()),
      );
      const extra = /cbi|arrest|anydesk|safe account|tell anyone/i.test(m.text) ? fresh : [];
      extra.forEach((s) => { this.seen.add(s.type); this.score = Math.min(100, this.score + s.weight + 5); });
      const verdict = this.score >= 70 ? "SCAM" : this.score >= 35 ? "SUSPICIOUS" : "SAFE";
      this.emit({ type: "risk_update", risk_score: this.score, verdict, new_signals: extra });
      if (this.score >= 70 && !this.alerted) {
        this.alerted = true;
        this.emit({ type: "scam_alert", result: mockResult(this.all, "live"), alert_id: uuid() });
      }
    } else {
      const r = mockResult(this.all, "live");
      this.emit({ type: "session_summary", result: r, analysis_id: r.id });
    }
  }
}
