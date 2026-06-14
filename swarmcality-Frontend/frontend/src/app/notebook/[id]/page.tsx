"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { NotebookDetail, Source, GeneratedPrompt } from "@/types";
import Navbar from "@/components/Navbar";
import SourceItem from "@/components/SourceItem";
import AddSourceModal from "@/components/AddSourceModal";
import PromptDisplay from "@/components/PromptDisplay";
import SwarmPanel from "@/components/SwarmPanel";

type Tab = "prompt" | "swarm";

export default function NotebookPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [notebook, setNotebook] = useState<NotebookDetail | null>(null);
  const [prompts, setPrompts] = useState<GeneratedPrompt[]>([]);
  const [activePrompt, setActivePrompt] = useState<GeneratedPrompt | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [basePrompt, setBasePrompt] = useState("");
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState("");
  const [targetAgent, setTargetAgent] = useState("Claude Code");
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("prompt");

  useEffect(() => {
    if (!authLoading && !user) router.replace("/login");
  }, [authLoading, user, router]);

  const load = useCallback(async () => {
    try {
      const [nb, ps] = await Promise.all([
        api.notebooks.get(id),
        api.prompts.list(id),
      ]);
      setNotebook(nb);
      setNameInput(nb.name);
      setPrompts(ps);
      setActivePrompt(ps[0] ?? null);
    } catch {
      router.replace("/dashboard");
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useEffect(() => { if (user) load(); }, [user, load]);

  async function handleGenerate() {
    if (!notebook || generating) return;
    setGenError("");
    setGenerating(true);
    try {
      const p = await api.prompts.generate(id, targetAgent, basePrompt || undefined);
      setPrompts((prev) => [p, ...prev]);
      setActivePrompt(p);
    } catch (err: unknown) {
      setGenError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleDeleteSource(sourceId: string) {
    setDeletingIds((s) => new Set(s).add(sourceId));
    try {
      await api.sources.delete(id, sourceId);
      setNotebook((nb) =>
        nb
          ? { ...nb, sources: nb.sources.filter((s) => s.id !== sourceId), source_count: nb.source_count - 1 }
          : nb
      );
    } finally {
      setDeletingIds((s) => { const n = new Set(s); n.delete(sourceId); return n; });
    }
  }

  function handleSourceAdded(source: Source) {
    setNotebook((nb) =>
      nb ? { ...nb, sources: [...nb.sources, source], source_count: nb.source_count + 1 } : nb
    );
  }

  async function handleRename() {
    if (!notebook || !nameInput.trim() || nameInput === notebook.name) {
      setEditingName(false); return;
    }
    try {
      const updated = await api.notebooks.update(id, { name: nameInput.trim() });
      setNotebook((nb) => nb ? { ...nb, name: updated.name } : nb);
    } finally {
      setEditingName(false);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!notebook) return null;

  return (
    <div className="min-h-screen bg-base flex flex-col">
      <Navbar notebookName={notebook.name} />

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left: Sources sidebar ───────────────────────────────────────── */}
        <aside className="w-72 shrink-0 border-r border-border flex flex-col bg-elevated/30 overflow-y-auto">
          {/* Notebook name */}
          <div className="px-4 pt-5 pb-4 border-b border-border">
            {editingName ? (
              <input
                autoFocus
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                onBlur={handleRename}
                onKeyDown={(e) => e.key === "Enter" && handleRename()}
                className="w-full bg-elevated border border-accent rounded-lg px-2 py-1 text-sm font-semibold outline-none"
              />
            ) : (
              <button
                onClick={() => setEditingName(true)}
                className="text-sm font-semibold text-left w-full hover:text-accent transition-colors"
                title="Click to rename"
              >
                {notebook.name}
              </button>
            )}
            {notebook.description && (
              <p className="text-xs text-secondary mt-1 leading-relaxed">{notebook.description}</p>
            )}
          </div>

          {/* Sources header */}
          <div className="flex items-center justify-between px-4 pt-4 pb-2">
            <span className="text-xs font-semibold text-secondary uppercase tracking-wide">
              Sources · {notebook.sources.length}
            </span>
          </div>

          {/* Source list */}
          <div className="flex-1 px-1 pb-2">
            {notebook.sources.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 gap-2 text-center px-4">
                <span className="text-3xl">📭</span>
                <p className="text-xs text-secondary">No sources yet. Add one below.</p>
              </div>
            ) : (
              notebook.sources.map((s) => (
                <SourceItem
                  key={s.id}
                  source={s}
                  onDelete={handleDeleteSource}
                  deleting={deletingIds.has(s.id)}
                />
              ))
            )}
          </div>

          {/* Add source button */}
          <div className="p-4 border-t border-border">
            <button
              onClick={() => setShowModal(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 border border-dashed border-border-light hover:border-accent text-secondary hover:text-accent rounded-lg text-xs font-medium transition-colors"
            >
              <span className="text-base">+</span> Add source
            </button>
          </div>
        </aside>

        {/* ── Main: tabbed area ────────────────────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="shrink-0 border-b border-border px-6 flex gap-1 pt-3 bg-elevated/20">
            <button
              onClick={() => setActiveTab("prompt")}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
                activeTab === "prompt"
                  ? "border-accent text-accent"
                  : "border-transparent text-secondary hover:text-primary"
              }`}
            >
              ✨ Prompt
            </button>
            <button
              onClick={() => setActiveTab("swarm")}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
                activeTab === "swarm"
                  ? "border-accent text-accent"
                  : "border-transparent text-secondary hover:text-primary"
              }`}
            >
              🚀 Swarm
            </button>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl w-full mx-auto px-6 py-8 flex flex-col gap-6">

              {/* ── PROMPT TAB ─────────────────────────────────────────────── */}
              {activeTab === "prompt" && (
                <>
                  {/* Generate section */}
                  <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div>
                        <h2 className="font-semibold text-base">Generate Prompt</h2>
                        <p className="text-secondary text-xs mt-1">
                          Synthesizes all {notebook.source_count} source
                          {notebook.source_count !== 1 ? "s" : ""} into one detailed prompt.
                        </p>
                      </div>

                      <div className="flex items-center gap-3 flex-wrap">
                        <div className="flex flex-col gap-1">
                          <label className="text-xs text-secondary font-medium">Target agent</label>
                          <select
                            value={targetAgent}
                            onChange={(e) => setTargetAgent(e.target.value)}
                            className="bg-elevated border border-border rounded-lg px-3 py-2 text-xs outline-none focus:border-accent transition-colors"
                          >
                            <option>Claude Code</option>
                            <option>Cursor</option>
                            <option>Devin</option>
                            <option>Copilot</option>
                            <option>Generic</option>
                          </select>
                        </div>

                        <button
                          onClick={handleGenerate}
                          disabled={generating || notebook.source_count === 0}
                          className="self-end flex items-center gap-2 px-5 py-2 bg-accent hover:bg-accent-hover disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-accent/20"
                        >
                          {generating ? (
                            <>
                              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                              Generating…
                            </>
                          ) : (
                            <>✨ Generate</>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Base prompt */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs text-secondary font-medium">
                        Base prompt{" "}
                        <span className="text-secondary/60">(optional)</span>
                      </label>
                      <textarea
                        rows={3}
                        value={basePrompt}
                        onChange={(e) => setBasePrompt(e.target.value)}
                        placeholder="e.g. Use Next.js 14 with App Router, Tailwind CSS, and Supabase. The design must be mobile-first…"
                        className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors resize-none text-secondary placeholder:text-secondary/40"
                      />
                    </div>

                    {notebook.source_count === 0 && (
                      <div className="text-xs text-secondary bg-elevated border border-border rounded-lg px-4 py-3">
                        Add at least one source before generating.
                      </div>
                    )}
                    {genError && (
                      <div className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-lg px-4 py-3">
                        {genError}
                      </div>
                    )}

                    {/* Launch swarm shortcut */}
                    {activePrompt && (
                      <div className="flex items-center gap-2 pt-1 border-t border-border">
                        <p className="text-xs text-secondary flex-1">
                          Prompt ready — launch the swarm to build from it.
                        </p>
                        <button
                          onClick={() => setActiveTab("swarm")}
                          className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-accent/10 hover:bg-accent/20 border border-accent/30 text-accent rounded-lg transition-colors font-medium"
                        >
                          🚀 Go to Swarm
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Prompt display */}
                  {activePrompt ? (
                    <div className="flex flex-col gap-4">
                      {prompts.length > 1 && (
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold text-sm">Latest prompt</h3>
                          <button
                            onClick={() => setShowHistory((h) => !h)}
                            className="text-xs text-secondary hover:text-primary transition-colors"
                          >
                            {showHistory ? "Hide history" : `Show history (${prompts.length - 1} older)`}
                          </button>
                        </div>
                      )}

                      <PromptDisplay prompt={activePrompt} />

                      {showHistory && prompts.length > 1 && (
                        <div className="flex flex-col gap-2 mt-2">
                          <h4 className="text-xs font-medium text-secondary uppercase tracking-wide">
                            History
                          </h4>
                          {prompts.slice(1).map((p) => (
                            <button
                              key={p.id}
                              onClick={() => setActivePrompt(p)}
                              className={`text-left px-4 py-3 rounded-xl border transition-colors text-xs ${
                                activePrompt.id === p.id
                                  ? "border-accent/50 bg-accent/5"
                                  : "border-border hover:border-border-light bg-card"
                              }`}
                            >
                              <p className="font-medium text-primary">{p.summary}</p>
                              <p className="text-secondary mt-0.5">
                                {new Date(p.created_at).toLocaleString()} · {p.estimated_complexity} complexity
                              </p>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
                      <span className="text-5xl">✨</span>
                      <h3 className="font-semibold text-lg">No prompts yet</h3>
                      <p className="text-secondary text-sm max-w-sm">
                        Add your sources and click Generate to synthesize a detailed prompt for
                        the swarm.
                      </p>
                    </div>
                  )}
                </>
              )}

              {/* ── SWARM TAB ──────────────────────────────────────────────── */}
              {activeTab === "swarm" && (
                <SwarmPanel notebookGoal={activePrompt?.prompt} />
              )}
            </div>
          </div>
        </main>
      </div>

      {showModal && (
        <AddSourceModal
          notebookId={id}
          onAdded={handleSourceAdded}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}
