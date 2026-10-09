export type Verdict = "SAFE" | "SUSPICIOUS" | "SCAM";
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
export interface Signal { type: SignalType; evidence: string; weight: number }
export interface Entities { phones: string[]; upi_ids: string[]; urls: string[]; apps: string[]; amounts: string[] }
export interface BlocklistHit { value: string; kind: "phone" | "upi" | "url"; reports: number }

export interface AnalysisResult {
  id: string;
  source: "text" | "image" | "live";
  risk_score: number;
  verdict: Verdict;
  scam_type: ScamType;
  language: Language;
  signals: Signal[];
  explanation: Bilingual;
  actions: Bilingual[];
  entities: Entities;
  blocklist_hits: BlocklistHit[];
  extracted_text?: string;
  created_at: string;
}

export interface ApiError { error: string; code: string }
export interface Health { status: "ok"; llm: string; telegram: "live" | "mock" }

export interface GuardianLinkReq {
  user_id?: string; user_name: string; user_phone?: string; guardian_name: string;
  relationship: string; secondary?: { name: string; relationship: string };
}
export interface GuardianLinkRes {
  user_id: string; guardian_id: string; link_code: string; telegram_deep_link: string; secondary_link_code?: string;
}
export interface GuardianInfo { id: string; name: string; relationship: string; linked: boolean; role: "primary" | "secondary" }
export interface AlertItem {
  id: string; created_at: string; verdict: Verdict; scam_type: ScamType; risk_score: number;
  summary: Bilingual; acked: boolean; escalated: boolean;
}
export interface Stats {
  scams_caught: number; suspicious_flagged: number; est_money_saved_inr: number; is_estimate: true;
  by_type: { scam_type: string; count: number }[];
  by_day: { date: string; count: number }[];
  by_language: { language: string; count: number }[];
}
export interface DemoTurn { delay_ms: number; speaker: "scammer" | "victim"; text: string }
export type DemoVariant = "hinglish" | "english" | "benign";
export type Scenario = "digital_arrest" | "fake_kyc" | "upi_refund";
export interface SimTurnRes {
  scammer_message: string; coach: Bilingual | null; safe_so_far: boolean; done: boolean; final_score?: number;
}

export type ClientMsg =
  | { type: "transcript"; text: string; is_final: boolean }
  | { type: "end"; save_evidence: boolean };
export type ServerMsg =
  | { type: "risk_update"; risk_score: number; verdict: Verdict; new_signals: Signal[] }
  | { type: "scam_alert"; result: AnalysisResult; alert_id: string }
  | { type: "session_summary"; result: AnalysisResult; analysis_id: string };
