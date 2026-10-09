"use client";
import { useEffect, type ReactNode } from "react";
import { LangProvider } from "@/lib/lang";
import { Header } from "./Header";

export function Providers({ children }: { children: ReactNode }) {
  useEffect(() => {
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  }, []);
  return (
    <LangProvider>
      <Header />
      <main className="mx-auto max-w-3xl space-y-4 px-4 py-6">{children}</main>
    </LangProvider>
  );
}
