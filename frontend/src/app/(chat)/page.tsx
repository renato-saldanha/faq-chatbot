import Link from "next/link";
import { ChatWindow } from "@/components/domain/chat-window";

export default function ChatPage() {
  return (
    <main className="page-container">
      <h1>Chat de FAQ</h1>
      <p className="page-subtitle">Tire suas dúvidas mais frequentes com nosso assistente.</p>
      <ChatWindow />
      <p className="chat-admin-link">
        <Link href="/login">Área administrativa</Link>
      </p>
    </main>
  );
}
