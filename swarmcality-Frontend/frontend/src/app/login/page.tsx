"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.auth.login(email, password);
      login(res.access_token, res.user);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link href="/" className="text-xl font-semibold tracking-tight">
            <span className="text-accent">Dev</span>Forge
          </Link>
          <p className="text-secondary text-sm mt-2">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4">
          {error && (
            <div className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-secondary font-medium">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors placeholder:text-secondary/50"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-secondary font-medium">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors placeholder:text-secondary/50"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-1 bg-accent hover:bg-accent-hover disabled:opacity-50 rounded-lg py-2.5 text-sm font-semibold transition-colors"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-center text-xs text-secondary">
            No account?{" "}
            <Link href="/register" className="text-accent hover:underline">
              Create one
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
