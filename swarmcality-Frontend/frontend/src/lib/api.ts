const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("pf_token");
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  isFormData = false
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};

  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isFormData) headers["Content-Type"] = "application/json";

  // Merge caller headers last so they can override
  const mergedHeaders = { ...headers, ...(init.headers as Record<string, string> ?? {}) };

  const res = await fetch(`${BASE}${path}`, { ...init, headers: mergedHeaders });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ────────────────────────────────────────────────────────────────────

export const api = {
  auth: {
    register: (email: string, name: string, password: string) =>
      request<import("@/types").AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, name, password }),
      }),
    login: (email: string, password: string) =>
      request<import("@/types").AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    me: () => request<import("@/types").User>("/auth/me"),
  },

  // ── Notebooks ─────────────────────────────────────────────────────────────
  notebooks: {
    list: () => request<import("@/types").Notebook[]>("/notebooks"),
    create: (name: string, description = "") =>
      request<import("@/types").Notebook>("/notebooks", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      }),
    get: (id: string) =>
      request<import("@/types").NotebookDetail>(`/notebooks/${id}`),
    update: (id: string, data: { name?: string; description?: string }) =>
      request<import("@/types").Notebook>(`/notebooks/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/notebooks/${id}`, { method: "DELETE" }),
  },

  // ── Sources ───────────────────────────────────────────────────────────────
  sources: {
    list: (notebookId: string) =>
      request<import("@/types").Source[]>(`/notebooks/${notebookId}/sources`),

    addAudio: (notebookId: string, file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return request<import("@/types").Source>(
        `/notebooks/${notebookId}/sources/audio`,
        { method: "POST", body: fd },
        true
      );
    },
    addImage: (notebookId: string, file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return request<import("@/types").Source>(
        `/notebooks/${notebookId}/sources/image`,
        { method: "POST", body: fd },
        true
      );
    },
    addYoutube: (notebookId: string, url: string) =>
      request<import("@/types").Source>(`/notebooks/${notebookId}/sources/youtube`, {
        method: "POST",
        body: JSON.stringify({ url }),
      }),
    addTranscript: (notebookId: string, text: string, label?: string) =>
      request<import("@/types").Source>(`/notebooks/${notebookId}/sources/transcript`, {
        method: "POST",
        body: JSON.stringify({ text, label }),
      }),
    addText: (notebookId: string, text: string, label?: string) =>
      request<import("@/types").Source>(`/notebooks/${notebookId}/sources/text`, {
        method: "POST",
        body: JSON.stringify({ text, label }),
      }),
    addPdf: (notebookId: string, file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return request<import("@/types").Source>(
        `/notebooks/${notebookId}/sources/pdf`,
        { method: "POST", body: fd },
        true
      );
    },
    delete: (notebookId: string, sourceId: string) =>
      request<void>(`/notebooks/${notebookId}/sources/${sourceId}`, {
        method: "DELETE",
      }),
  },

  // ── Prompts ───────────────────────────────────────────────────────────────
  prompts: {
    list: (notebookId: string) =>
      request<import("@/types").GeneratedPrompt[]>(`/notebooks/${notebookId}/prompts`),
    get: (notebookId: string, promptId: string) =>
      request<import("@/types").GeneratedPrompt>(
        `/notebooks/${notebookId}/prompts/${promptId}`
      ),
    generate: (notebookId: string, targetAgent = "Claude Code", basePrompt?: string, additionalContext?: string) =>
      request<import("@/types").GeneratedPrompt>(
        `/notebooks/${notebookId}/prompts/generate`,
        {
          method: "POST",
          body: JSON.stringify({
            target_agent: targetAgent,
            base_prompt: basePrompt || undefined,
            additional_context: additionalContext || undefined,
          }),
        }
      ),
  },
};
