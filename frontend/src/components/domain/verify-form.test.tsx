import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { renderWithClient } from "@/lib/test-utils";
import { VerifyForm } from "@/components/domain/verify-form";
import { useAuthStore } from "@/stores/auth-store";

vi.mock("@/lib/api");
vi.mock("sonner");

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

describe("VerifyForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ isAuthenticated: false, hasHydrated: false });
  });

  it("renderiza campo de código e botão de verificar", () => {
    renderWithClient(<VerifyForm email="usuario@example.com" />);

    expect(screen.getByLabelText("Código de 6 dígitos")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verificar" })).toBeInTheDocument();
  });

  it("preenche código e submete chamando api.post com email e codigo corretos", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ authenticated: false });
    const user = userEvent.setup();
    renderWithClient(<VerifyForm email="usuario@example.com" />);

    await user.type(screen.getByLabelText("Código de 6 dígitos"), "123456");
    await user.click(screen.getByRole("button", { name: "Verificar" }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/api/auth/otp/verify", {
        email: "usuario@example.com",
        codigo: "123456",
      });
    });
  });

  it("em sucesso com authenticated: true, autentica na store e navega para /metricas", async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ authenticated: true });
    const user = userEvent.setup();
    renderWithClient(<VerifyForm email="usuario@example.com" />);

    await user.type(screen.getByLabelText("Código de 6 dígitos"), "123456");
    await user.click(screen.getByRole("button", { name: "Verificar" }));

    await waitFor(() => {
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });
    expect(pushMock).toHaveBeenCalledWith("/metricas");
  });

  it("em caso de erro (código inválido), chama toast.error e não navega", async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error("Erro 401: código inválido"));
    const user = userEvent.setup();
    renderWithClient(<VerifyForm email="usuario@example.com" />);

    await user.type(screen.getByLabelText("Código de 6 dígitos"), "000000");
    await user.click(screen.getByRole("button", { name: "Verificar" }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Código inválido ou expirado.");
    });
    expect(pushMock).not.toHaveBeenCalled();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
