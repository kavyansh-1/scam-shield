"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { MOCK, WS_URL, uuid } from "@/lib/api";
import { MockSocket } from "@/lib/mockSocket";
import type { ClientMsg, ServerMsg } from "@/lib/types";

export type SocketStatus = "idle" | "connecting" | "open" | "reconnecting" | "closed";

export function useLiveSocket(onMessage: (m: ServerMsg) => void) {
  const [status, setStatus] = useState<SocketStatus>("idle");
  const wsRef = useRef<WebSocket | null>(null);
  const mockRef = useRef<MockSocket | null>(null);
  const queue = useRef<ClientMsg[]>([]);
  const handler = useRef(onMessage);
  handler.current = onMessage;
  const urlRef = useRef("");
  const wantOpen = useRef(false);
  const retries = useRef(0);

  const connect = useCallback(() => {
    const ws = new WebSocket(urlRef.current);
    wsRef.current = ws;
    ws.onopen = () => {
      retries.current = 0;
      setStatus("open");
      queue.current.forEach((m) => ws.send(JSON.stringify(m)));
      queue.current = [];
    };
    ws.onmessage = (e: MessageEvent<string>) => {
      try { handler.current(JSON.parse(e.data) as ServerMsg); } catch { /* ignore bad frame */ }
    };
    ws.onclose = () => {
      if (!wantOpen.current) { setStatus("closed"); return; }
      setStatus("reconnecting");
      const delay = Math.min(8000, 500 * 2 ** retries.current++);
      setTimeout(() => { if (wantOpen.current) connect(); }, delay);
    };
    ws.onerror = () => ws.close();
  }, []);

  const open = useCallback((userId: string) => {
    queue.current = [];
    wantOpen.current = true;
    if (MOCK) {
      mockRef.current = new MockSocket((m) => handler.current(m));
      setStatus("open");
      return;
    }
    urlRef.current = `${WS_URL}/ws/live?session_id=${uuid()}&user_id=${userId}`;
    setStatus("connecting");
    connect();
  }, [connect]);

  const send = useCallback((m: ClientMsg) => {
    if (MOCK) { mockRef.current?.send(m); return; }
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(m));
    else queue.current.push(m);
  }, []);

  const close = useCallback(() => {
    wantOpen.current = false;
    wsRef.current?.close();
    wsRef.current = null;
    mockRef.current = null;
    setStatus("closed");
  }, []);

  useEffect(() => () => { wantOpen.current = false; wsRef.current?.close(); }, []);
  return { status, open, send, close };
}
