# Architecture

Aegis AI is split into two deployable apps.

## Frontend

The Next.js app is a SaaS-style workspace with chat, knowledge, and settings surfaces. The chat client consumes server-sent events, renders Markdown with code highlighting, and updates messages optimistically.

## Backend

FastAPI exposes versioned REST endpoints under `/api/v1`. The service layer owns model calls, memory retrieval, RAG ingestion, agent planning, and tool execution. Repositories isolate SQLAlchemy access from route handlers.

## AI Flow

```mermaid
flowchart LR
    U["User message"] --> C["Conversation history"]
    U --> M["Memory retrieval"]
    U --> R["RAG retrieval"]
    C --> P["Prompt assembly"]
    M --> P
    R --> P
    P --> L["Local LLM provider"]
    L --> S["SSE stream"]
    S --> UI["Next.js chat"]
```

## RAG Flow

```mermaid
flowchart LR
    F["Upload"] --> P["Parser"]
    P --> CH["Chunker"]
    CH --> E["Embedding service"]
    E --> V["ChromaDB"]
    CH --> SQL["SQL metadata"]
    Q["Query"] --> E
    E --> V
    V --> RR["Re-ranker"]
    RR --> CIT["Citations"]
```
