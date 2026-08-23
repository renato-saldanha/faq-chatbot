import Link from "next/link";
import { ChatWindow } from "@/components/domain/chat-window";

export default function ChatPage() {
  return (
    <main className="page-container">
      <div className="chat-page-header">
        <div>
          <h1>Chat de FAQ</h1>
          <p className="page-subtitle">Tire suas dúvidas mais frequentes com nosso assistente.</p>
        </div>
        <Link href="/login" className="chat-admin-button">
          Painel interno
        </Link>
      </div>
      <ChatWindow />
    </main>
  );
}
