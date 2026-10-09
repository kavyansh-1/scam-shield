"use client";
import { useEffect, useRef } from "react";
import { ShieldAlert } from "lucide-react";
import { useLang } from "@/lib/lang";

export function WarningOverlay({ onClose }: { onClose: () => void }) {
  const { t } = useLang();
  const btn = useRef<HTMLButtonElement>(null);
  useEffect(() => { btn.current?.focus(); }, []);
  return (
    <div role="alertdialog" aria-modal="true" aria-live="assertive" aria-label={t("scamTitle")}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-6 bg-danger p-6 text-center text-white">
      <ShieldAlert aria-hidden size={96} />
      <h2 className="text-4xl font-extrabold leading-tight">{t("scamTitle")}</h2>
      <p className="text-2xl">{t("familyAlerted")}</p>
      <button ref={btn} type="button" onClick={onClose}
        className="min-h-[56px] rounded-xl bg-white px-8 text-xl font-bold text-danger focus:outline-none focus-visible:ring-4 focus-visible:ring-white/60">
        {t("close")}
      </button>
    </div>
  );
}
