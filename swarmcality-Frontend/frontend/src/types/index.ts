export interface User {
  id: string;
  email: string;
  name: string;
}

export interface Notebook {
  id: string;
  name: string;
  description: string;
  source_count: number;
  created_at: string;
  updated_at: string;
}

export type SourceType = "audio" | "image" | "youtube" | "transcript" | "text" | "pdf";

export interface Source {
  id: string;
  type: SourceType;
  source_label: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface GeneratedPrompt {
  id: string;
  prompt: string;
  summary: string;
  estimated_complexity: "low" | "medium" | "high";
  input_sources: string[];
  target_agent: string;
  created_at: string;
}

export interface NotebookDetail extends Notebook {
  sources: Source[];
  latest_prompt: GeneratedPrompt | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
