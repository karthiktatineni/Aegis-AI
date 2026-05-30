# Folder Structure

```text
.
|-- apps
|   |-- api
|   |   |-- app
|   |   |   |-- api/v1/routes      # REST and streaming endpoints
|   |   |   |-- core               # settings and auth-ready dependencies
|   |   |   |-- db                 # async engine and repositories
|   |   |   |-- models             # SQLAlchemy schema
|   |   |   |-- schemas            # Pydantic contracts
|   |   |   |-- services           # AI, RAG, memory, agents, tools
|   |   |   `-- utils
|   |   |-- alembic               # migrations
|   |   `-- tests                 # unit and integration tests
|   `-- web
|       |-- app                   # Next.js App Router pages
|       |-- components            # layout, chat, knowledge, UI primitives
|       |-- lib                   # API client and utilities
|       `-- types                 # shared frontend DTOs
|-- docs
|-- infra
|-- scripts
|-- docker-compose.yml
`-- README.md
```
