# SkillPilot

[![CI](https://github.com/wayyoungboy/SkillPilot/actions/workflows/ci.yml/badge.svg)](https://github.com/wayyoungboy/SkillPilot/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI Skill Orchestration Engine based on SeekDB**

[中文文档](README_CN.md) | English README

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- SeekDB (local or remote service)
- OpenAI API Key (for embeddings and AI recommendations)

### Installation

```bash
# Clone the repository
git clone git@github.com:wayyoungboy/SkillPilot.git
cd SkillPilot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

```bash
# Copy environment configuration
cp .env.example .env

# Edit .env file to configure:
# - SeekDB connection
# - OpenAI API Key (OPENAI_API_KEY)
```

### Running

```bash
# Start the server
uvicorn skillpilot.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs to view the API documentation.

### Import Skills from Platforms

SkillPilot supports importing skills from multiple AI platforms:

```bash
# Install all importers
pip install -e ".[import-all]"

# Import from Coze
python -m scripts.import_skills --platform coze --api-key YOUR_KEY

# Import from Dify
python -m scripts.import_skills --platform dify --api-key YOUR_KEY

# Import from Hugging Face (no config needed)
python -m scripts.import_skills --platform huggingface --limit 100

# Import from all platforms
python -m scripts.import_skills --all --limit 25
```

See [IMPORTERS.md](IMPORTERS.md) for detailed documentation.

### Testing

```bash
# Run all tests
pytest skillpilot/tests/ -v

# Run tests with coverage report
pytest skillpilot/tests/ --cov=skillpilot --cov-report=html
```

---

## Features

- **SeekDB as Single Storage** - Uses SeekDB as both vector database and relational database, simplifying the tech stack
- **Unified Skill Management** - Supports unified storage, search, and management of multi-platform skills
- **AI-Powered Recommendations** - Intelligent task analysis and skill matching using LLMs
- **Plugin-based Importers** - Import skills from Coze, Dify, GPT Store, Hugging Face with extensible architecture
- **Complete RESTful API** - Supports skill management, user authentication, and task orchestration
- **High Test Coverage** - 54+ unit and integration tests to ensure code quality

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  SkillPilot Application Layer       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Web Frontend │  │ API Service  │  │ SDK          ││
│  │ (TODO)       │  │ (FastAPI)    │  │ (Python)     ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────┐
│              SkillPilot Business Logic Layer        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Skill Search │  │ Skill        │  │ User         ││
│  │ Engine       │  │ Orchestration│  │ Service      ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
└────────────────────┬────────────────────────────────┘
                     │ SeekDB Client
┌────────────────────▼────────────────────────────────┐
│         SeekDB Storage Engine (Single Storage)       │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Vector Index │  │ Relational   │                 │
│  │ - Skill Vec  │  │ - Users      │                 │
│  │ - Task Vec   │  │ - Skills     │                 │
│  │ - HNSW       │  │ - Plans      │                 │
│  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
SkillPilot/
├── skillpilot/                 # Main source directory
│   ├── api/routes/          # API routes
│   │   ├── auth.py          # Authentication routes
│   │   ├── skill.py         # Skill management routes
│   │   └── orchestration.py # Orchestration routes
│   ├── core/
│   │   ├── models/          # Data models
│   │   │   ├── common.py    # Common models and enums
│   │   │   ├── user.py      # User models
│   │   │   ├── skill.py     # Skill models
│   │   │   ├── orchestration.py # Orchestration models
│   │   │   └── auth.py      # Auth models
│   │   ├── services/        # Business services
│   │   │   ├── auth.py      # Authentication service
│   │   │   ├── skill.py     # Skill service
│   │   │   └── orchestration.py # Orchestration service
│   │   └── config.py        # Configuration
│   ├── db/
│   │   └── seekdb.py        # SeekDB client
│   ├── tests/
│   │   ├── unit/            # Unit tests
│   │   └── integration/     # Integration tests
│   └── main.py              # Application entry point
├── .github/workflows/       # GitHub Actions workflows
├── pyproject.toml           # Project configuration
├── .gitignore               # Git ignore rules
├── README.md                # English documentation
├── README_CN.md             # Chinese documentation
└── .env.example             # Environment variables example
```

---

## API Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | User registration |
| POST | /api/v1/auth/login | User login |
| POST | /api/v1/auth/refresh | Refresh token |

### Skill Management

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/skills | List skills |
| GET | /api/v1/skills/{skill_id} | Get skill details |
| POST | /api/v1/skills | Create skill |
| PUT | /api/v1/skills/{skill_id} | Update skill |
| DELETE | /api/v1/skills/{skill_id} | Delete skill |
| GET | /api/v1/skills/search | Search skills |

### Orchestration

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/orchestrations | Create orchestration task |
| GET | /api/v1/orchestrations | List orchestrations |
| GET | /api/v1/orchestrations/{plan_id} | Get orchestration details |
| POST | /api/v1/orchestrations/{plan_id}/execute | Execute orchestration |
| DELETE | /api/v1/orchestrations/{plan_id} | Cancel orchestration |

---

## Data Models

### SeekDB Tables

SkillPilot uses SeekDB as its single storage infrastructure with the following tables:

| Table | Description | Main Fields |
|-------|-------------|-------------|
| `skills` | Skill catalog | skill_id, skill_name, platform, description, capabilities, rating, pricing |
| `skill_vectors` | Skill vectors | skill_id, skill_vector, capability_vectors |
| `users` | User data | user_id, email, password_hash, name, role |
| `orchestration_plans` | Orchestration plans | plan_id, task_description, skill_chain, status |
| `task_vectors` | Task vectors | task_id, task_description, task_vector, required_capabilities |

### Vector Index Configuration

```python
# HNSW Vector Index Configuration
index_type: hnsw
m: 16
ef_construction: 200
vector_dimension: 1536
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SEEKDB_URL | SeekDB connection URL | seekdb://localhost:6432 |
| SEEKDB_VECTOR_DIMENSION | Vector dimension | 1536 |
| SEEKDB_INDEX_TYPE | Index type | hnsw |
| SEEKDB_HNSW_M | HNSW M parameter | 16 |
| SEEKDB_HNSW_EF_CONSTRUCTION | HNSW ef_construction | 200 |
| JWT_SECRET_KEY | JWT secret key | (must be set) |
| JWT_ALGORITHM | JWT algorithm | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token expiry (minutes) | 15 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token expiry (days) | 7 |
| DEBUG | Debug mode | false |

---

## Development

### Code Style

This project uses Ruff for code linting and formatting:

```bash
# Lint code
ruff check skillpilot/

# Format code
ruff format skillpilot/
```

### Adding New Features

1. Add model definitions in `skillpilot/core/models/`
2. Implement business logic in `skillpilot/core/services/`
3. Add API routes in `skillpilot/api/routes/`
4. Write test cases in `skillpilot/tests/`

---

## Roadmap

- [ ] Complete SeekDB vector search implementation
- [ ] Cross-platform skill adapters (Coze, Dify, LangChain, etc.)
- [ ] AI-powered orchestration engine (LLM integration)
- [ ] Skill usage analytics and statistics
- [ ] Web admin interface
- [ ] Python SDK
- [ ] Multi-platform auto-publish feature

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

MIT License

---

## Contact

- GitHub: [@wayyoungboy](https://github.com/wayyoungboy/SkillPilot)
- Email: wayyoungboy@gmail.com
