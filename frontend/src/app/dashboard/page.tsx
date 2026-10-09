"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, errMsg } from "@/lib/api";
import { useLang } from "@/lib/lang";
import type { Stats } from "@/lib/types";
import { ImpactStats } from "@/components/ImpactStats";
import { BigButton, Card, ErrorBox, Spinner } from "@/components/ui";

const COLORS = ["#0E6B7A", "#B3171C", "#8A5300", "#14632E", "#5B4B8A"];

export default function Dashboard() {
  const { t } = useLang();
  const [s, setS] = useState<Stats | null>(null);
  const [err, setErr] = useState("");
  const load = useCallback(() => { api.stats().then((x) => { setS(x); setErr(""); }).catch((e) => setErr(errMsg(e))); }, []);
  useEffect(() => { load(); const i = setInterval(load, 10000); return () => clearInterval(i); }, [load]);

  if (err && !s) return <ErrorBox message={err} />;
  if (!s) return <Spinner label={t("loading")} />;
  const empty = s.scams_caught + s.suspicious_flagged === 0;
  return (
    <>
      <h1 className="text-3xl font-extrabold">{t("dashboard")}</h1>
      <ImpactStats stats={s} />
      {empty ? (
        <Card className="space-y-3 text-center"><p className="text-lg">{t("noData")}</p><BigButton href="/live?demo=hinglish">{t("runDemo")}</BigButton></Card>
      ) : (
        <>
          <Card><h2 className="mb-2 text-xl font-bold">{t("byType")}</h2>
            <div className="h-64"><ResponsiveContainer><BarChart data={s.by_type.map((d) => ({ ...d, scam_type: d.scam_type.replace(/_/g, " ") }))}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="scam_type" tick={{ fontSize: 12 }} /><YAxis allowDecimals={false} /><Tooltip />
              <Bar dataKey="count" fill="#0E6B7A" /></BarChart></ResponsiveContainer></div></Card>
          <Card><h2 className="mb-2 text-xl font-bold">{t("byDay")}</h2>
            <div className="h-56"><ResponsiveContainer><LineChart data={s.by_day}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" tick={{ fontSize: 12 }} /><YAxis allowDecimals={false} /><Tooltip />
              <Line dataKey="count" stroke="#B3171C" strokeWidth={3} /></LineChart></ResponsiveContainer></div></Card>
          <Card><h2 className="mb-2 text-xl font-bold">{t("byLanguage")}</h2>
            <div className="h-64"><ResponsiveContainer><PieChart>
              <Pie data={s.by_language} dataKey="count" nameKey="language" innerRadius={50} outerRadius={85}>
                {s.by_language.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie>
              <Tooltip /><Legend /></PieChart></ResponsiveContainer></div></Card>
        </>
      )}
      <Link href="/" className="inline-block min-h-[44px] py-2 text-lg text-brand underline">{t("home")}</Link>
    </>
  );
}
