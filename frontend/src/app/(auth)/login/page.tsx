import { LoginForm } from "@/components/domain/login-form";

export default function LoginPage() {
  return (
    <main className="page-container auth-page">
      <h1>Painel Admin</h1>
      <p className="page-subtitle">Entre com seu e-mail para receber um código de acesso.</p>
      <LoginForm />
    </main>
  );
}
