"use client";
import { useLang } from "@/lib/lang";
import type { AlertItem } from "@/lib/types";
import { Card, VerdictBadge } from "./ui";

export function AlertFeed({ alerts, onAck }: { alerts: AlertItem[]; onAck: (id: string) => void }) {
  const { t, lang } = useLang();
  if (!alerts.length) return <p className="py-6 text-center text-lg">{t("noAlerts")}</p>;
  return (
    <ul className="space-y-3">
      {alerts.map((a) => (
        <li key={a.id}>
          <Card className="space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <VerdictBadge verdict={a.verdict} />
              <span className="text-base text-ink/70">{new Date(a.created_at).toLocaleString()}</span>
            </div>
            <p className="text-lg">{a.summary[lang]}</p>
            <p className="text-base text-ink/70">{a.scam_type.replace(/_/g, " ")} · {t("risk")} {a.risk_score}</p>
            {a.escalated && <p className="font-semibold text-warn">⚠ {t("escalated")}</p>}
            {a.acked ? <p className="font-semibold text-safe">✓ {t("acked")}</p> : (
              <button type="button" onClick={() => onAck(a.id)} className="min-h-[52px] w-full rounded-xl bg-brand text-lg font-semibold text-white">{t("ack")}</button>
            )}
          </Card>
        </li>
      ))}
    </ul>
  );
}
