# CrewChief – Technical Product Requirements

## 0. Purpose & Audience

This document defines the **technical product requirements** for **CrewChief** – a local-first garage and maintenance assistant powered by **Foundry Local**.

**Primary audience:**
AI coding assistants (e.g., Claude Code, Augment Code) and human developers who will:

* Design the architecture,
* Generate and organize the code,
* Evolve the project in phases.

The focus for **v1** is:

* Local-only, single-user **garage + maintenance**,
* A thin agent-like layer using **Foundry Local** for reasoning,
* No cloud persistence or user accounts.

---

## 1. Product Overview

### 1.1. Concept

**CrewChief** is a local Python application that:

* Stores and manages a **garage** of cars and **maintenance history**.
* Uses a **local LLM via Foundry Local** to:

  * Summarize the garage,
  * Prioritize upcoming maintenance,
  * Suggest track-prep and service plans.

All data and AI calls remain on the user’s machine (except optional external APIs in later phases).

### 1.2. Core Goals (v1)

* Provide a **simple CLI-based UX** to:

  * Add cars,
  * Log maintenance,
  * View summaries.
* Use a **local LLM** to:

  * Generate plain-language summaries of garage/maintenance,
  * Suggest **what to do next** (maintenance roadmap),
  * Suggest **track prep** steps for a selected car.
* Ensure **local-first, privacy-friendly** architecture:

  * Data in local SQLite or equivalent (no remote DB),
  * LLM endpoint default is Foundry Local on `localhost`.

### 1.3. Explicit Non-goals (for v1)

* No user authentication / multi-user accounts.
* No web UI (CLI only for v1).
* No marketplace / listings / valuation.
* No VIN decoding / recall / external car APIs (these are v2+).
* No remote deployment or cloud hosting.

---

## 2. Target User & Use Cases

### 2.1. User

* Technical car enthusiast (gearhead).
* Comfortable with CLI / terminal.
* Has multiple cars (daily, project, track, etc.).
* Wants help staying on top of maintenance and track readiness.

### 2.2. Primary Use Cases (v1)

1. **Garage Setup**

   * Add 1–N cars with metadata (year, make, model, nickname, usage type, current mileage, notes).

2. **Maintenance Logging**

   * Log events (oil change, brakes, tires, fluids, mods, inspections).
   * View history per car.

3. **Garage Summary**

   * Ask CrewChief: “What’s my fleet like?”
   * LLM returns a text summary (e.g., which cars are daily vs track toys, mileage, age).

4. **Maintenance Roadmap**

   * Ask CrewChief: “What should I do next for my cars?”
   * LLM looks at maintenance history + simple rule-of-thumb intervals and suggests next items with rough priority.

5. **Track Prep Helper**

   * For a selected car: “I have a track day coming up; what should I do?”
   * LLM uses car metadata + last maintenance events + generic track-prep docs to output a checklist.

---

## 3. High-Level Architecture

### 3.1. Components

* **CLI Frontend**

  * `crewchief` command with subcommands:

    * `init-garage`, `add-car`, `list-cars`, `log-service`, `history`, `summary`, `suggest-maint`, `track-prep`.

* **Core App / Domain Layer (Python)**

  * Pydantic models for:

    * `Car`, `MaintenanceEvent`, `GarageSummary`, `MaintenanceSuggestion`, etc.
  * A `GarageRepository` implementation over SQLite.

* **Persistence Layer**

  * Local **SQLite** database:

    * Single file (e.g., `crewchief.db`) in a user-configurable directory.
  * Migrations/schemas managed by the app (no external tooling required).

* **LLM Integration Layer**

  * HTTP client to **Foundry Local** (OpenAI-compatible style).
  * Helper function (e.g., `llm_chat()`), and higher-level helpers for:

    * `generate_garage_summary()`,
    * `generate_maintenance_plan()`,
    * `generate_track_prep_checklist()`.

* **Config & Settings**

  * Config file (e.g., `config.toml` or `.env`) + Pydantic `BaseSettings` for:

    * Foundry Local base URL,
    * Model name,
    * Path to DB,
    * Optional switches (LLM on/off).

### 3.2. Tech Stack

* **Language:** Python 3.11+

* **Libraries:**

  * `pydantic` v2 (core models),
  * `pydantic-settings` for configuration,
  * `sqlite3` or lightweight ORM (e.g., SQLModel / SQLAlchemy with Pydantic models as schemas),
  * `httpx` or `requests` for LLM HTTP calls,
  * `typer` or `click` for CLI (typer preferred for type hints).

* **LLM Runtime:**

  * **Foundry Local** running on user’s machine,
  * OpenAI-compatible endpoint, e.g. `http://localhost:<port>/v1`.

---

## 4. Data Model Requirements

### 4.1. Car

Minimal fields (v1):

* `id` (int, primary key)
* `nickname` (str, optional but recommended)
* `year` (int)
* `make` (str)
* `model` (str)
* `trim` (str | None)
* `vin` (str | None, not required v1)
* `usage_type` (enum: `daily`, `track`, `project`, `show`, `other`)
* `current_odometer` (int | None)
* `notes` (str | None)
* `created_at` (datetime)
* `updated_at` (datetime)

### 4.2. MaintenanceEvent

Fields:

* `id` (int, primary key)
* `car_id` (FK → Car)
* `service_date` (date)
* `odometer` (int | None)
* `service_type` (enum or string; v1 may use free text with suggested categories like `oil_change`, `brakes`, `tires`, `fluids`, `inspection`, `mod`, `other`)
* `description` (str | None)
* `parts` (str | None – free text list)
* `cost` (float | None)
* `location` (str | None – shop name or DIY)
* `created_at` (datetime)

### 4.3. Aggregate / Derived Models (for LLM)

Not persisted, but defined as Pydantic models for LLM interaction:

* `GarageSnapshot`

  * `cars: list[Car]`
  * `maintenance_events: list[MaintenanceEvent]` (possibly filtered/reduced)

* `MaintenanceSuggestion`

  * `car_id` (int)
  * `car_label` (e.g., `"2017 Toyota 86 (track)"`)
  * `suggested_actions: list[str]`
  * `priority` (enum: `high`, `medium`, `low`)
  * `reasoning` (str)

* `TrackPrepChecklist`

  * `car_id` (int)
  * `car_label` (str)
  * `items: list[str]`
  * `notes: str | None`

These models should be used to validate any JSON structured output from the LLM.

---

## 5. Functional Requirements

### 5.1. Garage Management

* **Init command**

  * `crewchief init-garage`
  * Creates:

    * Config file (if not present),
    * SQLite DB with required tables.

* **Add car**

  * `crewchief add-car`

    * Interactive prompts or CLI flags:

      * year, make, model, nickname, usage_type, odometer, notes.
  * Stores car in DB.

* **List cars**

  * `crewchief list-cars`
  * Shows row per car with:

    * id, nickname, year/make/model, usage, current_odometer.

* **View car details**

  * `crewchief show-car <car_id>`
  * Shows details + last few maintenance events.

### 5.2. Maintenance Management

* **Log maintenance**

  * `crewchief log-service <car_id>`

    * Interactive prompts or flags:

      * service_date (default= today),
      * odometer,
      * service_type,
      * description,
      * parts,
      * cost.
  * Adds a row to `MaintenanceEvent`.

* **View history**

  * `crewchief history <car_id>`
  * Shows chronological list of maintenance events with date, type, short description.

### 5.3. LLM-Assisted Features

#### 5.3.1. Garage Summary

* Command:

  * `crewchief summary`
* Behavior:

  * Fetch all cars + last (N) maintenance events (configurable).
  * Build a `GarageSnapshot` object and serialize to JSON.
  * Call LLM with:

    * System prompt: CrewChief persona.
    * Context: `GarageSnapshot` JSON.
    * User prompt: e.g. `"Summarize this garage and highlight what stands out."`
  * Print summary to stdout.

#### 5.3.2. Maintenance Suggestions

* Command:

  * `crewchief suggest-maint`
* Behavior:

  * Same base as `summary`, but user prompt:

    * `"Based on this garage and maintenance history, propose the next 5–10 maintenance actions across cars, ordered by priority. Return JSON following the `MaintenanceSuggestion` schema."`
  * Parse LLM response via Pydantic `MaintenanceSuggestion` models.
  * Print:

    * Human-readable suggestions,
    * Optionally a `--json` flag to output raw JSON.

#### 5.3.3. Track Prep Checklist

* Command:

  * `crewchief track-prep <car_id>`
* Behavior:

  * Fetch car + recent maintenance events for that car.
  * Provide generic track-prep guidelines from a static local file (e.g., `track_prep_guide.md`).
  * Call LLM with:

    * System prompt: CrewChief persona + safety emphasis.
    * Context: car data + recent maintenance + track-prep guide text.
    * User prompt: `"Generate a pre-track checklist tailored for this car and its current state. Use bullet points."`
  * Print checklist.

### 5.4. Config & Modes

* Config file (e.g., `~/.crewchief/config.toml` or `config.json` in project dir) containing:

  * `db_path`
  * `llm_base_url` (default: `http://localhost:1234/v1`)
  * `llm_model` (e.g., `phi-3.5-mini` or similar)
  * `llm_enabled` (bool, default: true)

* If `llm_enabled = false`:

  * LLM-dependent commands should:

    * Exit with a clear message or
    * Fall back to deterministic, non-AI summaries.

---

## 6. LLM Integration Details

### 6.1. Call Pattern

Implement a single reusable function (module-private) such as:

* `llm_chat(system_prompt: str, user_prompt: str, context: dict | str | None, response_schema: type[BaseModel] | None = None) -> str | BaseModel`

Behavior:

1. Load settings (base URL, model) from `AppSettings` (Pydantic settings class).

2. Build an OpenAI-style `chat.completions` payload:

   ```json
   {
     "model": "<model>",
     "messages": [
       { "role": "system", "content": "<system_prompt>" },
       { "role": "user", "content": "<combined user prompt + serialized context>" }
     ]
   }
   ```

3. Send POST to `${base_url}/chat/completions`.

4. Parse JSON response:

   * `choices[0].message.content`.

5. If `response_schema` is provided:

   * Expect the LLM content to be JSON.
   * Validate with `response_schema.model_validate_json(...)`.
   * Return the typed object.

6. If `response_schema` is `None`:

   * Return raw text.

### 6.2. Prompts

Persist prompt templates as text files or Python multi-line strings, e.g.:

* `prompts/system_crewchief.txt`
* `prompts/garage_summary.txt`
* `prompts/maintenance_suggestions.txt`
* `prompts/track_prep.txt`

**System prompt baseline:**

* Defines CrewChief persona:

  * Car-savvy, track-aware, safety-conscious.
* Constraints:

  * Suggest, don’t prescribe; recommend professional mechanic when in doubt.
  * Use only given context; don’t hallucinate specifics about the car beyond provided data.

---

## 7. Non-Functional Requirements

* **Local-first & privacy:**

  * All data persisted locally in SQLite.
  * Only LLM calls go off-process (to local Foundry Local HTTP server).
  * v1: No network calls to external APIs.

* **Performance:**

  * Target CLI latency:

    * Non-LLM commands: < 200 ms.
    * LLM commands: mainly dependent on model; app overhead minimal.

* **Resilience:**

  * If LLM call fails (no server, timeout, invalid response):

    * User gets a clear error message.
    * App does not crash.
  * DB errors should be surfaced with actionable text (e.g., `"DB file not found, did you run init-garage?"`).

* **Testability:**

  * Core logic (garage, maintenance, snapshots) should be testable without running LLM.
  * LLM calls abstracted behind `llm_chat` so tests can mock it.

---

## 8. Implementation Plan (for AI Coder)

The AI coder should break work into **small, incremental steps**. Suggested order:

### Phase 1 – Skeleton & Config

* [ ] Create Python package structure, e.g.:

  * `crewchief/`

    * `__init__.py`
    * `cli.py`
    * `models.py`
    * `db.py`
    * `llm.py`
    * `settings.py`
    * `prompts/`
* [ ] Add `pyproject.toml` with dependencies: `pydantic`, `pydantic-settings`, `typer`, `httpx`, etc.
* [ ] Implement `AppSettings` (Pydantic settings) with fields for DB path, LLM base URL, model, enabled flag.
* [ ] Wire up a basic `crewchief` CLI entry point with Typer and a `--version` command.

### Phase 2 – Data Models & DB

* [ ] Define Pydantic models: `Car`, `MaintenanceEvent`.
* [ ] Implement SQLite schema and simple repository layer:

  * `GarageRepository` with methods:

    * `init_db()`
    * `add_car()`, `get_cars()`, `get_car()`
    * `add_maintenance_event()`, `get_maintenance_for_car()`.
* [ ] Implement CLI commands:

  * `init-garage`
  * `add-car`
  * `list-cars`
  * `show-car`
  * `log-service`
  * `history`

### Phase 3 – LLM Integration

* [ ] Implement `llm_chat()` in `llm.py` wired to Foundry Local-style endpoint.
* [ ] Add prompt templates in `prompts/` directory.
* [ ] Implement helper functions:

  * `generate_garage_summary(snapshot: GarageSnapshot) -> str`
  * `generate_maintenance_suggestions(snapshot: GarageSnapshot) -> list[MaintenanceSuggestion]`
  * `generate_track_prep_checklist(car: Car, events: list[MaintenanceEvent]) -> TrackPrepChecklist | str`

### Phase 4 – LLM-Backed CLI Commands

* [ ] Implement `summary` command:

  * Build `GarageSnapshot`,
  * Call `generate_garage_summary`,
  * Print result.

* [ ] Implement `suggest-maint` command:

  * Build `GarageSnapshot`,
  * Call `generate_maintenance_suggestions`,
  * Print suggestions as table / bullets, with `--json` option.

* [ ] Implement `track-prep <car_id>` command:

  * Load car + recent events,
  * Load static track-prep guide file,
  * Call `generate_track_prep_checklist`,
  * Print checklist.

### Phase 5 – Polish & Docs

* [ ] Add basic README:

  * What CrewChief is,
  * Requirements (Python, Foundry Local),
  * Quickstart commands.
* [ ] Add minimal tests for:

  * DB operations,
  * CLI non-LLM commands.
* [ ] Add a simple “LLM not available” handling path:

  * Meaningful error messages when Foundry Local isn’t running.

---

This PRD should give the AI coder enough structure to **plan the actual implementation**, organize the repo, and generate code in small, safe iterations.
