import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { renderWithClient } from "@/lib/test-utils";
import type { CategoryBreakdown, DailyCount, MetricsSummary, TopQuestion, UnansweredQuestion } from "@/types/api";
import MetricasPage from "./page";

vi.mock("@/lib/api");

const summaryFake: MetricsSummary = { total_conversas: 10, total_sem_resposta: 2, taxa_sem_resposta: 0.2 };
const timeseriesFake: DailyCount[] = [];
const topQuestionsFake: TopQuestion[] = [];
const categoriesFake: CategoryBreakdown[] = [];
const unansweredFake: UnansweredQuestion[] = [];

function mockGetSuccess() {
  vi.mocked(api.get).mockImplementation((path: string) => {
    if (path.includes("/summary")) return Promise.resolve(summaryFake) as ReturnType<typeof api.get>;
    if (path.includes("/timeseries")) return Promise.resolve(timeseriesFake) as ReturnType<typeof api.get>;
    if (path.includes("/top-questions")) return Promise.resolve(topQuestionsFake) as ReturnType<typeof api.get>;
    if (path.includes("/categories")) return Promise.resolve(categoriesFake) as ReturnType<typeof api.get>;
    if (path.includes("/unanswered")) return Promise.resolve(unansweredFake) as ReturnType<typeof api.get>;
    return Promise.reject(new Error(`path não mapeado: ${path}`));
  });
}

function renderPage() {
  return renderWithClient(<MetricasPage />);
}

describe("MetricasPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("não mostra o banner de erro quando todas as métricas carregam com sucesso", async () => {
    mockGetSuccess();

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("10")).toBeInTheDocument();
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("mostra banner de erro quando qualquer métrica falha ao carregar", async () => {
    vi.mocked(api.get).mockImplementation((path: string) => {
      if (path.includes("/summary")) return Promise.reject(new Error("Erro 500: falha interna"));
      return Promise.resolve([]) as ReturnType<typeof api.get>;
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Não foi possível carregar todas as métricas. Tente recarregar a página.",
      );
    });
  });
});
