# Database Schema

Aegis AI uses SQLAlchemy models and Alembic migrations. SQLite is the local default; PostgreSQL is used by Docker deployment.

## Tables

| Table | Purpose |
| --- | --- |
| `users` | Auth-ready user records |
| `conversations` | Chat sessions, summaries, pin/archive state |
| `messages` | Conversation messages, citations, edit metadata |
| `memories` | Short-term and long-term memory summaries |
| `user_preferences` | Key/value preference storage |
| `knowledge_collections` | Named RAG collections with tags |
| `documents` | Uploaded source files and metadata |
| `document_chunks` | Chunk text and vector embedding ids |
| `agent_runs` | Agent goals, plans, reflections, results |
| `tool_runs` | Tool execution audit records |
| `audit_logs` | Security and lifecycle events |

## Vector Store

ChromaDB stores embeddings by collection. SQL rows keep document metadata, chunk content, and embedding ids. Citations join vector hits back to source metadata.
