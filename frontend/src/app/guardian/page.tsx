"use client";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, errMsg } from "@/lib/api";
import { useLang } from "@/lib/lang";
import type { AlertItem, GuardianLinkRes } from "@/lib/types";
import { useUser } from "@/hooks/useUser";
import { AlertFeed } from "@/components/AlertFeed";
import { GuardianLinkCard } from "@/components/GuardianLinkCard";
import { BigButton, Card, ErrorBox } from "@/components/ui";

const inp = "w-full min-h-[48px] rounded-xl border-2 border-line p-3 text-lg";

export default function Guardian() {
  const { t } = useLang();
  const { userId } = useUser();
  const [tab, setTab] = useState<"setup" | "view">("setup");
  const [f, setF] = useState({ user_name: "", user_phone: "", guardian_name: "", relationship: "", s_name: "", s_rel: "" });
  const [link, setLink] = useState<GuardianLinkRes | null>(null);
  const [linked, setLinked] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setErr("");
    try {
      setLink(await api.linkGuardian({
        user_id: userId, user_name: f.user_name, user_phone: f.user_phone || undefined,
        guardian_name: f.guardian_name, relationship: f.relationship,
        secondary: f.s_name ? { name: f.s_name, relationship: f.s_rel || "Other" } : undefined,
      }));
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  };

  useEffect(() => {
    if (!userId || linked || !link) return;
    const i = setInterval(() => {
      api.getGuardians(userId).then((g) => setLinked(g.guardians.some((x) => x.role === "primary" && x.linked))).catch(() => {});
    }, 3000);
    return () => clearInterval(i);
  }, [userId, link, linked]);

  const loadAlerts = useCallback(() => { if (userId) api.getAlerts(userId).then((a) => setAlerts(a.alerts)).catch((x) => setErr(errMsg(x))); }, [userId]);
  useEffect(() => {
    if (tab !== "view") return;
    loadAlerts(); const i = setInterval(loadAlerts, 3000); return () => clearInterval(i);
  }, [tab, loadAlerts]);
  const ack = async (id: string) => { try { await api.ackAlert(id); loadAlerts(); } catch (x) { setErr(errMsg(x)); } };

  return (
    <>
      <div role="tablist" className="grid grid-cols-2 gap-2">
        {(["setup", "view"] as const).map((k) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
            className={`min-h-[52px] rounded-xl text-lg font-semibold ${tab === k ? "bg-brand text-white" : "border-2 border-brand bg-white text-brand"}`}>
            {k === "setup" ? t("setupFamily") : t("guardianView")}
          </button>
        ))}
      </div>
      {err && <ErrorBox message={err} />}
      {tab === "setup" ? (
        link ? <GuardianLinkCard code={link.link_code} link={link.telegram_deep_link} linked={linked} /> : (
          <Card>
            <form onSubmit={submit} className="space-y-3">
              <label className="block text-lg">{t("yourName")}<input required className={inp} value={f.user_name} onChange={set("user_name")} /></label>
              <label className="block text-lg">{t("phoneOpt")}<input inputMode="tel" className={inp} value={f.user_phone} onChange={set("user_phone")} /></label>
              <label className="block text-lg">{t("guardianName")}<input required className={inp} value={f.guardian_name} onChange={set("guardian_name")} /></label>
              <label className="block text-lg">{t("relationship")}<input required className={inp} value={f.relationship} onChange={set("relationship")} /></label>
              <fieldset className="space-y-3 rounded-xl border border-line p-3">
                <legend className="px-1 text-lg">{t("secondaryOpt")}</legend>
                <input aria-label={t("guardianName")} placeholder={t("guardianName")} className={inp} value={f.s_name} onChange={set("s_name")} />
                <input aria-label={t("relationship")} placeholder={t("relationship")} className={inp} value={f.s_rel} onChange={set("s_rel")} />
              </fieldset>
              <BigButton type="submit" disabled={busy || !userId}>{t("createLink")}</BigButton>
            </form>
          </Card>
        )
      ) : <AlertFeed alerts={alerts} onAck={ack} />}
    </>
  );
}
