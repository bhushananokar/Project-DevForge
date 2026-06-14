"use client";

import { useState, useRef } from "react";
import { api } from "@/lib/api";
import type { Source } from "@/types";

type Tab = "youtube" | "audio" | "image" | "pdf" | "transcript" | "text";

interface Props {
  notebookId: string;
  onAdded: (source: Source) => void;
  onClose: () => void;
}

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "youtube", label: "YouTube", icon: "▶️" },
  { id: "audio", label: "Audio", icon: "🎙️" },
  { id: "image", label: "Image / Note", icon: "🖼️" },
  { id: "pdf", label: "PDF", icon: "📑" },
  { id: "transcript", label: "Transcript", icon: "📄" },
  { id: "text", label: "Text", icon: "💬" },
];

export default function AddSourceModal({ notebookId, onAdded, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("youtube");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // YouTube
  const [ytUrl, setYtUrl] = useState("");

  // Transcript / Text
  const [textContent, setTextContent] = useState("");
  const [textLabel, setTextLabel] = useState("");

  // File upload
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  function reset() {
    setError(""); setYtUrl(""); setTextContent(""); setTextLabel(""); setSelectedFile(null);
  }

  function handleTabChange(t: Tab) { setTab(t); reset(); }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      let source: Source;
      if (tab === "youtube") {
        source = await api.sources.addYoutube(notebookId, ytUrl.trim());
      } else if (tab === "audio") {
        if (!selectedFile) throw new Error("Select an audio file.");
        source = await api.sources.addAudio(notebookId, selectedFile);
      } else if (tab === "image") {
        if (!selectedFile) throw new Error("Select an image file.");
        source = await api.sources.addImage(notebookId, selectedFile);
      } else if (tab === "pdf") {
        if (!selectedFile) throw new Error("Select a PDF file.");
        source = await api.sources.addPdf(notebookId, selectedFile);
      } else if (tab === "transcript") {
        if (!textContent.trim()) throw new Error("Transcript cannot be empty.");
        source = await api.sources.addTranscript(notebookId, textContent, textLabel || undefined);
      } else {
        if (!textContent.trim()) throw new Error("Text cannot be empty.");
        source = await api.sources.addText(notebookId, textContent, textLabel || undefined);
      }
      onAdded(source);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center z-50 p-0 sm:p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-card border border-border rounded-t-2xl sm:rounded-2xl w-full sm:max-w-lg animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-border">
          <h2 className="font-semibold text-sm">Add source</h2>
          <button onClick={onClose} className="text-secondary hover:text-primary w-7 h-7 flex items-center justify-center rounded-lg hover:bg-elevated transition-colors">
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-5 pt-4 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => handleTabChange(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                tab === t.id
                  ? "bg-accent/20 text-accent border border-accent/30"
                  : "text-secondary hover:text-primary hover:bg-elevated"
              }`}
            >
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="px-5 pt-4 pb-5 flex flex-col gap-4">
          {error && (
            <div className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          {/* YouTube */}
          {tab === "youtube" && (
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-secondary font-medium">YouTube URL</label>
              <input
                autoFocus
                required
                value={ytUrl}
                onChange={(e) => setYtUrl(e.target.value)}
                placeholder="https://youtu.be/..."
                className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors"
              />
              <p className="text-xs text-secondary">Works with auto-generated and manual captions.</p>
            </div>
          )}

          {/* Audio / Image / PDF file upload */}
          {(tab === "audio" || tab === "image" || tab === "pdf") && (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault(); setDragOver(false);
                const f = e.dataTransfer.files[0];
                if (f) setSelectedFile(f);
              }}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                dragOver ? "border-accent bg-accent/5" : selectedFile ? "border-success/50 bg-success/5" : "border-border hover:border-border-light"
              }`}
            >
              <input
                ref={fileRef}
                type="file"
                className="hidden"
                accept={
                  tab === "audio" ? "audio/*,video/mp4,video/webm"
                  : tab === "pdf" ? "application/pdf"
                  : "image/*"
                }
                onChange={(e) => e.target.files?.[0] && setSelectedFile(e.target.files[0])}
              />
              {selectedFile ? (
                <div className="flex flex-col items-center gap-1">
                  <span className="text-2xl">
                    {tab === "audio" ? "🎙️" : tab === "pdf" ? "📑" : "🖼️"}
                  </span>
                  <p className="text-sm font-medium text-primary">{selectedFile.name}</p>
                  <p className="text-xs text-secondary">{(selectedFile.size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2 text-secondary">
                  <span className="text-3xl">
                    {tab === "audio" ? "🎙️" : tab === "pdf" ? "📑" : "🖼️"}
                  </span>
                  <p className="text-sm">
                    Drop {tab === "audio" ? "audio/video" : tab === "pdf" ? "PDF" : "image"} here or click to browse
                  </p>
                  <p className="text-xs">
                    {tab === "audio" ? "mp3, wav, m4a, mp4, webm — max 25 MB"
                     : tab === "pdf" ? "PDF with text layer — max 50 MB"
                     : "jpg, png, gif, webp — max 20 MB"}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Transcript / Text */}
          {(tab === "transcript" || tab === "text") && (
            <>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-secondary font-medium">
                  Label <span className="text-secondary/60">(optional)</span>
                </label>
                <input
                  value={textLabel}
                  onChange={(e) => setTextLabel(e.target.value)}
                  placeholder={tab === "transcript" ? "weekly-standup" : "background-context"}
                  className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-secondary font-medium">
                  {tab === "transcript" ? "Transcript" : "Text content"}
                </label>
                <textarea
                  autoFocus
                  required
                  rows={8}
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder={
                    tab === "transcript"
                      ? "Paste your meeting transcript here…"
                      : "Paste any relevant context, requirements, or notes…"
                  }
                  className="bg-elevated border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-accent transition-colors resize-none font-mono text-xs leading-relaxed"
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-accent hover:bg-accent-hover disabled:opacity-50 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Processing…
              </>
            ) : (
              "Add source"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
