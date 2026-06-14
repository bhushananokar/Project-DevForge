"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useState, useRef, useEffect } from "react";

interface NavbarProps {
  notebookName?: string;
}

export default function Navbar({ notebookName }: NavbarProps) {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setMenuOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const initials = user?.name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) ?? "?";

  return (
    <nav className="h-14 border-b border-border flex items-center px-4 gap-4 bg-elevated/50 backdrop-blur-sm sticky top-0 z-40">
      <Link href="/dashboard" className="text-base font-semibold tracking-tight shrink-0">
        <span className="text-accent">Dev</span>Forge
      </Link>

      {notebookName && (
        <>
          <span className="text-border-light">/</span>
          <span className="text-sm text-secondary truncate max-w-xs">{notebookName}</span>
        </>
      )}

      <div className="ml-auto relative" ref={ref}>
        <button
          onClick={() => setMenuOpen((o) => !o)}
          className="w-8 h-8 rounded-full bg-accent/20 border border-accent/30 text-accent text-xs font-bold flex items-center justify-center hover:bg-accent/30 transition-colors"
        >
          {initials}
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-10 w-48 bg-card border border-border rounded-xl shadow-xl animate-fade-in overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-secondary truncate">{user?.email}</p>
            </div>
            <Link
              href="/dashboard"
              onClick={() => setMenuOpen(false)}
              className="block px-4 py-2.5 text-sm text-secondary hover:text-primary hover:bg-elevated transition-colors"
            >
              My notebooks
            </Link>
            <button
              onClick={logout}
              className="w-full text-left px-4 py-2.5 text-sm text-danger hover:bg-danger/10 transition-colors"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
