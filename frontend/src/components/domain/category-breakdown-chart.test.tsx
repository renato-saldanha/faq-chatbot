import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CategoryBreakdownChart } from "./category-breakdown-chart";
import type { CategoryBreakdown } from "@/types/api";

describe("CategoryBreakdownChart", () => {
  it("mostra estado 'sem dados' e não lança exceção quando o array está vazio", () => {
    expect(() => render(<CategoryBreakdownChart data={[]} />)).not.toThrow();

    expect(screen.getByText("Sem dados no período.")).toBeInTheDocument();
  });

  it("renderiza o container do gráfico quando há dados válidos", () => {
    const data: CategoryBreakdown[] = [
      { categoria: "Conta", quantidade: 5 },
      { categoria: "Pagamento", quantidade: 12 },
      { categoria: "Outros", quantidade: 1 },
    ];

    const { container } = render(<CategoryBreakdownChart data={data} />);

    expect(screen.queryByText("Sem dados no período.")).not.toBeInTheDocument();
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });
});
