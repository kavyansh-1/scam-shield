# Scam Shield - Contract

Single source of truth for backend and frontend.

```
ENUMS
Verdict: SAFE | SUSPICIOUS | SCAM
Thresholds: score < 35 SAFE; 35-69 SUSPICIOUS; >= 70 SCAM
Language: en | hi | hinglish      (detected language of the analysed content)
UiLang: en | hi
ScamType: digital_arrest | fake_kyc | upi_collect | remote_access | courier_parcel
          | lottery_prize | investment | other | none
SignalType: authority_impersonation | urgency_threat | isolation | remote_access
            | payment_demand | credential_request | suspicious_link_or_apk
            | upi_collect_trick | known_bad_entity

Bilingual = { "en": string, "hi": string }

AnalysisResult {
  id: uuid,
  source: "text"|"image"|"live",
  risk_score: int 0-100,
  verdict: Verdict,
  scam_type: ScamType,
  language: Language,
  signals: [{ type: SignalType, evidence: string (verbatim quote), weight: int 1-30 }],
  explanation: Bilingual (max 2 short sentences each, simple words),
  actions: [Bilingual] (2-4 imperative steps),
  entities: { phones: string[], upi_ids: string[], urls: string[],
              apps: string[], amounts: string[] },
  blocklist_hits: [{ value: string, kind: "phone"|"upi"|"url", reports: int }],
  extracted_text?: string (image only),
  created_at: ISO-8601
}

ERRORS: { "error": string, "code": string }

ENDPOINTS
GET  /api/health
  -> { status:"ok", llm: provider, telegram:"live"|"mock" }

POST /api/analyze/text
  { text: string (<=8000), save_evidence?: boolean } -> AnalysisResult

POST /api/analyze/image
  multipart: file (png|jpg|webp, <=6MB), save_evidence? -> AnalysisResult

WS   /ws/live?session_id=<uuid>&user_id=<uuid>
  client->server: { type:"transcript", text:string, is_final:boolean }
                  { type:"end", save_evidence:boolean }
  server->client: { type:"risk_update", risk_score:int, verdict:Verdict,
                    new_signals: Signal[] }
                  { type:"scam_alert", result:AnalysisResult, alert_id:uuid }
                     (sent ONCE per session, when score first >= 70)
                  { type:"session_summary", result:AnalysisResult, analysis_id:uuid }

POST /api/guardian/link
  { user_id?, user_name, user_phone?, guardian_name, relationship,
    secondary?: { name, relationship } }
  -> { user_id, guardian_id, link_code (6 chars), telegram_deep_link,
       secondary_link_code? }

GET  /api/guardian/{user_id}
  -> { guardians:[{ id, name, relationship, linked:boolean,
                    role:"primary"|"secondary" }] }

POST /api/alerts/send
  { user_id, analysis_id } -> { alert_id }

GET  /api/alerts/{user_id}
  -> { alerts:[{ id, created_at, verdict, scam_type, risk_score,
                 summary: Bilingual, acked:boolean, escalated:boolean }] }

POST /api/alerts/{alert_id}/ack -> { acked:true }

POST /api/blocklist/report
  { value, kind } -> { value, kind, reports }

POST /api/report/generate
  { analysis_id } -> { report_id, pdf_url }

GET  /api/report/{report_id}.pdf -> application/pdf

GET  /api/stats
  -> { scams_caught:int, suspicious_flagged:int, est_money_saved_inr:int,
       is_estimate:true, by_type:[{scam_type,count}],
       by_day:[{date,count}], by_language:[{language,count}] }

POST /api/simulator/start
  { scenario:"digital_arrest"|"fake_kyc"|"upi_refund", ui_lang }
  -> { session_id, scammer_message: string }

POST /api/simulator/turn
  { session_id, user_message }
  -> { scammer_message, coach: Bilingual|null, safe_so_far:boolean,
       done:boolean, final_score?: int 0-100 }

GET  /api/demo/call?variant=hinglish|english|benign
  -> { turns:[{ delay_ms:int, speaker:"scammer"|"victim", text:string }] }

ALERT FLOW
scam_alert -> create Alert -> Telegram message to the primary guardian
(user name, phone if given, scam type, top 3 evidence quotes, risk score)
with inline button "I am calling them". No ack within ACK_TIMEOUT_S ->
send to the secondary guardian and set escalated=true.
Mock mode (no bot token): skip Telegram, still create Alert rows and run
the same timers.

PRIVACY
Audio is never sent to or stored by the backend. Raw text and transcripts
are kept only if save_evidence=true, and are purged after DATA_TTL_HOURS.
```
