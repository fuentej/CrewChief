# CrewChief Architecture

## Overview

CrewChief is a local-first Python CLI application for garage and maintenance tracking with LLM assistance. The architecture follows a layered design with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  CLI Layer (cli.py)                     │
│  - Typer commands                       │
│  - User prompts and output formatting   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  Models Layer (models.py)               │
│  - Pydantic v2 models                   │
│  - Data validation                      │
│  - Type safety                          │
└────────────────┬────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼──────┐      ┌───────▼──────┐
│ DB Layer   │      │ LLM Layer    │
│ (db.py)    │      │ (llm.py)     │
│            │      │              │
│ Repository │      │ - llm_chat() │
│ pattern    │      │ - Prompts    │
│ - SQLite   │      │ - Foundry    │
└────────────┘      │   Local      │
                    └──────────────┘
                           │
                    ┌──────▼────────┐
                    │ Foundry Local │
                    │ API (port     │
                    │ 1234)         │
                    └───────────────┘
```

## Layer Descriptions

### CLI Layer (`cli.py`)
- **Purpose**: User interaction and command handling
- **Responsibilities**:
  - Parse CLI arguments using Typer
  - Prompt for user input interactively
  - Format and display output using Rich
  - Call repository and LLM functions
  - Handle errors and display messages
- **Key Classes**: Commands decorated with `@app.command()`

### Models Layer (`models.py`)
- **Purpose**: Data definitions and validation
- **Responsibilities**:
  - Define Pydantic v2 models for all data structures
  - Validate data using Pydantic field constraints
  - Provide type hints for IDE support
- **Key Models**:
  - `Car`: Vehicle information
  - `MaintenanceEvent`: Service records
  - `GarageSnapshot`: Garage state for LLM context
  - LLM response models (suggestions, checklists)

### Database Layer (`db.py`)
- **Purpose**: Data persistence
- **Responsibilities**:
  - Implement Repository pattern for data access
  - Manage SQLite connections
  - Convert database rows to Pydantic models
  - Handle CRUD operations (Create, Read, Update, Delete)
- **Key Class**: `GarageRepository`
- **Database**: SQLite with enforced foreign keys

### LLM Layer (`llm.py`)
- **Purpose**: AI integration
- **Responsibilities**:
  - Communicate with Foundry Local API
  - Load prompt templates
  - Validate responses against Pydantic schemas
  - Handle LLM-specific errors gracefully
- **Key Function**: `llm_chat()`
- **Integration**: OpenAI-compatible API at `http://localhost:1234/v1`

### Settings Layer (`settings.py`)
- **Purpose**: Configuration management
- **Responsibilities**:
  - Load settings from environment variables or .env files
  - Provide defaults for all configuration
  - Validate configuration values
- **Key Class**: `AppSettings` (Pydantic BaseSettings)

## Data Flow

### Add a Car Command
```
User input → CLI validates → Creates Car model → Repository.add_car()
→ SQLite INSERT → Returns Car with ID → Format and display
```

### Get Garage Summary (LLM)
```
CLI.summary() → Repository.get_cars() + get_all_maintenance()
→ Build GarageSnapshot → llm_chat(snapshot) → Foundry Local API
→ Validate response → Format and display
```

## Key Design Principles

1. **Local-First**: All data and LLM calls stay on the local machine
2. **Type Safety**: Pydantic models validate all data
3. **Error Resilience**: Graceful handling of LLM failures
4. **Separation of Concerns**: Each layer has a single responsibility
5. **Testability**: Core logic testable without LLM (mocks)

## Dependencies

- **pydantic**: Data validation
- **typer**: CLI framework
- **httpx**: HTTP client for LLM API
- **rich**: Terminal formatting
- **sqlite3**: Built-in database library

## Configuration

Config is managed via `AppSettings` class in `settings.py`, loaded from:
1. Environment variables (with `CREWCHIEF_` prefix)
2. `.env` file in current directory
3. Default values

Key settings:
- `db_path`: SQLite database location
- `llm_base_url`: Foundry Local API endpoint
- `llm_model`: Model name to use
- `llm_enabled`: Enable/disable LLM features
- `llm_timeout`: Request timeout in seconds
