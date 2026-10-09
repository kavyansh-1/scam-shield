"use client";
import { useParams } from "next/navigation";
import { FileText } from "lucide-react";
import { api, MOCK } from "@/lib/api";
import { useLang } from "@/lib/lang";
import { BigButton, Card } from "@/components/ui";

export default function Report() {
  const { id } = useParams<{ id: string }>();
  const { t } = useLang();
  const url = api.pdfUrl(id);
  return (
    <>
      <h1 className="flex items-center gap-2 text-3xl font-extrabold"><FileText aria-hidden /> {t("reportReady")}</h1>
      <Card className="space-y-4">
        <p className="text-xl">{t("helpline")}</p>
        {MOCK ? <p className="text-lg text-warn">{t("demoMode")}: PDF needs the backend.</p> : (
          <>
            <a href={url} target="_blank" rel="noreferrer" className="inline-flex min-h-[52px] w-full items-center justify-center rounded-xl bg-brand px-5 text-lg font-semibold text-white">{t("downloadPdf")}</a>
            <iframe title={t("reportReady")} src={url} className="h-[480px] w-full rounded-xl border border-line" />
          </>
        )}
        <BigButton variant="secondary" href="/">{t("home")}</BigButton>
      </Card>
    </>
  );
}
