"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CategoryBreakdown } from "@/types/api";

interface CategoryBreakdownChartProps {
  data: CategoryBreakdown[];
}

export function CategoryBreakdownChart({ data }: CategoryBreakdownChartProps) {
  if (data.length === 0) {
    return <p className="chart-empty">Sem dados no período.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="categoria" stroke="var(--ink-faint)" tick={{ fill: "var(--ink-soft)" }} />
        <YAxis allowDecimals={false} stroke="var(--ink-faint)" tick={{ fill: "var(--ink-soft)" }} />
        <Tooltip
          contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 8 }}
          labelStyle={{ color: "var(--ink)" }}
        />
        <Bar dataKey="quantidade" fill="var(--primary)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
