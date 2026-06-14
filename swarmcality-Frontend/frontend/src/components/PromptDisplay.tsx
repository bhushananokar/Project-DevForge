"use client";

import { useState } from "react";
import type { GeneratedPrompt } from "@/types";

const COMPLEXITY_COLORS: Record<string, string> = {
  low:    "text-green-400 bg-green-400/10 border-green-400/20",
  medium: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  high:   "text-red-400   bg-red-400/10   border-red-400/20",
};

interface Props {
  prompt: GeneratedPrompt;
}

export default function PromptDisplay({ prompt }: Props) {
  const [copied, setCopied] = useState(false);
  const [view, setView] = useState<"rendered" | "raw">("rendered");

  async function copyToClipboard() {
    await navigator.clipboard.writeText(prompt.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const complexityClass = COMPLEXITY_COLORS[prompt.estimated_complexity] ?? COMPLEXITY_COLORS.medium;
  const date = new Date(prompt.created_at).toLocaleString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });

  return (
    <div className="flex flex-col gap-3 animate-fade-in">
      {/* Meta bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${complexityClass}`}>
          {prompt.estimated_complexity} complexity
        </span>
        <span className="text-xs text-secondary">Target: {prompt.target_agent}</span>
        <span className="text-xs text-secondary">{date}</span>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex rounded-lg border border-border overflow-hidden text-xs">
            <button
              onClick={() => setView("rendered")}
              className={`px-3 py-1.5 transition-colors ${view === "rendered" ? "bg-elevated text-primary" : "text-secondary hover:text-primary"}`}
            >
              Preview
            </button>
            <button
              onClick={() => setView("raw")}
              className={`px-3 py-1.5 transition-colors ${view === "raw" ? "bg-elevated text-primary" : "text-secondary hover:text-primary"}`}
            >
              Raw
            </button>
          </div>
          <button
            onClick={copyToClipboard}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors font-medium ${
              copied
                ? "bg-success/10 border-success/30 text-success"
                : "border-border hover:border-border-light text-secondary hover:text-primary"
            }`}
          >
            {copied ? "✓ Copied!" : "Copy"}
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-accent/5 border border-accent/20 rounded-xl px-4 py-3">
        <p className="text-xs text-secondary font-medium mb-1 uppercase tracking-wide">Summary</p>
        <p className="text-sm text-primary leading-relaxed">{prompt.summary}</p>
      </div>

      {/* Content */}
      <div className="bg-elevated border border-border rounded-xl overflow-hidden">
        {view === "raw" ? (
          <pre className="text-xs font-mono text-secondary leading-relaxed p-5 overflow-x-auto whitespace-pre-wrap break-words">
            {prompt.prompt}
          </pre>
        ) : (
          <div
            className="prompt-prose text-sm text-primary p-5 max-h-[60vh] overflow-y-auto"
            dangerouslySetInnerHTML={{ __html: markdownToHtml(prompt.prompt) }}
          />
        )}
      </div>

      {/* Sources used */}
      {prompt.input_sources.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-secondary font-medium">Sources used:</span>
          {prompt.input_sources.map((src, i) => (
            <span key={i} className="text-xs bg-card border border-border rounded-full px-2.5 py-0.5 text-secondary truncate max-w-[20ch]" title={src}>
              {src}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function markdownToHtml(md: string): string {
  return md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^[-*] (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
    .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
    .replace(/^---$/gm, "<hr>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(?!<[hul]|<\/[hul]|<hr|<li)(.+)/gm, "<p>$1</p>")
    .replace(/<p><\/p>/g, "");
}
