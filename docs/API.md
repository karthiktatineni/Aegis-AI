# API Documentation

FastAPI serves OpenAPI at `/api/v1/openapi.json`, Swagger at `/api/v1/docs`, and ReDoc at `/api/v1/redoc`.

## Core Endpoints

| Area | Method | Path | Purpose |
| --- | --- | --- | --- |
| Health | GET | `/api/v1/health` | Runtime and capability status |
| Chat | GET | `/api/v1/chat/conversations` | List/search conversations |
| Chat | POST | `/api/v1/chat/conversations` | Create a conversation |
| Chat | POST | `/api/v1/chat/conversations/{id}/stream` | Server-sent streaming response |
| Chat | PATCH | `/api/v1/chat/messages/{id}` | Edit a message |
| Memory | GET | `/api/v1/memory` | List memories |
| Memory | POST | `/api/v1/memory` | Create memory |
| Memory | PUT | `/api/v1/memory/preferences` | Upsert a user preference |
| Knowledge | POST | `/api/v1/knowledge/collections` | Create collection |
| Knowledge | POST | `/api/v1/knowledge/collections/{id}/upload` | Ingest PDF, DOCX, Markdown, TXT, CSV, HTML |
| Knowledge | POST | `/api/v1/knowledge/search` | Semantic search with citations |
| Agents | POST | `/api/v1/agents/run` | Plan and execute an agent run |
| Tools | GET | `/api/v1/tools` | Discover tool contracts |
| Models | GET | `/api/v1/models` | Model runtime status |

## Streaming Format

`POST /api/v1/chat/conversations/{id}/stream` returns `text/event-stream`.

```text
event: citations
data: {"citations": [...]}

event: token
data: {"text": "partial text"}

event: done
data: {"message_id": "...", "conversation_id": "..."}
```
