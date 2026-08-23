"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { ChatAskResponse } from "@/types/api";

interface Message {
  role: "user" | "bot";
  text: string;
  semResposta?: boolean;
}

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
    onError: () => {
      toast.error("Erro ao enviar sua pergunta. Tente novamente.");
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

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="chat-empty">Faça uma pergunta para começar.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-bubble-${m.role}`}>
            {m.semResposta && <span className="chat-badge">Sem resposta encontrada</span>}
            <p>{m.text}</p>
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
