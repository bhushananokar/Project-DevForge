"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { Notebook } from "@/types";
import Navbar from "@/components/Navbar";
import Link from "next/link";

const TYPE_ICONS: Record<string, string> = { audio: "🎙️", image: "🖼️", youtube: "▶️", transcript: "📄", text: "💬" };

function NotebookCard({ nb, onDelete }: { nb: Notebook; onDelete: (id: string) => void }) {
  const [deleting, setDeleting] = useState(false);

  async function handleDelete(e: React.MouseEvent) {
    e.preventDefault();
    if (!confirm(`Delete "${nb.name}"? This is permanent.`)) return;
    setDeleting(true);
    try { await api.notebooks.delete(nb.id); onDelete(nb.id); } catch { setDeleting(false); }
  }

  const updated = new Date(nb.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric" });

  return (
    <Link
      href={`/notebook/${nb.id}`}
      className="group bg-card border border-border hover:border-accent/50 rounded-xl p-5 flex flex-col gap-3 transition-all hover:shadow-lg hover:shadow-accent/5 relative"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="w-9 h-9 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-base">
          📓
        </div>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="opacity-0 group-hover:opacity-100 text-secondary hover:text-danger transition-all p-1 rounded-lg hover:bg-danger/10 text-xs"
          title="Delete notebook"
        >
          {deleting ? "…" : "✕"}
        </button>
      </div>

      <div>
        <h3 className="font-semibold text-sm text-primary line-clamp-1">{nb.name}</h3>
        {nb.description && (
          <p className="text-xs text-secondary mt-1 line-clamp-2 leading-relaxed">{nb.description}</p>
        )}
      </div>

      <div className="flex items-center justify-between mt-auto pt-2 border-t border-border">
        <span className="text-xs text-secondary">
          {nb.source_count} source{nb.source_count !== 1 ? "s" : ""}
        </span>
        <span className="text-xs text-secondary">{updated}</span>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  useEffect(() => {
    if (!authLoading && !user) router.replace("/login");
  }, [authLoading, user, router]);

  const load = useCallback(async () => {
    try {
      const data = await api.notebooks.list();
      setNotebooks(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { if (user) load(); }, [user, load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const nb = await api.notebooks.create(newName.trim(), newDesc.trim());
      router.push(`/notebook/${nb.id}`);
    } catch {
      setCreating(false);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-base flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Your Notebooks</h1>
            <p className="text-secondary text-sm mt-1">
              {notebooks.length === 0 ? "Create your first notebook to get started." : `${notebooks.length} notebook${notebooks.length !== 1 ? "s" : ""}`}
            </p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover rounded-lg text-sm font-semibold transition-colors"
          >
            <span className="text-base">+</span> New notebook
          </button>
        </div>

        {notebooks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 gap-4 text-center">
            <span className="text-5xl">📓</span>
            <h2 className="font-semibold text-lg">No notebooks yet</h2>
            <p className="text-secondary text-sm max-w-sm">
              Create a notebook, add your audio recordings, notes, and videos, then generate a
              perfect coding agent prompt.
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="mt-2 px-5 py-2.5 bg-accent hover:bg-accent-hover rounded-lg text-sm font-semibold transition-colors"
            >
              Create notebook
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {notebooks.map((nb) => (
              <NotebookCard
                key={nb.id}
                nb={nb}
                onDelete={(id) => setNotebooks((prev) => prev.filter((n) => n.id !== id))}
              />
            ))}
          </div>
        )}
      </main>

      {/* Create modal */}
      {showCreate && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={(e) => e.target === e.currentTarget && setShowCreate(false)}
        >
          <div className="bg-card border border-border rounded-2xl w-full max-w-md p-6 animate-slide-up">
            <h2 className="font-semibold mb-5">New notebook</h2>
            <form onSubmit={handleCreate} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-secondary font-medium">Name</label>
                <input
                  autoFocus
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="My feature spec"
                  className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-secondary font-medium">Description (optional)</label>
                <input
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="What is this notebook about?"
                  className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors"
                />
              </div>
              <div className="flex gap-3 mt-1">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 py-2.5 border border-border hover:border-border-light rounded-lg text-sm text-secondary hover:text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors"
                >
                  {creating ? "Creating…" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
