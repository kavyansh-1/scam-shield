export function ChatBubble({ from, text, typing }: { from: "scammer" | "user"; text?: string; typing?: boolean }) {
  return (
    <div className={`flex ${from === "user" ? "justify-end" : "justify-start"}`}>
      <p className={`max-w-[85%] rounded-2xl px-4 py-3 text-lg ${from === "user" ? "bg-brand text-white" : "bg-slate-200"}`}>
        {typing ? <span aria-label="typing">● ● ●</span> : text}
      </p>
    </div>
  );
}
