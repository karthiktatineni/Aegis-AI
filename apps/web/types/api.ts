export type Role = "user" | "assistant" | "system";

export type Citation = {
  document_id: string;
  chunk_id: string;
  filename: string;
  score: number;
  excerpt: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: Role;
  content: string;
  citations?: Citation[];
  created_at: string;
  updated_at: string;
};

export type Conversation = {
  id: string;
  title: string;
  summary?: string | null;
  pinned: boolean;
  archived: boolean;
  created_at: string;
  updated_at: string;
  messages: Message[];
};

export type Collection = {
  id: string;
  name: string;
  description?: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
  documents: Array<{
    id: string;
    filename: string;
    content_type?: string | null;
    checksum: string;
    tags: string[];
    created_at: string;
  }>;
};

export type ModelStatus = {
  provider: string;
  local_model_id: string;
  embedding_model: string;
  device: string;
  supported: string[];
};
