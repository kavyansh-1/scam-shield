"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, errMsg } from "@/lib/api";
import { useLang } from "@/lib/lang";
import type { Bilingual, Scenario } from "@/lib/types";
import { ChatBubble } from "@/components/ChatBubble";
import { CoachTip } from "@/components/CoachTip";
import { BigButton, Card, ErrorBox } from "@/components/ui";

type Msg = { from: "scammer" | "user"; text: string; coach?: Bilingual | null; safe?: boolean };

export default function Practice() {
  const { t, lang } = useLang();
  const [sid, setSid] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [err, setErr] = useState("");
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [msgs, typing]);

  const begin = async (s: Scenario) => {
    setErr(""); setScore(null); setMsgs([]); setTyping(true);
    try { const r = await api.simStart(s, lang); setSid(r.session_id); setMsgs([{ from: "scammer", text: r.scammer_message }]); }
    catch (e) { setErr(errMsg(e)); } finally { setTyping(false); }
  };
  const send = async (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim(); if (!text || typing) return;
    setInput(""); setMsgs((p) => [...p, { from: "user", text }]); setTyping(true);
    try {
      const r = await api.simTurn(sid, text);
      setMsgs((p) => {
        const last = p.length - 1;
        const upd = p.map((m, i) => (i === last ? { ...m, coach: r.coach, safe: r.safe_so_far } : m));
        return r.done ? upd : [...upd, { from: "scammer", text: r.scammer_message }];
      });
      if (r.done) setScore(r.final_score ?? (r.safe_so_far ? 90 : 40));
    } catch (x) { setErr(errMsg(x)); } finally { setTyping(false); }
  };
  const scenarios: Scenario[] = ["digital_arrest", "fake_kyc", "upi_refund"];

  return (
    <>
      <p role="note" className="rounded-xl bg-amber-100 p-3 text-center text-lg font-bold text-warn">{t("practiceBanner")}</p>
      {err && <ErrorBox message={err} />}
      {!sid ? (
        <Card className="space-y-3">
          <h1 className="text-2xl font-bold">{t("pickScenario")}</h1>
          {scenarios.map((s) => <BigButton key={s} variant="secondary" onClick={() => begin(s)}>{t(s)}</BigButton>)}
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            {msgs.map((m, i) => (
              <div key={i} className="space-y-2">
                <ChatBubble from={m.from} text={m.text} />
                {m.coach && <CoachTip tip={m.coach} safe={m.safe ?? true} />}
              </div>
            ))}
            {typing && <ChatBubble from="scammer" typing />}
            <div ref={end} />
          </div>
          {score !== null ? (
            <Card className="space-y-3 text-center">
              <p className="text-lg">{t("finalScore")}</p>
              <p className="text-5xl font-extrabold">{score}/100</p>
              <BigButton onClick={() => { setSid(""); setMsgs([]); setScore(null); }}>{t("tryAgain")}</BigButton>
            </Card>
          ) : (
            <form onSubmit={send} className="flex gap-2">
              <input value={input} onChange={(e) => setInput(e.target.value)} aria-label={t("yourReply")} placeholder={t("yourReply")} className="min-h-[52px] flex-1 rounded-xl border-2 border-line p-3 text-lg" />
              <button type="submit" disabled={typing} className="min-h-[52px] rounded-xl bg-brand px-5 text-lg font-semibold text-white disabled:opacity-50">{t("send")}</button>
            </form>
          )}
        </>
      )}
    </>
  );
}
