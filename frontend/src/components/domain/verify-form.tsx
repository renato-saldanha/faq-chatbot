"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

interface VerifyFormProps {
  email: string;
}

export function VerifyForm({ email }: VerifyFormProps) {
  const [codigo, setCodigo] = useState("");
  const router = useRouter();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);

  const mutation = useMutation({
    mutationFn: () => api.post<{ authenticated: boolean }>("/api/auth/otp/verify", { email, codigo }),
    onSuccess: (data) => {
      if (data.authenticated) {
        setAuthenticated(true);
        router.push("/faq");
      }
    },
    onError: () => toast.error("Código inválido ou expirado."),
  });

  return (
    <form
      className="auth-form"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
    >
      <label htmlFor="codigo">Código de 6 dígitos</label>
      <input
        id="codigo"
        type="text"
        inputMode="numeric"
        maxLength={6}
        value={codigo}
        onChange={(e) => setCodigo(e.target.value)}
        required
      />
      <button type="submit" disabled={mutation.isPending}>
        Verificar
      </button>
    </form>
  );
}
