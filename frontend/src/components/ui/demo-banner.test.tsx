import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DemoBanner } from "@/components/ui/demo-banner";

describe("DemoBanner", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("não renderiza fora do modo demonstração", () => {
    vi.stubEnv("NEXT_PUBLIC_DEMO", "");
    render(<DemoBanner />);

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("renderiza a faixa com NEXT_PUBLIC_DEMO=1", () => {
    vi.stubEnv("NEXT_PUBLIC_DEMO", "1");
    render(<DemoBanner />);

    expect(screen.getByRole("status")).toHaveTextContent("Modo demonstração: dados fictícios");
  });
});
