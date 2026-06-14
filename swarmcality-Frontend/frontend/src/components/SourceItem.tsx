"use client";

import type { Source } from "@/types";

const TYPE_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  audio:      { icon: "🎙️", color: "text-purple-400",  bg: "bg-purple-400/10" },
  image:      { icon: "🖼️", color: "text-blue-400",    bg: "bg-blue-400/10"   },
  youtube:    { icon: "▶️",  color: "text-red-400",     bg: "bg-red-400/10"    },
  transcript: { icon: "📄", color: "text-amber-400",   bg: "bg-amber-400/10"  },
  text:       { icon: "💬", color: "text-green-400",   bg: "bg-green-400/10"  },
  pdf:        { icon: "📑", color: "text-orange-400",  bg: "bg-orange-400/10" },
};

interface Props {
  source: Source;
  onDelete: (id: string) => void;
  deleting: boolean;
}

export default function SourceItem({ source, onDelete, deleting }: Props) {
  const cfg = TYPE_CONFIG[source.type] ?? TYPE_CONFIG.text;

  const timeAgo = (() => {
    const diff = Date.now() - new Date(source.created_at).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  })();

  return (
    <div className="group flex items-start gap-3 px-3 py-2.5 rounded-lg hover:bg-elevated transition-colors">
      <div className={`w-7 h-7 rounded-lg ${cfg.bg} flex items-center justify-center text-sm shrink-0 mt-0.5`}>
        {cfg.icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-primary truncate">{source.source_label}</p>
        <p className="text-xs text-secondary mt-0.5">{timeAgo}</p>
      </div>
      <button
        onClick={() => onDelete(source.id)}
        disabled={deleting}
        className="opacity-0 group-hover:opacity-100 text-secondary hover:text-danger p-1 rounded-md hover:bg-danger/10 transition-all text-xs shrink-0 mt-0.5"
        title="Remove source"
      >
        {deleting ? "…" : "✕"}
      </button>
    </div>
  );
}
