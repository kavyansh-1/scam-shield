// Mirrors docs/CONTRACT.md exactly. Keep in sync.

// ---- Enums ----
export type Verdict = "SAFE" | "SUSPICIOUS" | "SCAM";
// Thresholds: score < 35 SAFE; 35-69 SUSPICIOUS; >= 70 SCAM
export type Language = "en" | "hi" | "hinglish";
export type UiLang = "en" | "hi";
export type ScamType =
  | "digital_arrest" | "fake_kyc" | "upi_collect" | "remote_access" | "courier_parcel"
  | "lottery_prize" | "investment" | "other" | "none";
export type SignalType =
  | "authority_impersonation" | "urgency_threat" | "isolation" | "remote_access"
  | "payment_demand" | "credential_request" | "suspicious_link_or_apk"
  | "upi_collect_trick" | "known_bad_entity";

export interface Bilingual { en: string; hi: string }

// ---- Core models ----
export interface Signal {
  type: SignalType;
  evidence: string; // verbatim quote
  weight: number; // int 1-30
}

export interface Entities {
  phones: string[];
  upi_ids: string[];
  urls: string[];
  apps: string[];
  amounts: string[];
}

export type BlocklistKind = "phone" | "upi" | "url";
export interface BlocklistHit { value: string; kind: BlocklistKind; reports: number }

export interface AnalysisResult {
  id: string; // uuid
  source: "text" | "image" | "live";
  risk_score: number; // int 0-100
  verdict: Verdict;
  scam_type: ScamType;
  language: Language;
  signals: Signal[];
  explanation: Bilingual; // max 2 short sentences each
  actions: Bilingual[]; // 2-4 imperative steps
  entities: Entities;
  blocklist_hits: BlocklistHit[];
  extracted_text?: string; // image only
  created_at: string; // ISO-8601
}

export interface ApiError { error: string; code: string }

// ---- REST ----
export interface HealthResponse { status: "ok"; llm: string; telegram: "live" | "mock" }

export interface AnalyzeTextRequest { text: string; save_evidence?: boolean } // text <= 8000
// POST /api/analyze/image: multipart { file: png|jpg|webp <=6MB, save_evidence? } -> AnalysisResult

export interface GuardianContact { name: string; relationship: string }
export interface GuardianLinkRequest {
  user_id?: string;
  user_name: string;
  user_phone?: string;
  guardian_name: string;
  relationship: string;
  secondary?: GuardianContact;
}
export interface GuardianLinkResponse {
  user_id: string;
  guardian_id: string;
  link_code: string; // 6 chars
  telegram_deep_link: string;
  secondary_link_code?: string;
}
export interface Guardian {
  id: string;
  name: string;
  relationship: string;
  linked: boolean;
  role: "primary" | "secondary";
}
export interface GuardianListResponse { guardians: Guardian[] }

export interface AlertSendRequest { user_id: string; analysis_id: string }
export interface AlertSendResponse { alert_id: string }
export interface AlertItem {
  id: string;
  created_at: string;
  verdict: Verdict;
  scam_type: ScamType;
  risk_score: number;
  summary: Bilingual;
  acked: boolean;
  escalated: boolean;
}
export interface AlertListResponse { alerts: AlertItem[] }
export interface AlertAckResponse { acked: true }

export interface BlocklistReportRequest { value: string; kind: BlocklistKind }
export interface BlocklistReportResponse { value: string; kind: BlocklistKind; reports: number }

export interface ReportGenerateRequest { analysis_id: string }
export interface ReportGenerateResponse { report_id: string; pdf_url: string }

export interface StatsResponse {
  scams_caught: number;
  suspicious_flagged: number;
  est_money_saved_inr: number;
  is_estimate: true;
  by_type: { scam_type: ScamType; count: number }[];
  by_day: { date: string; count: number }[];
  by_language: { language: Language; count: number }[];
}

export type SimulatorScenario = "digital_arrest" | "fake_kyc" | "upi_refund";
export interface SimulatorStartRequest { scenario: SimulatorScenario; ui_lang: UiLang }
export interface SimulatorStartResponse { session_id: string; scammer_message: string }
export interface SimulatorTurnRequest { session_id: string; user_message: string }
export interface SimulatorTurnResponse {
  scammer_message: string;
  coach: Bilingual | null;
  safe_so_far: boolean;
  done: boolean;
  final_score?: number; // int 0-100
}

export type DemoVariant = "hinglish" | "english" | "benign";
export interface DemoTurn { delay_ms: number; speaker: "scammer" | "victim"; text: string }
export interface DemoCallResponse { turns: DemoTurn[] }

// ---- WebSocket /ws/live?session_id=<uuid>&user_id=<uuid> ----
export type LiveClientMessage =
  | { type: "transcript"; text: string; is_final: boolean }
  | { type: "end"; save_evidence: boolean };

export type LiveServerMessage =
  | { type: "risk_update"; risk_score: number; verdict: Verdict; new_signals: Signal[] }
  | { type: "scam_alert"; result: AnalysisResult; alert_id: string } // sent ONCE per session, first score >= 70
  | { type: "session_summary"; result: AnalysisResult; analysis_id: string };
