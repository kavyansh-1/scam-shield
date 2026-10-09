"use client";
import { useLang } from "@/lib/lang";
import type { Bilingual } from "@/lib/types";

export function CoachTip({ tip, safe }: { tip: Bilingual; safe: boolean }) {
  const { lang } = useLang();
  return (
    <p className={`rounded-xl border-l-8 p-3 text-lg ${safe ? "border-safe bg-green-50" : "border-warn bg-amber-50"}`}>
      {safe ? "✓ " : "⚠ "}{tip[lang]}
    </p>
  );
}
