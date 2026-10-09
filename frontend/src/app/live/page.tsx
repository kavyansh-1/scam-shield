"use client";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api, errMsg, sleep } from "@/lib/api";
import { useLang } from "@/lib/lang";
import type { AnalysisResult, DemoVariant, ServerMsg, Signal, Verdict } from "@/lib/types";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { useTTS } from "@/hooks/useTTS";
import { useUser } from "@/hooks/useUser";
import { ConsentModal } from "@/components/ConsentModal";
import { LiveTranscript, type Line } from "@/components/LiveTranscript";
import { WarningOverlay } from "@/components/WarningOverlay";
import { BigButton, Card, ErrorBox, RiskMeter, SignalChips, VerdictBadge } from "@/components/ui";

function LiveInner() {
  const { t, lang } = useLang();
  const { userId } = useUser();
  const { speak, cancel } = useTTS(lang);
  const router = useRouter();
  const params = useSearchParams();
  const [consent, setConsent] = useState(false);
  const [running, setRunning] = useState(false);
  const [lines, setLines] = useState<Line[]>([]);
  const [interim, setInterim] = useState("");
  const [risk, setRisk] = useState(0);
  const [verdict, setVerdict] = useState<Verdict>("SAFE");
  const [signals, setSignals] = useState<Signal[]>([]);
  const [alertOn, setAlertOn] = useState(false);
  const [summary, setSummary] = useState<AnalysisResult | null>(null);
  const [paste, setPaste] = useState("");
  const [err, setErr] = useState("");
  const lineId = useRef(0);
  const cancelled = useRef(false);
  const autoRan = useRef(false);

  const langRef = useRef(lang);
  langRef.current = lang;
  const speakRef = useRef(speak);
  speakRef.current = speak;

  const onMsg = useCallback((m: ServerMsg) => {
    if (m.type === "risk_update") {
      setRisk(m.risk_score); setVerdict(m.verdict);
      if (m.new_signals.length) setSignals((p) => [...p, ...m.new_signals]);
    } else if (m.type === "scam_alert") {
      setAlertOn(true);
      speakRef.current(langRef.current === "hi" ? "यह ठगी है। कॉल काट दें। आपके परिवार को बता दिया गया है।" : "This is a scam. Cut the call. Your family has been alerted.");
      if ("vibrate" in navigator) navigator.vibrate([400, 150, 400, 150, 400]);
    } else {
      setSummary(m.result);
    }
  }, []);
  const sock = useLiveSocket(onMsg);

  const addLine = (who: Line["who"], text: string) => setLines((p) => [...p, { id: lineId.current++, who, text }]);
  const reset = () => { setLines([]); setInterim(""); setRisk(0); setVerdict("SAFE"); setSignals([]); setAlertOn(false); setSummary(null); setErr(""); };

  const rec = useSpeechRecognition(lang, (text, isFinal) => {
    if (!text) return;
    if (isFinal) { setInterim(""); addLine("mic", text); sock.send({ type: "transcript", text, is_final: true }); }
    else { setInterim(text); sock.send({ type: "transcript", text, is_final: false }); }
  });

  const startMic = () => { reset(); sock.open(userId); rec.start(); setRunning(true); };
  const stop = () => {
    cancelled.current = true; rec.stop(); setRunning(false); setInterim("");
    sock.send({ type: "end", save_evidence: false });
  };
  const replay = useCallback(async (variant: DemoVariant) => {
    if (!userId) return;
    cancelled.current = false; reset(); sock.open(userId); setRunning(true);
    try {
      const call = await api.demoCall(variant);
      for (const turn of call.turns) {
        await sleep(turn.delay_ms);
        if (cancelled.current) return;
        addLine(turn.speaker, turn.text);
        sock.send({ type: "transcript", text: turn.text, is_final: true });
      }
      sock.send({ type: "end", save_evidence: false });
    } catch (e) { setErr(errMsg(e)); }
    finally { setRunning(false); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, sock]);
  const sendPasted = () => {
    if (!paste.trim()) return;
    if (!running) { reset(); sock.open(userId); setRunning(true); }
    addLine("mic", paste); sock.send({ type: "transcript", text: paste, is_final: true }); setPaste("");
  };

  // auto-start the demo when arriving via /live?demo=hinglish
  const demo = params.get("demo");
  useEffect(() => {
    if (demo && userId && !autoRan.current) { autoRan.current = true; setConsent(true); replay(demo as DemoVariant); }
  }, [demo, userId, replay]);
  useEffect(() => () => { cancelled.current = true; cancel(); }, [cancel]);

  const generate = async () => {
    if (!summary) return;
    try { const g = await api.generateReport(summary.id); router.push(`/report/${g.report_id}`); } catch (e) { setErr(errMsg(e)); }
  };

  return (
    <>
      {!consent && <ConsentModal onAccept={() => setConsent(true)} />}
      {alertOn && <WarningOverlay onClose={() => { setAlertOn(false); cancel(); }} />}
      <h1 className="text-3xl font-extrabold">{t("listen")}</h1>
      <Card className="space-y-3">
        <RiskMeter score={risk} />
        <div className="flex justify-center"><VerdictBadge verdict={verdict} /></div>
        <SignalChips signals={signals} />
      </Card>
      {!running ? (
        <div className="grid gap-2">
          <BigButton onClick={startMic} disabled={!consent || !userId || !rec.supported}>🎙 {t("start")}</BigButton>
        </div>
      ) : <BigButton variant="danger" onClick={stop}>■ {t("stop")}</BigButton>}
      {!rec.supported && (
        <Card className="space-y-2">
          <p className="text-lg">{t("pasteTranscript")}</p>
          <textarea value={paste} onChange={(e) => setPaste(e.target.value)} rows={3} aria-label={t("pasteTranscript")} className="w-full rounded-xl border-2 border-line p-3 text-lg" />
          <BigButton variant="secondary" onClick={sendPasted} disabled={!consent}>{t("send")}</BigButton>
        </Card>
      )}
      <Card className="space-y-2">
        <h2 className="text-lg font-bold">{t("replay")}</h2>
        <div className="grid gap-2 sm:grid-cols-3">
          {(["hinglish", "english", "benign"] as const).map((v) => (
            <BigButton key={v} variant="secondary" disabled={running || !consent} onClick={() => replay(v)}>{t(v)}</BigButton>
          ))}
        </div>
      </Card>
      <LiveTranscript lines={lines} interim={interim} evidence={signals.map((s) => s.evidence)} />
      {err && <ErrorBox message={err} />}
      {summary && (
        <Card className="space-y-3">
          <h2 className="text-xl font-bold">{t("summary")}</h2>
          <VerdictBadge verdict={summary.verdict} />
          <p className="text-lg">{summary.explanation[lang]}</p>
          <BigButton onClick={generate}>{t("downloadPdf")}</BigButton>
        </Card>
      )}
    </>
  );
}

export default function Live() {
  return <Suspense fallback={null}><LiveInner /></Suspense>;
}
