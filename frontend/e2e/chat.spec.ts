import { expect, test } from "@playwright/test";

test.describe("Chat público", () => {
  test("pergunta cadastrada retorna resposta da base de conhecimento", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "Quais formas de pagamento são aceitas?" }).click();

    const botBubble = page.locator(".chat-bubble-bot").last();
    await expect(botBubble).toContainText("cartão de crédito", { timeout: 10_000 });
    await expect(botBubble.locator(".chat-badge")).toHaveCount(0);
  });

  test("pergunta fora da base retorna sem_resposta", async ({ page }) => {
    await page.goto("/");

    await page.getByPlaceholder("Digite sua pergunta...").fill("Qual a velocidade de rotação de Júpiter?");
    await page.getByRole("button", { name: "Enviar" }).click();

    const botBubble = page.locator(".chat-bubble-bot").last();
    await expect(botBubble.locator(".chat-badge")).toContainText("Sem resposta encontrada", {
      timeout: 10_000,
    });
  });
});
