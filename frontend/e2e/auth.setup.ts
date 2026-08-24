import { expect, test as setup } from "@playwright/test";
import { readLatestOtpFromLogs } from "./helpers/otp";
import { STORAGE_STATE } from "./helpers/storage-state";

const ADMIN_EMAIL = process.env.ADMIN_EMAIL ?? "admin@example.com";

setup("autentica como admin e salva a sessão", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(ADMIN_EMAIL);
  await page.getByRole("button", { name: "Enviar código" }).click();
  await expect(page.getByLabel("Código de 6 dígitos")).toBeVisible();

  const codigo = readLatestOtpFromLogs(ADMIN_EMAIL);
  await page.getByLabel("Código de 6 dígitos").fill(codigo);
  await page.getByRole("button", { name: "Verificar" }).click();

  await expect(page).toHaveURL(/\/faq/);
  await page.context().storageState({ path: STORAGE_STATE });
});
