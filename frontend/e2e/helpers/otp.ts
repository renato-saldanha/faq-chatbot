import { execSync } from "node:child_process";

const OTP_LOG_PATTERN = /OTP para ([^:]+): (\d{6})/;

/** Lê o código OTP mais recente do log do container backend (sem SMTP configurado, o AuthService loga o código — ver app/services/auth_service.py). */
export function readLatestOtpFromLogs(email: string): string {
  const output = execSync("docker compose logs backend --no-color --tail 200", {
    cwd: "..",
    encoding: "utf-8",
  });

  const matches = [...output.matchAll(new RegExp(OTP_LOG_PATTERN, "g"))].filter(
    (m) => m[1].trim().toLowerCase() === email.trim().toLowerCase(),
  );

  if (matches.length === 0) {
    throw new Error(`Nenhum código OTP encontrado no log do backend para ${email}`);
  }

  return matches[matches.length - 1][2];
}
