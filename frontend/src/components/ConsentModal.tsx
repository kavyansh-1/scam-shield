"use client";
import { Mic } from "lucide-react";
import { useLang } from "@/lib/lang";
import { BigButton } from "./ui";

export function ConsentModal({ onAccept }: { onAccept: () => void }) {
  const { t } = useLang();
  return (
    <div role="dialog" aria-modal="true" aria-label={t("consentTitle")} className="fixed inset-0 z-40 flex items-center justify-center bg-ink/60 p-4">
      <div className="w-full max-w-md space-y-4 rounded-2xl bg-white p-6">
        <Mic aria-hidden className="text-brand" size={36} />
        <h2 className="text-2xl font-bold">{t("consentTitle")}</h2>
        <p className="text-lg">{t("consentBody")}</p>
        <BigButton onClick={onAccept}>{t("accept")}</BigButton>
      </div>
    </div>
  );
}
