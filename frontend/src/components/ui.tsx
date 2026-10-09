"use client";
import Link from "next/link";
import { AlertTriangle, ShieldAlert, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";
import { useLang } from "@/lib/lang";
import type { Signal, UiLang, Verdict } from "@/lib/types";

export function BigButton({ children, onClick, href, variant = "primary", disabled, type = "button" }: {
  children: ReactNode; onClick?: () => void; href?: string; disabled?: boolean;
  variant?: "primary" | "secondary" | "danger"; type?: "button" | "submit";
}) {
  const cls = `inline-flex min-h-[52px] w-full items-center justify-center gap-2 rounded-xl px-5 py-3 text-lg font-semibold focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/40 disabled:opacity-50 ${
    variant === "primary" ? "bg-brand text-white" : variant === "danger" ? "bg-danger text-white" : "border-2 border-brand bg-white text-brand"
  }`;
  if (href) return <Link href={href} className={cls}>{children}</Link>;
  return <button type={type} onClick={onClick} disabled={disabled} className={cls}>{children}</button>;
}

export const verdictColor = (v: Verdict) => (v === "SCAM" ? "#B3171C" : v === "SUSPICIOUS" ? "#8A5300" : "#14632E");
export const scoreVerdict = (s: number): Verdict => (s >= 70 ? "SCAM" : s >= 35 ? "SUSPICIOUS" : "SAFE");

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const { t } = useLang();
  const Icon = verdict === "SCAM" ? ShieldAlert : verdict === "SUSPICIOUS" ? AlertTriangle : ShieldCheck;
  const label = verdict === "SCAM" ? t("scam") : verdict === "SUSPICIOUS" ? t("suspicious") : t("safe");
  const bg = verdict === "SCAM" ? "bg-red-100 text-danger" : verdict === "SUSPICIOUS" ? "bg-amber-100 text-warn" : "bg-green-100 text-safe";
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-lg font-bold ${bg}`}>
      <Icon aria-hidden size={22} /> {label}
    </span>
  );
}

export function RiskMeter({ score }: { score: number }) {
  const { t } = useLang();
  const v = scoreVerdict(score);
  const color = verdictColor(v);
  const arc = "M 15 100 A 85 85 0 0 1 185 100";
  return (
    <div role="img" aria-label={`${t("risk")} ${score} / 100`} className="mx-auto w-full max-w-xs">
      <svg viewBox="0 0 200 115" className="w-full">
        <path d={arc} pathLength={100} fill="none" stroke="#DCE5E8" strokeWidth={16} strokeLinecap="round" />
        <path d={arc} pathLength={100} fill="none" stroke={color} strokeWidth={16} strokeLinecap="round"
          strokeDasharray={`${Math.max(score, 0.5)} 100`} style={{ transition: "stroke-dasharray .6s ease, stroke .3s" }} />
        <text x="100" y="92" textAnchor="middle" fontSize="40" fontWeight="700" fill={color}>{score}</text>
        <text x="100" y="110" textAnchor="middle" fontSize="12" fill="#10262E">{t("risk")} / 100</text>
      </svg>
    </div>
  );
}

export function SignalChips({ signals }: { signals: Signal[] }) {
  if (!signals.length) return null;
  const types = Array.from(new Set(signals.map((s) => s.type)));
  return (
    <ul className="flex flex-wrap gap-2">
      {types.map((s) => (
        <li key={s} className="rounded-full border border-danger/40 bg-red-50 px-3 py-1 text-base text-danger">
          {s.replace(/_/g, " ")}
        </li>
      ))}
    </ul>
  );
}

const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
export function HighlightedText({ text, evidence }: { text: string; evidence: string[] }) {
  const ev = evidence.filter((e) => e.trim().length > 1);
  if (!ev.length) return <>{text}</>;
  const rx = new RegExp(`(${ev.map(esc).join("|")})`, "gi");
  const lower = ev.map((e) => e.toLowerCase());
  return (
    <>
      {text.split(rx).map((p, i) =>
        lower.includes(p.toLowerCase()) ? <mark key={i} className="rounded bg-red-200 px-1 text-ink">{p}</mark> : <span key={i}>{p}</span>,
      )}
    </>
  );
}

export function LanguageToggle() {
  const { lang, setLang } = useLang();
  const opts: { v: UiLang; label: string }[] = [{ v: "en", label: "English" }, { v: "hi", label: "हिन्दी" }];
  return (
    <div role="group" aria-label="Language" className="flex overflow-hidden rounded-full border-2 border-brand">
      {opts.map((o) => (
        <button key={o.v} type="button" aria-pressed={lang === o.v} onClick={() => setLang(o.v)}
          className={`min-h-[44px] px-4 text-base font-semibold ${lang === o.v ? "bg-brand text-white" : "bg-white text-brand"}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-line bg-white p-5 ${className}`}>{children}</section>;
}
export function Spinner({ label }: { label: string }) {
  return <p role="status" className="py-6 text-center text-lg text-ink/70">{label}</p>;
}
export function ErrorBox({ message }: { message: string }) {
  return <p role="alert" className="rounded-xl border border-danger bg-red-50 p-4 text-lg text-danger">{message}</p>;
}
