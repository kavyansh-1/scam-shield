"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import type { UiLang } from "@/lib/types";

interface SRResult { isFinal: boolean; 0: { transcript: string } }
interface SREvent { resultIndex: number; results: ArrayLike<SRResult> }
interface SR {
  lang: string; continuous: boolean; interimResults: boolean;
  onresult: ((e: SREvent) => void) | null; onend: (() => void) | null; onerror: (() => void) | null;
  start: () => void; stop: () => void;
}
type SRCtor = new () => SR;

export function useSpeechRecognition(lang: UiLang, onText: (text: string, isFinal: boolean) => void) {
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const recRef = useRef<SR | null>(null);
  const wantRef = useRef(false);
  const cb = useRef(onText);
  cb.current = onText;

  useEffect(() => {
    const w = window as unknown as { SpeechRecognition?: SRCtor; webkitSpeechRecognition?: SRCtor };
    if (!(w.SpeechRecognition ?? w.webkitSpeechRecognition)) setSupported(false);
  }, []);

  const start = useCallback(() => {
    const w = window as unknown as { SpeechRecognition?: SRCtor; webkitSpeechRecognition?: SRCtor };
    const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
    if (!Ctor) { setSupported(false); return; }
    const rec = new Ctor();
    rec.lang = lang === "hi" ? "hi-IN" : "en-IN";
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (e) => {
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        cb.current(r[0].transcript.trim(), r.isFinal);
      }
    };
    rec.onend = () => { if (wantRef.current) { try { rec.start(); } catch { /* already started */ } } else setListening(false); };
    rec.onerror = () => {};
    recRef.current = rec;
    wantRef.current = true;
    try { rec.start(); setListening(true); } catch { setListening(false); }
  }, [lang]);

  const stop = useCallback(() => {
    wantRef.current = false;
    recRef.current?.stop();
    setListening(false);
  }, []);

  useEffect(() => () => { wantRef.current = false; recRef.current?.stop(); }, []);
  return { supported, listening, start, stop };
}
