# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillPilot is an AI Skill Orchestration Engine based on SeekDB, providing vector search, skill management, and multi-platform support (Coze, Dify, LangChain).

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"              # Development
pip install -e ".[test]"             # Testing
pip install -e ".[all]"              # All features (AI providers + platforms)
pip install -e ".[import-all]"       # All platform importers only

# Run tests
pytest                                    # All tests
pytest skillpilot/tests/ -v               # Verbose output
pytest skillpilot/tests/unit/test_config.py  # Single test file
pytest --cov=skillpilot --cov-report=html    # With coverage

# Linting and formatting
ruff check skillpilot/                    # Lint
ruff format skillpilot/                   # Format

# Run server
uvicorn skillpilot.main:app --reload --host 0.0.0.0 --port 8000

# Import skills from platforms
python -m scripts.import_skills --platform coze --api-key YOUR_KEY
python -m scripts.import_skills --platform dify --api-key YOUR_KEY
python -m scripts.import_skills --platform huggingface --limit 100
python -m scripts.import_skills --all --limit 25

# Build package
python -m build
```

## Architecture

### Layer Structure

```
┌─────────────────────────────────────────┐
│  API Layer (skillpilot/api/routes/)     │
│  - FastAPI routers for endpoints        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Business Logic (skillpilot/core/)      │
│  ├── services/  - Business logic        │
│  ├── models/    - Pydantic schemas      │
│  ├── importers/ - Platform skill imports│
│  ├── adapters/  - Platform integrations │
│  └── utils/     - Helpers & logging     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Data Layer (skillpilot/db/)            │
│  - SeekDBClient (singleton, vector+rel) │
└─────────────────────────────────────────┘
```

### Key Components

- **SeekDB**: Single storage backend providing both vector search (HNSW) and relational storage
- **Services** (`core/services/`):
  - `auth_service` - JWT authentication, user registration/login
  - `skill_service` - CRUD operations, skill search
  - `orchestration_service` - Task decomposition, skill chain planning
  - `embedding_service` - Text embeddings (OpenAI/local/mock)
  - `vector_search_service` - Vector similarity search
  - `ai_service` - LLM integration (OpenAI/Anthropic)
- **Platform Importers** (`core/importers/`): Plugin system to import skills from Coze, Dify, GPT Store, Hugging Face Spaces
- **Platform Adapters** (`core/adapters/`): Execute skills on external platforms - Coze, Dify, LangChain with fallback `DefaultAdapter`
- **Models**: Pydantic v2 schemas in `core/models/`

### Database Tables

- `skills` / `skill_vectors` - Skill catalog and embeddings
- `users` - User data (authentication, profiles)
- `orchestration_plans` - Task decomposition plans with skill chains
- `task_vectors` - Task embeddings for matching

### Importers Architecture

Plugin-based system for importing skills from external platforms:

```
skillpilot/core/importers/
├── base.py         - BaseImporter abstract class
├── registry.py     - Importer discovery and registration
├── coze.py         - Coze bot importer
├── dify.py         - Dify app importer
├── gptstore.py     - GPT Store importer (web scraping)
└── huggingface.py  - Hugging Face Spaces importer
```

Each importer implements `fetch_skills()` and `normalize_skill()` methods.
See `IMPORTERS.md` for detailed usage.

### Configuration

Settings loaded via `pydantic-settings` from `.env` file:
- SeekDB connection: `SEEKDB_URL`, vector dimension (1536), HNSW params
- JWT: `JWT_SECRET_KEY`, algorithm, expiry
- AI providers: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `EMBEDDING_PROVIDER`, `LLM_PROVIDER`
- API: prefix `/api/v1`, rate limits

See `.env.example` for all options. Config accessed via `skillpilot.core.config.settings`.

### Testing Pattern

- Tests use `pytest` with `pytest-asyncio` (auto mode)
- Mock external dependencies with `unittest.mock.patch`
- Mock `seekdb_client` for service tests
- Test files mirror source structure in `skillpilot/tests/`
