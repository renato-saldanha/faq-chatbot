import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { TimeseriesChart } from "./timeseries-chart";
import type { DailyCount } from "@/types/api";

beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

afterEach(() => {
  cleanup();
});

describe("TimeseriesChart", () => {
  it("mostra estado 'sem dados' e não lança exceção quando o array está vazio", () => {
    expect(() => render(<TimeseriesChart data={[]} />)).not.toThrow();

    expect(screen.getByText("Sem dados no período.")).toBeInTheDocument();
  });

  it("renderiza o container do gráfico quando há dados válidos", () => {
    const data: DailyCount[] = [
      { data: "2026-08-20", quantidade: 3 },
      { data: "2026-08-21", quantidade: 7 },
      { data: "2026-08-22", quantidade: 2 },
    ];

    const { container } = render(<TimeseriesChart data={data} />);

    expect(screen.queryByText("Sem dados no período.")).not.toBeInTheDocument();
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });
});
