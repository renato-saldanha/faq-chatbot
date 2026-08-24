import { expect, test } from "@playwright/test";

// Nome prefixado com "zz-" para rodar por último: estoura de propósito o rate limit
// de 10/min do chat (app/rate_limit.py) — qualquer teste que rode depois no mesmo
// worker herdaria o IP já bloqueado.
test("estourar o rate limit do chat mostra erro específico de 429 na bolha da pergunta", async ({ page }) => {
  await page.goto("/");

  const input = page.getByPlaceholder("Digite sua pergunta...");
  const enviar = page.getByRole("button", { name: "Enviar" });

  for (let i = 0; i < 11; i++) {
    await input.fill(`Pergunta de teste de rate limit número ${i}`);
    await enviar.click();
    await page.waitForTimeout(150);
  }

  const lastUserBubble = page.locator(".chat-bubble-user").last();
  await expect(lastUserBubble.locator(".chat-bubble-error")).toContainText("Aguarde um instante", {
    timeout: 10_000,
  });
});
