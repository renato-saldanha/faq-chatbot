"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  async function handleLogout() {
    await api.post("/api/auth/logout");
    setAuthenticated(false);
    router.push("/login");
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="dashboard-layout">
      <nav className="dashboard-nav">
        <span className="dashboard-brand">Admin</span>
        <div className="dashboard-links">
          <Link href="/metricas">Métricas</Link>
          <Link href="/faq">FAQ</Link>
          <button onClick={handleLogout} className="dashboard-logout">
            Sair
          </button>
        </div>
      </nav>
      <main className="page-container">{children}</main>
    </div>
  );
}
