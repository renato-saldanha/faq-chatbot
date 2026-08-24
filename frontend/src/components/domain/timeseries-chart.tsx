"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyCount } from "@/types/api";

interface TimeseriesChartProps {
  data: DailyCount[];
}

export function TimeseriesChart({ data }: TimeseriesChartProps) {
  if (data.length === 0) {
    return <p className="chart-empty">Sem dados no período.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="data" stroke="var(--ink-faint)" tick={{ fill: "var(--ink-soft)" }} />
        <YAxis allowDecimals={false} stroke="var(--ink-faint)" tick={{ fill: "var(--ink-soft)" }} />
        <Tooltip
          contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 8 }}
          labelStyle={{ color: "var(--ink)" }}
        />
        <Line type="monotone" dataKey="quantidade" stroke="var(--primary)" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
