"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { User } from "@/types";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>({
  user: null,
  loading: true,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("pf_token");
    if (!token) { setLoading(false); return; }
    api.auth.me()
      .then(setUser)
      .catch(() => localStorage.removeItem("pf_token"))
      .finally(() => setLoading(false));
  }, []);

  function login(token: string, userData: User) {
    localStorage.setItem("pf_token", token);
    setUser(userData);
  }

  function logout() {
    localStorage.removeItem("pf_token");
    setUser(null);
    router.push("/");
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
