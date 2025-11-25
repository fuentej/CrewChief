# CrewChief

**Local-first garage and maintenance assistant powered by Foundry Local**

> **Note:** CrewChief is a **demonstration project** showcasing local-first LLM integration patterns and best practices for building AI-powered CLI applications. See [LESSONS_LEARNED.md](LESSONS_LEARNED.md) for insights on working with local LLM services, handling JSON parsing, and defensive programming strategies.

CrewChief is a Python CLI application that helps you manage your garage and track maintenance for multiple vehicles, with AI-powered suggestions and insights using a local LLM. It also includes an interactive terminal UI for managing your garage visually.

**Quick Links:**
- 🖥️ **[TUI Documentation](TUI.md)** - Full guide to the interactive terminal interface
- 💻 **[CLI Commands](#commands)** - Command-line usage below

## Features

- **Garage Management**: Track multiple vehicles with detailed metadata
- **Parts Profile**: Track specific parts (oil, tires, filters) with brand and specs
- **Maintenance Logging**: Record service history, parts, and costs
- **Cost Analysis**: Track spending, cost per mile, compare across vehicles
- **Maintenance Intervals**: Set service schedules, get reminders for due services
- **AI Summaries**: Get intelligent overviews of your fleet (requires Foundry Local)
- **Maintenance Planning**: AI-powered suggestions for upcoming service
- **Track Prep**: Generate custom track day checklists for your cars
- **Local-First**: All data stays on your machine, no cloud services required

### Learning from This Project

This project demonstrates production-ready patterns for local LLM integration, including:
- Handling truncated JSON responses from local LLM services
- Multiple small requests vs. single large requests strategy
- Defensive JSON parsing with markdown extraction
- Temperature tuning for structured vs. creative outputs

See **[LESSONS_LEARNED.md](LESSONS_LEARNED.md)** for detailed insights on building reliable LLM-powered applications.

## Requirements

- **Windows 10/11 or Windows Server 2025**
- **Python 3.11 or higher**
- **Azure AI Foundry Local** (optional, for AI features)

**Need help installing?** See [PREREQUISITES.md](PREREQUISITES.md) for step-by-step instructions.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd crewchief

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install CrewChief
pip install -e .
```

## Quick Start

```bash
# Initialize your garage
crewchief init-garage

# Add your first car (interactive prompts)
crewchief add-car

# Or add a car with flags
crewchief add-car --year 2020 --make Honda --model Civic --usage daily

# List all cars
crewchief list-cars

# View detailed information for a specific car
crewchief show-car 1

# Update car information
crewchief update-car 1 --vin JF1ZNAA19H9706029 --odometer 50000

# Remove a car (with confirmation)
crewchief remove-car 1

# Log maintenance (interactive)
crewchief log-service 1

# Or with flags
crewchief log-service 1 --date 2024-01-15 --type oil_change --odometer 50000

# View maintenance history
crewchief history 1

# Get AI-powered garage summary (requires Azure AI Foundry Local)
crewchief summary

# Get maintenance suggestions
crewchief suggest-maint

# Generate track prep checklist
crewchief track-prep 1
```

## Usage Examples

### Adding Vehicles

Interactive mode walks you through each field:
```bash
$ crewchief add-car
Enter year: 2024
Enter make: Porsche
Enter model: 911 GT3
Enter trim (optional):
Enter VIN (optional): WP0AC2A9XRS123456
Select usage type [daily/track/project/show/other]: track
Enter current odometer (optional): 1200
Enter notes (optional): Track-focused build

✓ Added: 2024 Porsche 911 GT3 (ID: 1)
```

Or use flags for quick entry:
```bash
crewchief add-car \
  --year 2020 \
  --make Honda \
  --model Civic \
  --trim Si \
  --nickname "Daily Driver" \
  --usage daily \
  --odometer 45000
```

### Logging Maintenance

Track all service work with integrated parts and cost tracking:
```bash
$ crewchief log-service 1
Service type: brakes
Service date (YYYY-MM-DD, or press Enter for today): 2024-03-15
Description (optional): Replaced front brake pads and rotors

Add parts from profile? [y/N]: y

Parts in profile:
  1. Brake Pads: Hawk DTC-60
  2. Brake Fluid: Motul RBF 660

Select parts (numbers separated by spaces): 1 2
Cost for Hawk DTC-60: 125.00
Running total: $125.00
Cost for Motul RBF 660: 35.00
Running total: $160.00

Add another part (custom)? [y/N]: y
Part name: brake rotors
Cost: 250.00
Running total: $410.00

Add another part (custom)? [y/N]: n
Add labor cost? [y/N]: y
Labor cost: 200.00
Running total: $610.00

Location/shop (optional): Track Day Motorsports

✓ Service logged successfully! (ID: 42)
✓ Added 1 new parts to profile
```

**Key features:**
- Select multiple parts from your profile by number
- Enter cost for each part with running total
- Add custom parts not in profile (saved automatically)
- Add labor costs separately
- All costs tracked in service log for cost analysis

### Viewing Maintenance History

```bash
$ crewchief history 1

Maintenance History: 2024 Porsche 911 GT3

📅 2024-03-15 | 15,200 mi | Brakes
   Replaced front brake pads and rotors
   Parts: Hawk DTC-60 pads, Girodisc rotors
   Cost: $1,850.00
   Location: Track Day Motorsports

📅 2024-01-10 | 12,500 mi | Oil Change
   Motul RBF 660 brake fluid flush
   Cost: $120.00
```

### AI-Powered Features

Get a conversational overview of your garage:
```bash
$ crewchief summary

🏁 Garage Summary

Your garage is looking healthy with 2 vehicles being actively maintained.
The 2024 Porsche 911 GT3 has excellent recent service records, with brake
work completed just 5 days ago - perfect timing for track season. Your
2020 Honda Civic is due for an oil change soon, as the last service was
6 months ago at 45,000 miles. Overall, both vehicles are well-maintained
with comprehensive service histories.
```

Get intelligent maintenance recommendations:
```bash
$ crewchief suggest-maint

🔧 Maintenance Suggestions

🏎️  2024 Porsche 911 GT3 (HIGH Priority)
   • Inspect brake fluid condition - track cars need frequent checks
   • Check tire wear and pressure - critical for track safety
   • Verify torque on wheel lug nuts before next track session

   Reasoning: Track-focused vehicle with high-performance demands. Recent
   brake service is good, but fluids and tires need regular monitoring.

🚗 2020 Honda Civic (MEDIUM Priority)
   • Schedule oil change - overdue based on 6-month interval
   • Check tire tread depth and alignment

   Reasoning: Daily driver is due for routine maintenance. No critical
   safety issues, but staying on top of oil changes extends engine life.
```

Generate a track day preparation checklist:
```bash
$ crewchief track-prep 1

🏁 Track Day Prep: 2024 Porsche 911 GT3

❗ Critical Items (Must Complete)
  ☐ Inspect brake pads (minimum 50% material remaining)
  ☐ Check brake fluid level and condition
  ☐ Inspect brake lines for leaks or damage
  ☐ Verify tire tread depth (minimum 4/32")
  ☐ Check tire age (no older than 6 years)
  ☐ Inspect wheel bearings for play
  ☐ Check all fluid levels (oil, coolant, brake)
  ☐ Verify lug nut torque (95 lb-ft for Porsche)

⚙️  Recommended Items
  ☐ Set tire pressures to track spec (34/36 PSI cold)
  ☐ Bleed brakes if fluid is >1 year old
  ☐ Remove loose items from interior
  ☐ Top off washer fluid
  ☐ Check battery terminals
  ☐ Verify insurance covers track events

📝 Notes
Based on your maintenance history, brakes were last serviced 5 days ago
with new pads and rotors - excellent condition. Verify proper bedding
procedure was completed. Consider brake fluid flush if tracking regularly
(high-temp fluid degrades faster).
```

## Azure AI Foundry Local Setup

For AI-powered features, you need Azure AI Foundry Local running:

1. **Install Foundry Local:**

   Windows:
   ```bash
   winget install Microsoft.FoundryLocal
   ```

   macOS:
   ```bash
   brew install microsoft/foundrylocal/foundrylocal
   ```

2. **Download and start a model:**
   ```bash
   foundry model download Phi-3.5-mini-instruct
   foundry service start
   ```

3. **Initialize CrewChief (auto-detects Foundry Local):**
   ```bash
   crewchief init-garage
   ```

   This will automatically detect your Foundry Local endpoint and model, creating a `.env` file with the correct configuration.

See [PREREQUISITES.md](PREREQUISITES.md) for detailed setup instructions.

## Configuration

CrewChief can be configured via environment variables or a `.env` file (auto-created by `init-garage`):

```bash
CREWCHIEF_DB_PATH=~/.crewchief/crewchief.db
CREWCHIEF_LLM_BASE_URL=http://localhost:1234/v1
CREWCHIEF_LLM_MODEL=Phi-3.5-mini-instruct-generic-gpu:1
CREWCHIEF_LLM_ENABLED=true
CREWCHIEF_LLM_TIMEOUT=30
```

**Note:** The model name should use the fID format (e.g., `Phi-3.5-mini-instruct-generic-gpu:1`). The `init-garage` command automatically detects this from your Foundry Local instance.

## Commands

CrewChief provides 21 commands organized by category. Run `crewchief commands` for a formatted list, or `crewchief <command> --help` for detailed help on any command.

### Setup
- `init-garage` - Initialize the garage database and configuration

### Car Management
- `add-car` - Add a new car to your garage
- `list-cars` - List all cars
- `show-car <id>` - Show detailed info for a car
- `update-car <id>` - Update car information
- `remove-car <id>` - Remove a car and its history

### Maintenance Logging
- `log-service <id>` - Log a maintenance event
- `history <id>` - View maintenance history
- `update-service <id>` - Edit a maintenance record
- `delete-service <id>` - Delete a maintenance record

### Parts Profile
- `add-part <id>` - Add a part (oil, tires, filters, etc.)
- `list-parts <id>` - List all parts for a car
- `update-part <id>` - Edit a part
- `delete-part <id>` - Delete a part

### Cost Analysis
- `cost-summary [id]` - Cost breakdown (single car or all)
- `cost-compare` - Compare costs across all cars

### Maintenance Intervals
- `set-interval <id>` - Set service intervals (miles/months)
- `check-due [id]` - Check which services are due

### AI Features (LLM-powered)
- `summary [id]` - AI-generated garage/car summary
- `suggest-maint [id]` - AI maintenance suggestions
- `track-prep <id>` - Generate track day checklist

> **Tip:** Use `crewchief commands` to see this list in your terminal with color-coded categories.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black crewchief/ tests/
ruff check crewchief/ tests/

# Run type checking
mypy crewchief/
```

## Architecture

CrewChief is built with:
- **Typer** for CLI interface
- **Pydantic v2** for data validation
- **SQLite** for local data storage
- **httpx** for LLM API calls
- **Azure AI Foundry Local** for AI features

## Project Status

✅ **Version 1.1.0** - Core features plus advanced tracking capabilities!

**Completed (v1.0):**
- ✅ Phase 1: Package structure, configuration, basic CLI
- ✅ Phase 2: Pydantic models, SQLite database, CRUD operations
- ✅ Phase 3: LLM integration with Azure AI Foundry Local
- ✅ Phase 4: AI-powered CLI commands (summary, suggestions, track prep)
- ✅ Phase 5: Comprehensive test suite (models, database, LLM, CLI)

**Completed (v1.1 - Expansion):**
- ✅ Parts Profile System: Track specific parts (oil, tires, filters, etc.)
- ✅ Individual Car Summaries: AI summaries and suggestions per-car
- ✅ Cost Analysis: Track spending, cost per mile, compare across cars
- ✅ Maintenance Intervals: Set schedules, auto-track due services
- ✅ Enhanced LLM Integration: Multiple small requests to avoid truncation
- ✅ Commands Browser: `crewchief commands` for easy discovery

**Future Enhancements:**
- Export/Import functionality (CSV/JSON)
- Total Cost of Ownership (TCO) tracking

## License

This is demonstration-only software. You may download and run it as-is for evaluation,
but you may not modify, redistribute, or use it commercially. See the LICENSE file
for full terms.

## Contributing

Contributions welcome! Please see development documentation for guidelines.
