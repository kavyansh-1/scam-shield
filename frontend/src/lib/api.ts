import type {
  AlertItem, AnalysisResult, ApiError, DemoTurn, DemoVariant, GuardianInfo, GuardianLinkReq,
  GuardianLinkRes, Health, Scenario, SimTurnRes, Stats, ScamType, Signal,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
export const MOCK = process.env.NEXT_PUBLIC_MOCK === "1";

export const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));
export const uuid = (): string =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
      });
export const errMsg = (e: unknown): string => (e instanceof Error ? e.message : "Error");

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new Error("Cannot reach the server. Is the backend running?");
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { const b = (await res.json()) as Partial<ApiError>; if (b.error) msg = b.error; } catch { /* ignore */ }
    throw new Error(msg);
  }
  return (await res.json()) as T;
}
const post = <T,>(path: string, body: unknown) =>
  req<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

/* ---------- mock fixtures ---------- */
const SCAM_RX = /(cbi|arrest|giraftar|anydesk|teamviewer|safe account|rbi account|otp|upi pin|digital arrest|warrant|कॉल मत|गिरफ्तार|ओटीपी)/i;
export const mockSignals: Signal[] = [
  { type: "authority_impersonation", evidence: "CBI officer", weight: 25 },
  { type: "urgency_threat", evidence: "arrest", weight: 20 },
  { type: "isolation", evidence: "do not tell anyone", weight: 20 },
  { type: "remote_access", evidence: "AnyDesk", weight: 25 },
  { type: "payment_demand", evidence: "safe account", weight: 25 },
];
export function mockResult(text: string, source: AnalysisResult["source"] = "text"): AnalysisResult {
  const scam = SCAM_RX.test(text);
  const found = scam ? mockSignals.filter((s) => text.toLowerCase().includes(s.evidence.toLowerCase())) : [];
  const signals = scam ? (found.length >= 2 ? found : mockSignals.slice(0, 3)) : [];
  return {
    id: uuid(), source, risk_score: scam ? 92 : 8, verdict: scam ? "SCAM" : "SAFE",
    scam_type: scam ? ("digital_arrest" as ScamType) : "none", language: "en", signals,
    explanation: scam
      ? { en: "This looks like a digital-arrest scam. Real officers never ask for money on a call.", hi: "यह डिजिटल अरेस्ट ठगी लगती है। असली अधिकारी कॉल पर पैसे नहीं माँगते।" }
      : { en: "This looks like a normal notice. Still, never share your OTP.", hi: "यह सामान्य संदेश लगता है। फिर भी OTP किसी को न बताएँ।" },
    actions: scam
      ? [{ en: "Cut the call now.", hi: "कॉल अभी काट दें।" }, { en: "Do not send money.", hi: "पैसे न भेजें।" }, { en: "Call 1930.", hi: "1930 पर कॉल करें।" }]
      : [{ en: "No action needed.", hi: "कुछ करने की ज़रूरत नहीं।" }],
    entities: { phones: [], upi_ids: [], urls: [], apps: [], amounts: [] },
    blocklist_hits: [], extracted_text: source === "image" ? "Sample extracted text: CBI officer, you will be arrested. Install AnyDesk." : undefined,
    created_at: new Date().toISOString(),
  };
}
const mockCall: DemoTurn[] = [
  { delay_ms: 600, speaker: "scammer", text: "Hello, I am calling from the CBI cyber crime branch." },
  { delay_ms: 1500, speaker: "victim", text: "Haan ji, bataiye." },
  { delay_ms: 1500, speaker: "scammer", text: "A parcel in your name has illegal items. You will face arrest." },
  { delay_ms: 1500, speaker: "scammer", text: "Do not tell anyone. Stay on the video call." },
  { delay_ms: 1500, speaker: "scammer", text: "Download AnyDesk so I can verify your phone." },
  { delay_ms: 1500, speaker: "scammer", text: "Transfer the verification deposit to the RBI safe account." },
];
let mockPolls = 0;
const mockStats: Stats = {
  scams_caught: 14, suspicious_flagged: 6, est_money_saved_inr: 350000, is_estimate: true,
  by_type: [{ scam_type: "digital_arrest", count: 6 }, { scam_type: "fake_kyc", count: 4 }, { scam_type: "upi_collect", count: 3 }, { scam_type: "remote_access", count: 1 }],
  by_day: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d, i) => ({ date: d, count: [1, 2, 1, 3, 2, 4, 1][i] })),
  by_language: [{ language: "en", count: 5 }, { language: "hi", count: 4 }, { language: "hinglish", count: 5 }],
};
const mockSimMsgs = ["This is Inspector Rao from CBI. A parcel with drugs is in your name.", "You must stay on this call. Do not tell your family.", "Share your OTP now to clear your name."];
let simStep = 0;

/* ---------- API ---------- */
export const api = {
  health: async (): Promise<Health> =>
    MOCK ? { status: "ok", llm: "mock", telegram: "mock" } : req<Health>("/api/health"),

  analyzeText: async (text: string, save_evidence = false): Promise<AnalysisResult> => {
    if (MOCK) { await sleep(700); return mockResult(text); }
    return post<AnalysisResult>("/api/analyze/text", { text, save_evidence });
  },
  analyzeImage: async (file: File, save_evidence = false): Promise<AnalysisResult> => {
    if (MOCK) { await sleep(900); return mockResult("CBI arrest AnyDesk safe account", "image"); }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("save_evidence", String(save_evidence));
    return req<AnalysisResult>("/api/analyze/image", { method: "POST", body: fd });
  },

  linkGuardian: async (b: GuardianLinkReq): Promise<GuardianLinkRes> => {
    if (MOCK) { mockPolls = 0; return { user_id: b.user_id ?? uuid(), guardian_id: uuid(), link_code: "AB12CD", telegram_deep_link: "https://t.me/ScamShieldBot?start=AB12CD" }; }
    return post<GuardianLinkRes>("/api/guardian/link", b);
  },
  getGuardians: async (userId: string): Promise<{ guardians: GuardianInfo[] }> => {
    if (MOCK) { mockPolls += 1; return { guardians: [{ id: "g1", name: "Guardian", relationship: "Son", linked: mockPolls > 2, role: "primary" }] }; }
    return req(`/api/guardian/${userId}`);
  },
  sendAlert: (user_id: string, analysis_id: string) =>
    MOCK ? Promise.resolve({ alert_id: uuid() }) : post<{ alert_id: string }>("/api/alerts/send", { user_id, analysis_id }),
  getAlerts: async (userId: string): Promise<{ alerts: AlertItem[] }> => {
    if (MOCK) {
      return { alerts: [{ id: "a1", created_at: new Date().toISOString(), verdict: "SCAM", scam_type: "digital_arrest", risk_score: 92, summary: { en: "Fake CBI call: arrest threat, AnyDesk, safe account.", hi: "नकली CBI कॉल: गिरफ़्तारी की धमकी, AnyDesk, सेफ अकाउंट।" }, acked: false, escalated: false }] };
    }
    return req(`/api/alerts/${userId}`);
  },
  ackAlert: (id: string) => (MOCK ? Promise.resolve({ acked: true as const }) : post<{ acked: true }>(`/api/alerts/${id}/ack`, {})),
  reportEntity: (value: string, kind: "phone" | "upi" | "url") =>
    MOCK ? Promise.resolve({ value, kind, reports: 1 }) : post<{ value: string; kind: string; reports: number }>("/api/blocklist/report", { value, kind }),
  generateReport: (analysis_id: string) =>
    MOCK ? Promise.resolve({ report_id: analysis_id, pdf_url: "" }) : post<{ report_id: string; pdf_url: string }>("/api/report/generate", { analysis_id }),
  pdfUrl: (reportId: string, pdfUrl?: string) =>
    pdfUrl ? (pdfUrl.startsWith("http") ? pdfUrl : `${API_URL}${pdfUrl}`) : `${API_URL}/api/report/${reportId}.pdf`,

  stats: async (): Promise<Stats> => (MOCK ? mockStats : req<Stats>("/api/stats")),

  simStart: async (scenario: Scenario, ui_lang: string): Promise<{ session_id: string; scammer_message: string }> => {
    if (MOCK) { simStep = 0; return { session_id: uuid(), scammer_message: mockSimMsgs[0] }; }
    return post("/api/simulator/start", { scenario, ui_lang });
  },
  simTurn: async (session_id: string, user_message: string): Promise<SimTurnRes> => {
    if (MOCK) {
      await sleep(600);
      simStep += 1;
      const unsafe = /otp|\b\d{4,6}\b|anydesk/i.test(user_message);
      const done = simStep >= 3 || /bye|hang|cut|band/i.test(user_message);
      return {
        scammer_message: done ? "..." : mockSimMsgs[Math.min(simStep, 2)],
        coach: unsafe ? { en: "Risky: never share an OTP or install apps for a caller.", hi: "जोखिम: OTP न बताएँ और ऐप इंस्टॉल न करें।" } : { en: "Good. Ask for ID or hang up.", hi: "बढ़िया। पहचान माँगें या कॉल काट दें।" },
        safe_so_far: !unsafe, done, final_score: done ? (unsafe ? 40 : 90) : undefined,
      };
    }
    return post("/api/simulator/turn", { session_id, user_message });
  },
  demoCall: async (variant: DemoVariant): Promise<{ turns: DemoTurn[] }> => {
    if (MOCK) return { turns: variant === "benign" ? [{ delay_ms: 800, speaker: "scammer", text: "Hello, this is your bank customer care. Never share your OTP with anyone." }] : mockCall };
    return req(`/api/demo/call?variant=${variant}`);
  },
};
