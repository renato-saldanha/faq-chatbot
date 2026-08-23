import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { renderWithClient } from "@/lib/test-utils";
import { LoginForm } from "@/components/domain/login-form";

vi.mock("@/lib/api");
vi.mock("sonner");
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza campo de e-mail e botão de enviar código", () => {
    renderWithClient(<LoginForm />);

    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar código" })).toBeInTheDocument();
  });

  it("preenche e-mail e submete chamando api.post com o e-mail informado", async () => {
    vi.mocked(api.post).mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderWithClient(<LoginForm />);

    await user.type(screen.getByLabelText("E-mail"), "usuario@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar código" }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/api/auth/otp/request", {
        email: "usuario@example.com",
      });
    });
  });

  it("em caso de sucesso, troca para exibir o VerifyForm", async () => {
    vi.mocked(api.post).mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderWithClient(<LoginForm />);

    await user.type(screen.getByLabelText("E-mail"), "usuario@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar código" }));

    expect(await screen.findByLabelText("Código de 6 dígitos")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verificar" })).toBeInTheDocument();
  });

  it("em caso de erro, chama toast.error e mantém o formulário de e-mail visível", async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error("Erro 500: falha"));
    const user = userEvent.setup();
    renderWithClient(<LoginForm />);

    await user.type(screen.getByLabelText("E-mail"), "usuario@example.com");
    await user.click(screen.getByRole("button", { name: "Enviar código" }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Erro ao solicitar código. Tente novamente.");
    });
    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.queryByLabelText("Código de 6 dígitos")).not.toBeInTheDocument();
  });
});
