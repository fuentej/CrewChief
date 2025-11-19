# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CrewChief** is a Python CLI application for local-first garage and maintenance tracking with LLM-powered assistance via Foundry Local.

## Current Implementation Status

**⚠️ IMPORTANT**: This project is in the **planning stage** with only documentation and templates present. No Python source code has been implemented yet. The implementation should follow the 5-phase plan detailed in `PRD.md`.

**Legacy Files to Ignore/Replace**:
- `package.json`, `index.js` - Node.js placeholders
- `docker/Dockerfile` - Currently configured for Node.js, needs Python migration

**Authoritative Documentation**:
- `PRD.md` (13.9 KB) - Complete technical specification and requirements
- This file (`CLAUDE.md`) - Development guidance for AI assistants

## Tech Stack

- **Language**: Python 3.11+
- **Core Libraries**:
  - `pydantic` v2 - Data models and validation
  - `pydantic-settings` - Configuration management
  - `typer` - CLI framework (preferred over click for type hints)
  - `httpx` - HTTP client for LLM API calls
  - `sqlite3` or `sqlmodel` - Database layer
- **LLM Runtime**: Foundry Local (OpenAI-compatible API on localhost)

## Development Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (once pyproject.toml is created)
pip install -e ".[dev]"

# Run the CLI
crewchief --help

# Run tests
pytest

# Format code
black crewchief/ tests/
ruff check crewchief/ tests/

# Run type checking (optional, once mypy is configured)
mypy crewchief/
```

## Core Architecture

**CrewChief** is a **local-first Python CLI application** with:

- **LLM Integration**: Foundry Local (OpenAI-compatible API on localhost)
- **Data Model**: Cars and MaintenanceEvents stored in local SQLite database
- **Core Features**:
  - Garage management (add/list/show cars)
  - Maintenance logging and history
  - LLM-powered garage summaries
  - AI-generated maintenance suggestions
  - Track prep checklist generation

### Python Package Structure

```
crewchief/
├── __init__.py
├── cli.py           # Typer CLI commands
├── models.py        # Pydantic models (Car, MaintenanceEvent, etc.)
├── db.py            # SQLite repository layer
├── llm.py           # Foundry Local integration
├── settings.py      # Pydantic settings for config
└── prompts/         # LLM prompt templates
```

### CLI Commands

```bash
crewchief init-garage              # Initialize DB and config
crewchief add-car                  # Add a car to garage
crewchief list-cars                # List all cars
crewchief show-car <car_id>        # Show car details
crewchief log-service <car_id>     # Log maintenance event
crewchief history <car_id>         # View maintenance history
crewchief summary                  # LLM-generated garage summary
crewchief suggest-maint            # LLM maintenance suggestions
crewchief track-prep <car_id>      # LLM track prep checklist
```

## Architecture Principles

### Local-First & Privacy
- All data stored in local SQLite database
- LLM calls only to local Foundry Local instance (no cloud APIs)
- No user authentication or multi-user support in v1
- Single-user, local-only operation

### LLM Integration Pattern

The `llm_chat()` function will:
1. Accept system prompt, user prompt, context data, and optional Pydantic response schema
2. Build OpenAI-compatible chat completion payload
3. POST to `${base_url}/chat/completions` (default: `http://localhost:1234/v1`)
4. Parse response and optionally validate against Pydantic schema
5. Return typed object or raw text

### Pydantic Data Models

**Car Model**:
- id, nickname, year, make, model, trim, vin
- usage_type (enum: daily, track, project, show, other)
- current_odometer, notes, timestamps

**MaintenanceEvent Model**:
- id, car_id (FK), service_date, odometer
- service_type (oil_change, brakes, tires, fluids, inspection, mod, other)
- description, parts, cost, location, created_at

**LLM-Specific Models** (not persisted):
- GarageSnapshot, MaintenanceSuggestion, TrackPrepChecklist

## Implementation Phases (from PRD)

When implementing the Python version, follow this sequence:

1. **Phase 1**: Python package structure, config (AppSettings), basic CLI with Typer
2. **Phase 2**: Pydantic models, SQLite schema, repository layer, basic CRUD CLI commands
3. **Phase 3**: LLM integration (`llm_chat()`, prompt templates)
4. **Phase 4**: LLM-backed CLI commands (summary, suggest-maint, track-prep)
5. **Phase 5**: Documentation, tests, error handling for LLM unavailability

## Immediate Next Steps

When starting implementation, begin with **Phase 1**:

1. Create `pyproject.toml` file with the dependencies shown below
2. Create `crewchief/` package directory with `__init__.py`
3. Implement `crewchief/settings.py` with AppSettings class
4. Create `crewchief/cli.py` with basic Typer app and `--version` command
5. Set up basic project structure and ensure `pip install -e .` works
6. Verify CLI entry point works with `crewchief --help`

Only after Phase 1 is complete and working, proceed to Phase 2 (data models and database).

## Key Development Constraints

- **No web UI in v1** - CLI only
- **No external APIs in v1** - No VIN decoding, recalls, or market data
- **Safety-first prompts** - LLM should suggest, not prescribe; recommend professionals when appropriate
- **Error resilience** - Graceful handling of LLM failures or unavailability
- **Testability** - Core logic testable without running LLM (use mocks)

## Project Structure & Dependencies

### pyproject.toml Setup

Create a `pyproject.toml` with:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "crewchief"
version = "1.0.0"
description = "Local-first garage and maintenance assistant powered by Foundry Local"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "typer>=0.9",
    "httpx>=0.24",
    "sqlmodel>=0.0.14",  # or just sqlite3 built-in
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1",
]

[project.scripts]
crewchief = "crewchief.cli:app"
```

### Recommended File Organization

```
crewchief/
├── pyproject.toml
├── PRD.md                    # Technical requirements (authoritative)
├── crewchief/
│   ├── __init__.py
│   ├── cli.py               # Typer CLI commands & entry point
│   ├── models.py            # Pydantic models (Car, MaintenanceEvent, etc.)
│   ├── db.py                # SQLite repository/ORM layer
│   ├── llm.py               # Foundry Local integration (llm_chat function)
│   ├── settings.py          # Pydantic BaseSettings for config
│   └── prompts/
│       ├── system_crewchief.txt
│       ├── garage_summary.txt
│       ├── maintenance_suggestions.txt
│       └── track_prep.txt
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_db.py
│   └── test_cli.py
└── docker/                  # Docker configs (for future deployment)
    ├── Dockerfile
    └── docker-compose.yml
```

## Configuration

Config file location: `~/.crewchief/config.toml` or local `config.json`

```toml
db_path = "~/.crewchief/crewchief.db"
llm_base_url = "http://localhost:1234/v1"
llm_model = "phi-3.5-mini"
llm_enabled = true
```

## Repository Settings & Schema

### Database Schema (SQLite)

**cars table**:
```sql
CREATE TABLE cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT,
    year INTEGER NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    trim TEXT,
    vin TEXT,
    usage_type TEXT NOT NULL,  -- 'daily', 'track', 'project', 'show', 'other'
    current_odometer INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**maintenance_events table**:
```sql
CREATE TABLE maintenance_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id INTEGER NOT NULL,
    service_date DATE NOT NULL,
    odometer INTEGER,
    service_type TEXT NOT NULL,  -- 'oil_change', 'brakes', 'tires', etc.
    description TEXT,
    parts TEXT,
    cost REAL,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (car_id) REFERENCES cars(id)
);
```

### Pydantic Settings Class

Use `pydantic-settings` for configuration:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    db_path: str = "~/.crewchief/crewchief.db"
    llm_base_url: str = "http://localhost:1234/v1"
    llm_model: str = "phi-3.5-mini"
    llm_enabled: bool = True
    llm_timeout: int = 30
```

## Implementation Best Practices

### Type Safety with Pydantic

- Use Pydantic v2 models for ALL data structures
- Leverage `Field()` for validation and defaults
- Use `model_validate()` for parsing external data (including LLM JSON responses)
- Define explicit enums for constrained fields (usage_type, service_type, priority)

Example:
```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class UsageType(str, Enum):
    DAILY = "daily"
    TRACK = "track"
    PROJECT = "project"
    SHOW = "show"
    OTHER = "other"

class Car(BaseModel):
    id: int | None = None
    nickname: str | None = None
    year: int = Field(ge=1900, le=2100)
    make: str
    model: str
    trim: str | None = None
    vin: str | None = None
    usage_type: UsageType
    current_odometer: int | None = Field(default=None, ge=0)
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### LLM Response Validation

Always validate LLM JSON responses with Pydantic schemas:

```python
from pydantic import BaseModel

class MaintenanceSuggestion(BaseModel):
    car_id: int
    car_label: str
    suggested_actions: list[str]
    priority: str  # 'high', 'medium', 'low'
    reasoning: str

# In llm.py
def llm_chat(
    system_prompt: str,
    user_prompt: str,
    context: dict | str | None = None,
    response_schema: type[BaseModel] | None = None
) -> str | BaseModel:
    # ... make API call ...
    content = response.json()["choices"][0]["message"]["content"]

    if response_schema:
        return response_schema.model_validate_json(content)
    return content
```

### Error Handling

- Wrap LLM calls in try/except blocks
- Provide clear error messages if Foundry Local is unavailable
- Never crash on LLM failures - degrade gracefully
- Validate all DB operations and provide actionable error messages

### Testing Strategy

- Mock `llm_chat()` in tests to avoid LLM dependency
- Test Pydantic models independently
- Test DB operations with in-memory SQLite (`:memory:`)
- Test CLI commands using Typer's testing utilities

## Docker & Deployment (Future)

The `docker/` and `iac/` directories contain deployment configurations for future use. For v1, focus on local CLI development only.

## Common Development Commands

```bash
# Initialize database (Phase 2+)
crewchief init-garage

# Add a car interactively
crewchief add-car

# Add a car with all parameters
crewchief add-car --year 2024 --make Porsche --model "911 GT3" --nickname "Track Monster" --usage track

# Log maintenance
crewchief log-service 1 --type oil_change --odometer 15000 --description "Motul 5W-40"

# View garage
crewchief list-cars
crewchief show-car 1

# LLM features (Phase 4+)
crewchief summary
crewchief suggest-maint
crewchief track-prep 1

# Database operations (development)
sqlite3 ~/.crewchief/crewchief.db ".schema"  # View schema
sqlite3 ~/.crewchief/crewchief.db ".tables"  # List tables
```

## Foundry Local Setup

Before using LLM features, ensure Foundry Local is running:

1. Install Foundry (see foundry.black documentation)
2. Start Foundry with a compatible model:
   ```bash
   foundry serve phi-3.5-mini
   ```
3. Verify it's accessible:
   ```bash
   curl http://localhost:1234/v1/models
   ```

## Important Notes

- **Authoritative source**: `PRD.md` contains the complete technical specification
- **No Node.js**: Ignore `package.json` and `index.js` - this is a Python project
- **Local-first**: No cloud APIs, no authentication, single-user only in v1
- **Privacy-focused**: All data and LLM calls stay on the local machine
- **Phase by phase**: Implement incrementally following the 5-phase plan in PRD.md
- **Safety first**: LLM should suggest, not prescribe; always recommend professional help when appropriate
