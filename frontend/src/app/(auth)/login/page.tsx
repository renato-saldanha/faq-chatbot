import { LoginForm } from "@/components/domain/login-form";

const DEMO_EMAIL = "admin@demo.test";

export default function LoginPage() {
  return (
    <main className="page-container auth-page">
      <h1>Painel Admin</h1>
      <p className="page-subtitle">Entre com seu e-mail para receber um código de acesso.</p>
      {process.env.NEXT_PUBLIC_DEMO === "1" && (
        <p className="demo-code">Modo demonstração: use o e-mail {DEMO_EMAIL}</p>
      )}
      <LoginForm />
    </main>
  );
}
