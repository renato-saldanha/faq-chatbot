"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import type { ChatAskResponse } from "@/types/api";

interface Message {
  role: "user" | "bot";
  text: string;
  semResposta?: boolean;
  erro?: string;
}

const ERRO_RATE_LIMIT = "Muitas perguntas em pouco tempo. Aguarde um instante antes de tentar de novo.";
const ERRO_GENERICO = "Não foi possível enviar. Toque em Enviar para tentar de novo.";

const SUGESTOES = [
  "Como recupero minha senha?",
  "Quais formas de pagamento são aceitas?",
  "Como falo com um atendente humano?",
];

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  const mutation = useMutation({
    mutationFn: (pergunta: string) => api.post<ChatAskResponse>("/api/chat/ask", { pergunta }),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: data.resposta, semResposta: data.sem_resposta },
      ]);
    },
    onError: (error) => {
      const mensagemErro =
        error instanceof ApiError && error.status === 429 ? ERRO_RATE_LIMIT : ERRO_GENERICO;
      setMessages((prev) => {
        const next = [...prev];
        const lastUserIndex = next.map((m) => m.role).lastIndexOf("user");
        if (lastUserIndex !== -1) {
          next[lastUserIndex] = { ...next[lastUserIndex], erro: mensagemErro };
        }
        return next;
      });
      toast.error(mensagemErro);
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const pergunta = input.trim();
    if (!pergunta) return;
    setMessages((prev) => [...prev, { role: "user", text: pergunta }]);
    setInput("");
    mutation.mutate(pergunta);
  }

  function handleSuggestionClick(pergunta: string) {
    setMessages((prev) => [...prev, { role: "user", text: pergunta }]);
    mutation.mutate(pergunta);
  }

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Faça uma pergunta para começar. Alguns exemplos:</p>
            <div className="chat-suggestions">
              {SUGESTOES.map((sugestao) => (
                <button
                  key={sugestao}
                  type="button"
                  className="chat-suggestion-chip"
                  onClick={() => handleSuggestionClick(sugestao)}
                >
                  {sugestao}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-bubble-${m.role}`}>
            {m.semResposta && <span className="chat-badge">Sem resposta encontrada</span>}
            <p>{m.text}</p>
            {m.erro && <span className="chat-bubble-error">{m.erro}</span>}
          </div>
        ))}
        {mutation.isPending && <div className="chat-bubble chat-bubble-bot chat-typing">Digitando...</div>}
      </div>
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Digite sua pergunta..."
          aria-label="Digite sua pergunta"
          className="chat-input"
          disabled={mutation.isPending}
        />
        <button type="submit" className="chat-send" disabled={mutation.isPending || !input.trim()}>
          Enviar
        </button>
      </form>
    </div>
  );
}
