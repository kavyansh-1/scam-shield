"use client";
import { Camera, ImageUp } from "lucide-react";
import { useRef, useState } from "react";
import { useLang } from "@/lib/lang";

export function ScreenshotDropzone({ file, onFile }: { file: File | null; onFile: (f: File | null) => void }) {
  const { t } = useLang();
  const pick = useRef<HTMLInputElement>(null);
  const cam = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const take = (f: File | undefined) => { if (f && /^image\/(png|jpe?g|webp)$/.test(f.type)) onFile(f); };
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files[0]); }}
      className={`rounded-2xl border-2 border-dashed p-5 text-center ${over ? "border-brand bg-teal-50" : "border-line bg-white"}`}
    >
      <ImageUp aria-hidden className="mx-auto mb-2 text-brand" size={32} />
      <p className="mb-3 text-lg">{file ? file.name : t("dropShot")}</p>
      <div className="flex flex-col gap-2 sm:flex-row">
        <button type="button" onClick={() => pick.current?.click()} className="min-h-[48px] flex-1 rounded-xl border-2 border-brand px-4 font-semibold text-brand">{t("chooseFile")}</button>
        <button type="button" onClick={() => cam.current?.click()} className="flex min-h-[48px] flex-1 items-center justify-center gap-2 rounded-xl border-2 border-brand px-4 font-semibold text-brand">
          <Camera size={20} aria-hidden /> {t("camera")}
        </button>
      </div>
      <input ref={pick} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={(e) => take(e.target.files?.[0])} />
      <input ref={cam} type="file" accept="image/*" capture="environment" hidden onChange={(e) => take(e.target.files?.[0])} />
      {file && <button type="button" onClick={() => onFile(null)} className="mt-3 min-h-[44px] text-base underline">✕ {file.name}</button>}
    </div>
  );
}
