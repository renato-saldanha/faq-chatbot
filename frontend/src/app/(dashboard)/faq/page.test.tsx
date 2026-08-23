import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { toast } from "sonner";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import type { Categoria, FaqItem } from "@/types/api";
import FaqAdminPage from "./page";

vi.mock("@/lib/api");
vi.mock("sonner");

const categoriasFake: Categoria[] = [
  { id: 1, nome: "Conta", slug: "conta" },
  { id: 2, nome: "Pagamento", slug: "pagamento" },
];

const faqItemsFake: FaqItem[] = [
  {
    id: 10,
    categoria_id: 1,
    categoria_nome: "Conta",
    pergunta: "Como resetar minha senha?",
    resposta: "Acesse configurações e clique em redefinir senha para receber um e-mail com as instruções.",
    ativo: true,
  },
  {
    id: 11,
    categoria_id: 2,
    categoria_nome: "Pagamento",
    pergunta: "Como funciona o reembolso?",
    resposta: "Reembolsos são processados em até 5 dias úteis.",
    ativo: false,
  },
];

function mockGetDefault() {
  vi.mocked(api.get).mockImplementation((path: string) => {
    if (path.includes("categorias")) {
      return Promise.resolve(categoriasFake) as ReturnType<typeof api.get>;
    }
    return Promise.resolve(faqItemsFake) as ReturnType<typeof api.get>;
  });
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }

  return {
    queryClient,
    ...render(<FaqAdminPage />, { wrapper: Wrapper }),
  };
}

function getRowByPergunta(pergunta: string) {
  const cell = screen.getByText(pergunta);
  const row = cell.closest("tr");
  if (!row) throw new Error(`Linha da tabela não encontrada para "${pergunta}"`);
  return row as HTMLElement;
}

describe("FaqAdminPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockGetDefault();
  });

  afterEach(() => {
    cleanup();
  });

  it("renderiza os itens de FAQ retornados pela query (pergunta, resposta truncada, categoria, ativo)", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Como resetar minha senha?")).toBeInTheDocument();
    });

    const row1 = getRowByPergunta("Como resetar minha senha?");
    const respostaCell = within(row1).getAllByRole("cell")[1];
    expect(respostaCell.textContent).toBe(
      "Acesse configurações e clique em redefinir senha para recebe...",
    );
    expect(within(row1).getByText("Conta")).toBeInTheDocument();
    expect(within(row1).getByText("Sim")).toBeInTheDocument();

    const row2 = getRowByPergunta("Como funciona o reembolso?");
    expect(within(row2).getByText("Reembolsos são processados em até 5 dias úteis.")).toBeInTheDocument();
    expect(within(row2).getByText("Pagamento")).toBeInTheDocument();
    expect(within(row2).getByText("Não")).toBeInTheDocument();
  });

  it('mostra "Nenhuma pergunta cadastrada." quando a lista vem vazia', async () => {
    vi.mocked(api.get).mockImplementation((path: string) => {
      if (path.includes("categorias")) {
        return Promise.resolve(categoriasFake) as ReturnType<typeof api.get>;
      }
      return Promise.resolve([]) as ReturnType<typeof api.get>;
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Nenhuma pergunta cadastrada.")).toBeInTheDocument();
    });
  });

  it('clicar em "Nova pergunta" abre o formulário; preencher e submeter chama api.post com o payload certo', async () => {
    const user = userEvent.setup();
    vi.mocked(api.post).mockResolvedValue({} as FaqItem);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Como resetar minha senha?")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Nova pergunta" }));

    expect(screen.getByRole("button", { name: "Salvar" })).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Categoria"), "2");
    await user.type(screen.getByLabelText("Pergunta"), "Qual o prazo de entrega?");
    await user.type(screen.getByLabelText("Resposta"), "O prazo é de 3 dias úteis.");

    await user.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/api/faq", {
        categoria_id: 2,
        pergunta: "Qual o prazo de entrega?",
        resposta: "O prazo é de 3 dias úteis.",
        ativo: true,
      });
    });
  });

  it("sucesso ao salvar dispara invalidateQueries (refetch da lista), mostra toast de sucesso e fecha o form", async () => {
    const user = userEvent.setup();
    vi.mocked(api.post).mockResolvedValue({} as FaqItem);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Como resetar minha senha?")).toBeInTheDocument();
    });

    const getCallsBeforeSubmit = vi.mocked(api.get).mock.calls.length;

    await user.click(screen.getByRole("button", { name: "Nova pergunta" }));
    await user.selectOptions(screen.getByLabelText("Categoria"), "1");
    await user.type(screen.getByLabelText("Pergunta"), "Nova pergunta de teste?");
    await user.type(screen.getByLabelText("Resposta"), "Resposta de teste.");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Pergunta salva com sucesso.");
    });

    // Form fecha (volta a mostrar "Nova pergunta")
    expect(screen.getByRole("button", { name: "Nova pergunta" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Salvar" })).not.toBeInTheDocument();

    // invalidateQueries força refetch de faq-items -> mais chamadas de api.get do que antes do submit
    await waitFor(() => {
      expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThan(getCallsBeforeSubmit);
    });
  });

  it('clicar em "Editar" preenche o formulário com os dados do item e submete via PUT', async () => {
    const user = userEvent.setup();
    vi.mocked(api.put).mockResolvedValue({} as FaqItem);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Como resetar minha senha?")).toBeInTheDocument();
    });

    const row = getRowByPergunta("Como resetar minha senha?");
    await user.click(within(row).getByRole("button", { name: "Editar" }));

    const perguntaField = screen.getByLabelText("Pergunta") as HTMLTextAreaElement;
    const respostaField = screen.getByLabelText("Resposta") as HTMLTextAreaElement;
    const categoriaField = screen.getByLabelText("Categoria") as HTMLSelectElement;

    expect(perguntaField.value).toBe("Como resetar minha senha?");
    expect(respostaField.value).toBe(
      "Acesse configurações e clique em redefinir senha para receber um e-mail com as instruções.",
    );
    expect(categoriaField.value).toBe("1");

    await user.clear(perguntaField);
    await user.type(perguntaField, "Como resetar minha senha? (editado)");

    await user.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith("/api/faq/10", {
        categoria_id: 1,
        pergunta: "Como resetar minha senha? (editado)",
        resposta: "Acesse configurações e clique em redefinir senha para receber um e-mail com as instruções.",
        ativo: true,
      });
    });
    expect(api.post).not.toHaveBeenCalled();
  });

  it('clicar em "Excluir" com window.confirm retornando true chama api.delete', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.mocked(api.delete).mockResolvedValue(undefined);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Como resetar minha senha?")).toBeInTheDocument();
    });

    const row = getRowByPergunta("Como resetar minha senha?");
    await user.click(within(row).getByRole("button", { name: "Excluir" }));

    expect(window.confirm).toHaveBeenCalledWith("Excluir esta pergunta?");
    await waitFor(() => {
      expect(api.delete).toHaveBeenCalledWith("/api/faq/10");
    });
  });

  it('clicar em "Excluir" com window.confirm retornando false NÃO chama api.delete', async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    vi.mocked(api.delete).mockResolvedValue(undefined);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Como resetar minha senha?")).toBeInTheDocument();
    });

    const row = getRowByPergunta("Como resetar minha senha?");
    await user.click(within(row).getByRole("button", { name: "Excluir" }));

    expect(window.confirm).toHaveBeenCalledWith("Excluir esta pergunta?");
    expect(api.delete).not.toHaveBeenCalled();
  });
});
