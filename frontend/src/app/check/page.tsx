"use client";
import { useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useLang } from "@/lib/lang";
import type { AnalysisResult } from "@/lib/types";
import { ResultCard } from "@/components/ResultCard";
import { ScreenshotDropzone } from "@/components/ScreenshotDropzone";
import { BigButton, ErrorBox, Spinner } from "@/components/ui";

export default function Check() {
  const { t } = useLang();
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [save, setSave] = useState(false);
  const [res, setRes] = useState<AnalysisResult | null>(null);
  const [src, setSrc] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const paste = async () => {
    try { setText(await navigator.clipboard.readText()); } catch { /* clipboard blocked */ }
  };
  const run = async () => {
    setBusy(true); setErr(""); setRes(null);
    try {
      const r = file ? await api.analyzeImage(file, save) : await api.analyzeText(text.slice(0, 8000), save);
      setSrc(file ? "" : text); setRes(r);
    } catch (e) { setErr(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <>
      <h1 className="text-3xl font-extrabold">{t("check")}</h1>
      <label htmlFor="msg" className="sr-only">{t("pasteHere")}</label>
      <textarea id="msg" value={text} onChange={(e) => setText(e.target.value)} rows={6} maxLength={8000}
        placeholder={t("pasteHere")} className="w-full rounded-xl border-2 border-line p-4 text-lg" />
      <BigButton variant="secondary" onClick={paste}>📋 {t("paste")}</BigButton>
      <ScreenshotDropzone file={file} onFile={setFile} />
      <label className="flex min-h-[48px] items-center gap-3 text-lg">
        <input type="checkbox" checked={save} onChange={(e) => setSave(e.target.checked)} className="h-6 w-6" /> {t("includeMsg")}
      </label>
      <BigButton onClick={run} disabled={busy || (!file && text.trim().length < 3)}>{busy ? t("analyzing") : t("analyze")}</BigButton>
      {busy && <Spinner label={t("analyzing")} />}
      {err && <ErrorBox message={err} />}
      {res && <ResultCard r={res} sourceText={src} />}
    </>
  );
}
