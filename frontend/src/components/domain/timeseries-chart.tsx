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
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="data" />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Line type="monotone" dataKey="quantidade" stroke="#2563eb" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
