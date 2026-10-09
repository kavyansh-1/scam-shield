"use client";
import { QRCodeSVG } from "qrcode.react";
import { useLang } from "@/lib/lang";
import { Card } from "./ui";

export function GuardianLinkCard({ code, link, linked }: { code: string; link: string; linked: boolean }) {
  const { t } = useLang();
  return (
    <Card className="space-y-3 text-center">
      <p className="text-lg">{t("scanQr")}</p>
      <div className="mx-auto w-fit rounded-xl bg-white p-3"><QRCodeSVG value={link} size={200} /></div>
      <p className="text-lg">{t("code")}: <strong className="tracking-widest">{code}</strong></p>
      <a href={link} target="_blank" rel="noreferrer" className="block break-all text-base text-brand underline">{link}</a>
      <p role="status" className={`text-lg font-semibold ${linked ? "text-safe" : "text-ink/70"}`}>{linked ? `✓ ${t("linked")}` : t("waiting")}</p>
    </Card>
  );
}
