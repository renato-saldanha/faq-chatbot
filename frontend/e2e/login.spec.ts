import { expect, test } from "@playwright/test";
import { readLatestOtpFromLogs } from "./helpers/otp";

const ADMIN_EMAIL = process.env.ADMIN_EMAIL ?? "admin@example.com";

test.use({ storageState: { cookies: [], origins: [] } });

test("dashboard redireciona para /login quando não autenticado", async ({ page }) => {
  await page.goto("/metricas");
  await expect(page).toHaveURL(/\/login/);
});

test("código errado é rejeitado e não autentica", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(ADMIN_EMAIL);
  await page.getByRole("button", { name: "Enviar código" }).click();
  await expect(page.getByLabel("Código de 6 dígitos")).toBeVisible();

  // Gera e descarta o código real para não interferir num código "óbvio" coincidir;
  // testa com um valor certamente errado.
  readLatestOtpFromLogs(ADMIN_EMAIL);
  await page.getByLabel("Código de 6 dígitos").fill("000000");
  await page.getByRole("button", { name: "Verificar" }).click();

  await expect(page.getByText("Código inválido ou expirado.")).toBeVisible();
  await expect(page).toHaveURL(/\/login/);
});
