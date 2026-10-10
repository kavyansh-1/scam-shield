# Scam Shield API contract

Single source of truth for the backend (`backend/`) and frontend (`frontend/`).
Errors always look like `{ "error": string, "code": string }`.

## Enums
- **Verdict:** `SAFE | SUSPICIOUS | SCAM`. Thresholds: score < 35 SAFE; 35-69 SUSPICIOUS; >= 70 SCAM
- **Language:** `en | hi | hinglish` (detected language of the analysed content)
- **UiLang:** `en | hi`
- **ScamType:** `digital_arrest | fake_kyc | upi_collect | remote_access | courier_parcel | lottery_prize | investment | job_task | utility_disconnect | family_emergency | sextortion | loan_app | other | none`
- **SignalType:** `authority_impersonation | urgency_threat | isolation | remote_access | payment_demand | credential_request | suspicious_link_or_apk | upi_collect_trick | known_bad_entity | scam_lure`
- **Bilingual:** `{ "en": string, "hi": string }`

## AnalysisResult
```
{ id: uuid, source: "text"|"image"|"live", risk_score: int 0-100, verdict: Verdict,
  scam_type: ScamType, language: Language,
  signals: [{ type: SignalType, evidence: string (verbatim quote), weight: int 1-30 }],
  explanation: Bilingual (max 2 short sentences each),
  actions: [Bilingual] (2-4 imperative steps),
  entities: { phones: string[], upi_ids: string[], urls: string[], apps: string[], amounts: string[] },
  blocklist_hits: [{ value: string, kind: "phone"|"upi"|"url", reports: int }],
  extracted_text?: string (image only), created_at: ISO-8601 }
```

## Endpoints
| Method and path | Request | Response |
|---|---|---|
| `GET /api/health` | | `{ status: "ok", llm: provider, telegram: "live"\|"mock" }` |
| `POST /api/analyze/text` | `{ text (<=8000), save_evidence? }` | AnalysisResult |
| `POST /api/analyze/image` | multipart `file` (png/jpg/webp, <=6MB), `save_evidence?` | AnalysisResult |
| `GET /api/analysis/{id}` | | AnalysisResult |
| `POST /api/feedback` | `{ analysis_id, label: "scam"\|"safe", note? }` | `{ saved: true }` |
| `POST /api/check/entity` | `{ value, kind?: "phone"\|"upi"\|"url" }` | `{ value, kind, verdict, risk_score, reports, reasons: Bilingual[] }` |
| `POST /api/guardian/link` | `{ user_id?, user_name, user_phone?, guardian_name, relationship, secondary?: { name, relationship } }` | `{ user_id, guardian_id, link_code (6 chars), telegram_deep_link, secondary_link_code? }` |
| `GET /api/guardian/{user_id}` | | `{ guardians: [{ id, name, relationship, linked, role: "primary"\|"secondary" }] }` |
| `POST /api/alerts/send` | `{ user_id, analysis_id }` | `{ alert_id }` |
| `GET /api/alerts/{user_id}` | | `{ alerts: [{ id, created_at, verdict, scam_type, risk_score, summary: Bilingual, acked, escalated }] }` |
| `POST /api/alerts/{alert_id}/ack` | | `{ acked: true }` |
| `POST /api/blocklist/report` | `{ value, kind }` | `{ value, kind, reports }` |
| `POST /api/report/generate` | `{ analysis_id }` | `{ report_id, pdf_url }` |
| `GET /api/report/{report_id}.pdf` | | `application/pdf` |
| `GET /api/stats` | | `{ scams_caught, suspicious_flagged, est_money_saved_inr, is_estimate: true, by_type, by_day, by_language }` |
| `POST /api/simulator/start` | `{ scenario: "digital_arrest"\|"fake_kyc"\|"upi_refund", ui_lang }` | `{ session_id, scammer_message }` |
| `POST /api/simulator/turn` | `{ session_id, user_message }` | `{ scammer_message, coach: Bilingual\|null, safe_so_far, done, final_score? }` |
| `GET /api/demo/call?variant=hinglish\|english\|benign` | | `{ turns: [{ delay_ms, speaker: "scammer"\|"victim", text }] }` |

## WebSocket `/ws/live?session_id=<uuid>&user_id=<uuid>`
- client to server: `{ type: "transcript", text, is_final }` and `{ type: "end", save_evidence }`
- server to client:
  - `{ type: "risk_update", risk_score, verdict, new_signals: Signal[] }`
  - `{ type: "scam_alert", result: AnalysisResult, alert_id }` (sent **once** per session, when the score first reaches 70)
  - `{ type: "session_summary", result: AnalysisResult, analysis_id }`

## Alert flow
`scam_alert` creates an Alert and messages the primary guardian on Telegram (user name, phone if given, scam type, top 3 evidence quotes, risk score) with an inline button "I am calling them". No ack within `ACK_TIMEOUT_S` sends it to the secondary guardian and sets `escalated=true`. In mock mode (no bot token) Telegram is skipped and logged, guardians are auto-linked, and the same timers run.

## Scoring
- Fast rules pass (<100 ms) gives a rules score. If an LLM is available: `final = round(0.4*rules + 0.6*llm)`, otherwise `final = rules`.
- The final score is **never below the rules' hard floors**, so the alert never depends on the LLM.
- Credential requests are scored per sensitive item asked for (see `credential_items` in `backend/app/data/scam_patterns.json`).

## Privacy
Audio is never sent to or stored by the backend. Raw text and transcripts are kept only if `save_evidence=true`, and are purged after `DATA_TTL_HOURS`.
