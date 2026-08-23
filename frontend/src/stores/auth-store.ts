import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  isAuthenticated: boolean;
  hasHydrated: boolean;
  setAuthenticated: (v: boolean) => void;
  setHasHydrated: (v: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      hasHydrated: false,
      setAuthenticated: (v: boolean) => set({ isAuthenticated: v }),
      setHasHydrated: (v: boolean) => set({ hasHydrated: v }),
    }),
    {
      name: "auth-store",
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
      partialize: (state) => ({ isAuthenticated: state.isAuthenticated }),
    }
  )
);
