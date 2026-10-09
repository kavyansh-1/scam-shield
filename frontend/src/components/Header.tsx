"use client";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useLang } from "@/lib/lang";
import { LanguageToggle } from "./ui";

export function Header() {
  const { t } = useLang();
  const [live, setLive] = useState<boolean | null>(null);
  useEffect(() => {
    api.health().then((h) => setLive(h.llm !== "mock")).catch(() => setLive(null));
  }, []);
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper/95 backdrop-blur">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2 px-4 py-2">
        <Link href="/" className="flex min-h-[44px] items-center gap-2 text-xl font-bold text-brand">
          <ShieldCheck aria-hidden size={26} /> {t("appName")}
        </Link>
        <div className="flex items-center gap-2">
          {live !== null && (
            <span className={`rounded-full px-3 py-1 text-sm font-semibold ${live ? "bg-green-100 text-safe" : "bg-amber-100 text-warn"}`}>
              {live ? t("liveMode") : t("demoMode")}
            </span>
          )}
          <LanguageToggle />
        </div>
      </div>
    </header>
  );
}
