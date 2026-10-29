"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { OtpRequestResponse } from "@/types/api";
import { VerifyForm } from "@/components/domain/verify-form";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [step, setStep] = useState<"email" | "otp">("email");
  const [codigoDemo, setCodigoDemo] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => api.post<OtpRequestResponse | undefined>("/api/auth/otp/request", { email }),
    onSuccess: (data) => {
      setCodigoDemo(data?.codigo_demo ?? null);
      setStep("otp");
      toast.success("Se o e-mail estiver correto, um código foi enviado.");
    },
    onError: () => toast.error("Erro ao solicitar código. Tente novamente."),
  });

  if (step === "otp") {
    return <VerifyForm email={email} codigoDemo={codigoDemo} />;
  }

  return (
    <form
      className="auth-form"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
    >
      <label htmlFor="email">E-mail</label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        placeholder="seu@email.com"
      />
      <button type="submit" disabled={mutation.isPending}>
        Enviar código
      </button>
    </form>
  );
}
