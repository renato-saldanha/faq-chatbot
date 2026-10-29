import { DEMO_EMAIL, LoginForm } from "@/components/domain/login-form";

export default function LoginPage() {
  const demo = process.env.NEXT_PUBLIC_DEMO === "1";

  return (
    <main className="page-container auth-page">
      <h1>Painel Admin</h1>
      <p className="page-subtitle">
        {demo
          ? "Entre com o e-mail de demonstração e clique em Enviar código."
          : "Entre com seu e-mail para receber um código de acesso."}
      </p>
      {demo && (
        <p className="demo-code">
          Modo demonstração: nenhum e-mail é enviado. Use {DEMO_EMAIL}; o código aparece na tela seguinte.
        </p>
      )}
      <LoginForm />
    </main>
  );
}
