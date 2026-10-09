"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useLang } from "@/lib/lang";
import type { AnalysisResult } from "@/lib/types";
import { useTTS } from "@/hooks/useTTS";
import { useUser } from "@/hooks/useUser";
import { BigButton, Card, ErrorBox, HighlightedText, RiskMeter, SignalChips, VerdictBadge } from "./ui";

export function ResultCard({ r, sourceText }: { r: AnalysisResult; sourceText: string }) {
  const { t, lang } = useLang();
  const { userId } = useUser();
  const { speak } = useTTS(lang);
  const router = useRouter();
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const run = async (fn: () => Promise<void>, ok: string) => {
    setBusy(true); setErr(""); setNote("");
    try { await fn(); setNote(ok); } catch (e) { setErr(errMsg(e)); } finally { setBusy(false); }
  };
  const target = r.entities.phones[0] ? { v: r.entities.phones[0], k: "phone" as const }
    : r.entities.upi_ids[0] ? { v: r.entities.upi_ids[0], k: "upi" as const }
    : r.entities.urls[0] ? { v: r.entities.urls[0], k: "url" as const } : null;
  const text = sourceText || r.extracted_text || "";

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <VerdictBadge verdict={r.verdict} />
        <span className="text-lg capitalize text-ink/70">{r.scam_type.replace(/_/g, " ")}</span>
      </div>
      <RiskMeter score={r.risk_score} />
      {r.signals.length > 0 && (<div><h3 className="mb-2 text-lg font-bold">{t("signals")}</h3><SignalChips signals={r.signals} /></div>)}
      {text && <p className="whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-lg"><HighlightedText text={text} evidence={r.signals.map((s) => s.evidence)} /></p>}
      <p className="text-xl">{r.explanation[lang]}</p>
      <div>
        <h3 className="mb-1 text-lg font-bold">{t("whatToDo")}</h3>
        <ul className="list-disc space-y-1 pl-6 text-lg">{r.actions.map((a, i) => <li key={i}>{a[lang]}</li>)}</ul>
      </div>
      {r.blocklist_hits.length > 0 && (
        <div className="rounded-xl bg-red-50 p-3 text-lg">
          <strong>{t("blocklistHits")}:</strong> {r.blocklist_hits.map((h) => `${h.value} (${h.reports})`).join(", ")}
        </div>
      )}
      <div className="grid gap-2 sm:grid-cols-2">
        <BigButton variant="secondary" onClick={() => speak(`${r.explanation[lang]} ${r.actions.map((a) => a[lang]).join(". ")}`)}>🔊 {t("speak")}</BigButton>
        <BigButton variant="secondary" disabled={busy || !userId} onClick={() => run(async () => { await api.sendAlert(userId, r.id); }, t("sent"))}>{t("alertFamily")}</BigButton>
        {target && <BigButton variant="secondary" disabled={busy} onClick={() => run(async () => { await api.reportEntity(target.v, target.k); }, t("reported"))}>{t("reportNumber")}</BigButton>}
        <BigButton disabled={busy} onClick={() => run(async () => { const g = await api.generateReport(r.id); router.push(`/report/${g.report_id}`); }, "")}>{t("downloadPdf")}</BigButton>
      </div>
      {note && <p role="status" className="text-lg font-semibold text-safe">✓ {note}</p>}
      {err && <ErrorBox message={err} />}
    </Card>
  );
}
