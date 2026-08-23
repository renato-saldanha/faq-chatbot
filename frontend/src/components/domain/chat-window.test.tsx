import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { renderWithClient } from "@/lib/test-utils";
import type { ChatAskResponse } from "@/types/api";
import { ChatWindow } from "./chat-window";

vi.mock("@/lib/api");
vi.mock("sonner");

const mockedApi = vi.mocked(api);
const mockedToastError = vi.mocked(toast.error);

function fakeResponse(overrides: Partial<ChatAskResponse> = {}): ChatAskResponse {
  return {
    resposta: "Resposta qualquer",
    faq_item_id: 1,
    categoria: "Geral",
    sem_resposta: false,
    score: 0.9,
    ...overrides,
  };
}

function renderChatWindow() {
  return renderWithClient(<ChatWindow />);
}

async function askQuestion(pergunta: string) {
  const user = userEvent.setup();
  const input = screen.getByPlaceholderText("Digite sua pergunta...");
  await user.type(input, pergunta);
  await user.click(screen.getByRole("button", { name: "Enviar" }));
  return user;
}

describe("ChatWindow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("mostra o estado vazio inicial", () => {
    renderChatWindow();

    expect(screen.getByText(/Faça uma pergunta para começar/)).toBeInTheDocument();
  });

  it("clicar numa sugestão envia a pergunta correspondente", async () => {
    mockedApi.post.mockResolvedValueOnce(fakeResponse());
    const user = userEvent.setup();
    renderChatWindow();

    await user.click(screen.getByRole("button", { name: "Como recupero minha senha?" }));

    expect(screen.getByText("Como recupero minha senha?")).toBeInTheDocument();
    expect(mockedApi.post).toHaveBeenCalledWith("/api/chat/ask", {
      pergunta: "Como recupero minha senha?",
    });
  });

  it("envia a pergunta digitada e chama api.post com o payload correto", async () => {
    mockedApi.post.mockResolvedValueOnce(fakeResponse());

    renderChatWindow();
    await askQuestion("Qual o horário de funcionamento?");

    expect(screen.getByText("Qual o horário de funcionamento?")).toBeInTheDocument();
    expect(mockedApi.post).toHaveBeenCalledWith("/api/chat/ask", {
      pergunta: "Qual o horário de funcionamento?",
    });
  });

  it("limpa o campo de input após o envio", async () => {
    mockedApi.post.mockResolvedValueOnce(fakeResponse());

    renderChatWindow();
    await askQuestion("Alguma pergunta");

    const input = screen.getByPlaceholderText("Digite sua pergunta...") as HTMLInputElement;
    expect(input.value).toBe("");
  });

  it("exibe a resposta do bot após sucesso da mutation", async () => {
    mockedApi.post.mockResolvedValueOnce(
      fakeResponse({ resposta: "Nosso horário é das 9h às 18h.", faq_item_id: 5, categoria: "Atendimento", score: 0.95 }),
    );

    renderChatWindow();
    await askQuestion("Qual o horário de funcionamento?");

    expect(await screen.findByText("Nosso horário é das 9h às 18h.")).toBeInTheDocument();
  });

  it("exibe o badge 'Sem resposta encontrada' quando sem_resposta é true", async () => {
    mockedApi.post.mockResolvedValueOnce(
      fakeResponse({
        resposta: "Não encontrei uma resposta para isso.",
        faq_item_id: null,
        categoria: null,
        sem_resposta: true,
        score: null,
      }),
    );

    renderChatWindow();
    await askQuestion("Pergunta sem resposta na base");

    expect(await screen.findByText("Sem resposta encontrada")).toBeInTheDocument();
    expect(screen.getByText("Não encontrei uma resposta para isso.")).toBeInTheDocument();
  });

  it("chama toast.error, marca a pergunta como falha e não quebra quando a API falha", async () => {
    mockedApi.post.mockRejectedValueOnce(new Error("Erro 500: falha interna"));

    renderChatWindow();
    await askQuestion("Pergunta que vai falhar");

    await waitFor(() => {
      expect(mockedToastError).toHaveBeenCalledWith(
        "Não foi possível enviar sua pergunta. Toque em Enviar para tentar de novo.",
      );
    });
    expect(screen.getByText("Pergunta que vai falhar")).toBeInTheDocument();
    expect(screen.getByText("Não foi possível enviar")).toBeInTheDocument();
  });

  it("desabilita input e botão enquanto o envio está pendente", async () => {
    let resolvePromise: (value: ChatAskResponse) => void;
    const pending = new Promise<ChatAskResponse>((resolve) => {
      resolvePromise = resolve;
    });
    mockedApi.post.mockReturnValueOnce(pending);

    renderChatWindow();
    const user = userEvent.setup();
    const input = screen.getByPlaceholderText("Digite sua pergunta...");
    await user.type(input, "Pergunta pendente");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(input).toBeDisabled();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(screen.getByText("Digitando...")).toBeInTheDocument();

    resolvePromise!(fakeResponse({ resposta: "Resposta finalmente", faq_item_id: 2, score: 0.8 }));

    await waitFor(() => {
      expect(input).not.toBeDisabled();
    });
  });

  it("não envia pergunta vazia (botão desabilitado sem texto)", () => {
    renderChatWindow();

    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(mockedApi.post).not.toHaveBeenCalled();
  });
});
