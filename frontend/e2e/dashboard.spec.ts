import { expect, test } from "@playwright/test";
import { STORAGE_STATE } from "./helpers/storage-state";

test.use({ storageState: STORAGE_STATE });

test.describe.serial("Painel admin autenticado", () => {
  test("CRUD de FAQ ponta a ponta e reflete no chat público", async ({ page }) => {
    await page.goto("/faq");
    await expect(page.getByRole("heading", { name: "Base de Conhecimento" })).toBeVisible();

    await page.getByRole("button", { name: "Nova pergunta" }).click();
    const pergunta = `Pergunta E2E ${Date.now()}`;
    await page.getByLabel("Categoria").selectOption({ index: 1 });
    await page.getByLabel("Pergunta").fill(pergunta);
    await page.getByLabel("Resposta").fill("Resposta criada pelo teste E2E.");
    await page.getByRole("button", { name: "Salvar" }).click();

    await expect(page.getByRole("cell", { name: pergunta })).toBeVisible();

    await page.goto("/");
    await page.getByPlaceholder("Digite sua pergunta...").fill(pergunta);
    await page.getByRole("button", { name: "Enviar" }).click();
    const botBubble = page.locator(".chat-bubble-bot").last();
    await expect(botBubble).toContainText("Resposta criada pelo teste E2E.", { timeout: 10_000 });

    await page.goto("/faq");
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("row", { name: new RegExp(pergunta) })
      .getByRole("button", { name: "Excluir" })
      .click();
    await expect(page.getByRole("cell", { name: pergunta })).toHaveCount(0);
  });

  test("métricas carregam sem erro e mostram os KPIs", async ({ page }) => {
    await page.goto("/metricas");
    await expect(page.getByText("Total de conversas")).toBeVisible();
    await expect(page.locator(".metrics-error")).toHaveCount(0);
  });

  test("logout limpa a sessão e bloqueia o acesso ao painel", async ({ page }) => {
    await page.goto("/faq");
    await page.getByRole("button", { name: "Sair" }).click();
    await expect(page).toHaveURL(/\/login/);

    await page.goto("/metricas");
    await expect(page).toHaveURL(/\/login/);
  });
});
