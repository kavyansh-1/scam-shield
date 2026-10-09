"use client";
import Link from "next/link";
import { Mic, ShieldCheck, Users, MessageSquareWarning, GraduationCap, BarChart3 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useLang } from "@/lib/lang";
import { useUser } from "@/hooks/useUser";
import type { ReactNode } from "react";

function Tile({ href, icon, title, sub }: { href: string; icon: ReactNode; title: string; sub: string }) {
  return (
    <Link href={href} className="flex min-h-[96px] items-center gap-4 rounded-2xl border-2 border-brand bg-white p-5 focus-visible:ring-4 focus-visible:ring-brand/40">
      <span aria-hidden className="text-brand">{icon}</span>
      <span><span className="block text-2xl font-bold">{title}</span><span className="block text-lg text-ink/70">{sub}</span></span>
    </Link>
  );
}

export default function Home() {
  const { t } = useLang();
  const { userId } = useUser();
  const [linked, setLinked] = useState<boolean | null>(null);
  useEffect(() => {
    if (!userId) return;
    api.getGuardians(userId).then((g) => setLinked(g.guardians.some((x) => x.linked))).catch(() => setLinked(false));
  }, [userId]);
  return (
    <>
      <div className="flex items-center gap-3">
        <ShieldCheck aria-hidden size={40} className="text-brand" />
        <h1 className="text-3xl font-extrabold leading-tight">{t("tagline")}</h1>
      </div>
      <Link href="/guardian" className={`inline-flex min-h-[44px] items-center gap-2 rounded-full px-4 py-2 text-lg font-semibold ${linked ? "bg-green-100 text-safe" : "bg-amber-100 text-warn"}`}>
        <Users aria-hidden size={20} /> {linked ? `✓ ${t("guardianLinked")}` : t("guardianNot")}
      </Link>
      <div className="space-y-3">
        <Tile href="/check" icon={<MessageSquareWarning size={40} />} title={t("check")} sub={t("checkSub")} />
        <Tile href="/live" icon={<Mic size={40} />} title={t("listen")} sub={t("listenSub")} />
        <Tile href="/practice" icon={<GraduationCap size={40} />} title={t("practice")} sub={t("practiceSub")} />
      </div>
      <div className="flex flex-wrap gap-4 text-lg">
        <Link href="/live?demo=hinglish" className="min-h-[44px] py-2 text-brand underline">{t("replay")}</Link>
        <Link href="/dashboard" className="flex min-h-[44px] items-center gap-1 py-2 text-brand underline"><BarChart3 size={18} aria-hidden /> {t("dashboard")}</Link>
      </div>
    </>
  );
}
