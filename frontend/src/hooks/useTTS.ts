"use client";
import { useCallback } from "react";
import type { UiLang } from "@/lib/types";

export function useTTS(lang: UiLang): { speak: (text: string) => void; cancel: () => void } {
  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const tag = lang === "hi" ? "hi-IN" : "en-IN";
    const u = new SpeechSynthesisUtterance(text);
    u.lang = tag;
    const voices = window.speechSynthesis.getVoices();
    const v = voices.find((x) => x.lang === tag) ?? voices.find((x) => x.lang.startsWith(lang));
    if (v) u.voice = v;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }, [lang]);
  const cancel = useCallback(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
  }, []);
  return { speak, cancel };
}
