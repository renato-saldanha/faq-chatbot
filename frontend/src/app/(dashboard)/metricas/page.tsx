"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { CategoryBreakdownChart } from "@/components/domain/category-breakdown-chart";
import { MetricCard } from "@/components/domain/metric-card";
import { TimeseriesChart } from "@/components/domain/timeseries-chart";
import { api } from "@/lib/api";
import type {
  CategoryBreakdown,
  DailyCount,
  MetricsSummary,
  TopQuestion,
  UnansweredQuestion,
} from "@/types/api";

function buildQuery(dateFrom: string, dateTo: string): string {
  const params = new URLSearchParams();
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export default function MetricasPage() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const qs = buildQuery(dateFrom, dateTo);

  const summary = useQuery({
    queryKey: ["metrics-summary", dateFrom, dateTo],
    queryFn: () => api.get<MetricsSummary>(`/api/metrics/summary${qs}`),
  });
  const timeseries = useQuery({
    queryKey: ["metrics-timeseries", dateFrom, dateTo],
    queryFn: () => api.get<DailyCount[]>(`/api/metrics/timeseries${qs}`),
  });
  const topQuestions = useQuery({
    queryKey: ["metrics-top-questions", dateFrom, dateTo],
    queryFn: () => api.get<TopQuestion[]>(`/api/metrics/top-questions${qs}`),
  });
  const categories = useQuery({
    queryKey: ["metrics-categories", dateFrom, dateTo],
    queryFn: () => api.get<CategoryBreakdown[]>(`/api/metrics/categories${qs}`),
  });
  const unanswered = useQuery({
    queryKey: ["metrics-unanswered", dateFrom, dateTo],
    queryFn: () => api.get<UnansweredQuestion[]>(`/api/metrics/unanswered${qs}`),
  });

  return (
    <div>
      <h1>Métricas</h1>

      <div className="date-filter">
        <label>
          De
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>
        <label>
          Até
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>
      </div>

      <div className="metrics-grid">
        <MetricCard label="Total de conversas" value={summary.data?.total_conversas ?? "—"} />
        <MetricCard label="Sem resposta" value={summary.data?.total_sem_resposta ?? "—"} />
        <MetricCard
          label="Taxa sem resposta"
          value={summary.data ? `${(summary.data.taxa_sem_resposta * 100).toFixed(1)}%` : "—"}
        />
      </div>

      <section className="chart-section">
        <h2>Evolução das consultas</h2>
        <TimeseriesChart data={timeseries.data ?? []} />
      </section>

      <section className="chart-section">
        <h2>Distribuição por categoria</h2>
        <CategoryBreakdownChart data={categories.data ?? []} />
      </section>

      <section className="table-section">
        <h2>Perguntas mais frequentes</h2>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Pergunta</th>
                <th>Quantidade</th>
              </tr>
            </thead>
            <tbody>
              {(topQuestions.data ?? []).map((q) => (
                <tr key={q.faq_item_id}>
                  <td>{q.pergunta}</td>
                  <td>{q.quantidade}</td>
                </tr>
              ))}
              {topQuestions.data?.length === 0 && (
                <tr>
                  <td colSpan={2}>Sem dados no período.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="table-section">
        <h2>Perguntas sem resposta</h2>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Pergunta</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {(unanswered.data ?? []).map((q) => (
                <tr key={q.id}>
                  <td>{q.pergunta_usuario}</td>
                  <td>{new Date(q.criado_em).toLocaleString("pt-BR")}</td>
                </tr>
              ))}
              {unanswered.data?.length === 0 && (
                <tr>
                  <td colSpan={2}>Nenhuma pergunta sem resposta no período.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
