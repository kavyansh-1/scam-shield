"use client";
import { useEffect, useRef } from "react";
import { HighlightedText } from "./ui";

export interface Line { id: number; who: "scammer" | "victim" | "mic"; text: string }
export function LiveTranscript({ lines, evidence, interim }: { lines: Line[]; evidence: string[]; interim: string }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [lines, interim]);
  return (
    <div className="max-h-72 space-y-2 overflow-y-auto rounded-2xl border border-line bg-white p-4" aria-live="polite">
      {lines.map((l) => (
        <p key={l.id} className={`rounded-xl px-3 py-2 text-lg ${l.who === "victim" ? "ml-8 bg-teal-50" : "mr-8 bg-slate-100"}`}>
          <HighlightedText text={l.text} evidence={evidence} />
        </p>
      ))}
      {interim && <p className="px-3 text-lg italic text-ink/60">{interim}</p>}
      <div ref={end} />
    </div>
  );
}
