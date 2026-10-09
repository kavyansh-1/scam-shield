"use client";
import { useLang } from "@/lib/lang";
import type { Stats } from "@/lib/types";
import { Card } from "./ui";

export function ImpactStats({ stats }: { stats: Stats }) {
  const { t } = useLang();
  const items = [
    { label: t("scamsCaught"), value: String(stats.scams_caught) },
    { label: t("suspiciousFlagged"), value: String(stats.suspicious_flagged) },
    { label: t("moneySaved"), value: `₹${stats.est_money_saved_inr.toLocaleString("en-IN")}`, est: true },
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {items.map((i) => (
        <Card key={i.label}>
          <p className="text-base text-ink/70">{i.label}</p>
          <p className="text-4xl font-bold">{i.value}</p>
          {i.est && <p title={t("estimateTip")} className="mt-1 inline-block rounded bg-amber-100 px-2 text-base text-warn">{t("estimate")} · {t("estimateTip")}</p>}
        </Card>
      ))}
    </div>
  );
}
