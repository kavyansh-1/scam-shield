"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { dict, type Key } from "./i18n";
import type { UiLang } from "./types";

interface Ctx { lang: UiLang; setLang: (l: UiLang) => void; t: (k: Key) => string }
const LangCtx = createContext<Ctx>({ lang: "en", setLang: () => {}, t: (k) => dict.en[k] });

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<UiLang>("en");
  useEffect(() => {
    try {
      const s = localStorage.getItem("ss_lang");
      if (s === "hi" || s === "en") setLangState(s);
    } catch { /* ignore */ }
  }, []);
  const setLang = (l: UiLang) => {
    setLangState(l);
    try { localStorage.setItem("ss_lang", l); } catch { /* ignore */ }
    document.documentElement.lang = l;
  };
  const t = (k: Key) => dict[lang][k];
  return <LangCtx.Provider value={{ lang, setLang, t }}>{children}</LangCtx.Provider>;
}
export const useLang = () => useContext(LangCtx);
