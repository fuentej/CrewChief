# CrewChief

**Local-first garage and maintenance assistant powered by Foundry Local**

CrewChief is a Python CLI application that helps you manage your garage and track maintenance for multiple vehicles, with AI-powered suggestions and insights using a local LLM.

## Features

- **Garage Management**: Track multiple vehicles with detailed metadata
- **Maintenance Logging**: Record service history, parts, and costs
- **AI Summaries**: Get intelligent overviews of your fleet (requires Foundry Local)
- **Maintenance Planning**: AI-powered suggestions for upcoming service
- **Track Prep**: Generate custom track day checklists for your cars
- **Local-First**: All data stays on your machine, no cloud services required

## Requirements

- Python 3.11 or higher
- [Foundry Local](https://foundry.black) (for AI features)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd crewchief

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

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

# Log maintenance (interactive)
crewchief log-service 1

# Or with flags
crewchief log-service 1 --date 2024-01-15 --type oil_change --odometer 50000

# View maintenance history
crewchief history 1

# Get AI-powered garage summary (requires Foundry Local)
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

Track all service work:
```bash
$ crewchief log-service 1
Enter service date (YYYY-MM-DD): 2024-03-15
Select service type [oil_change/brakes/tires/fluids/inspection/mod/other]: brakes
Enter odometer reading (optional): 15200
Enter description (optional): Replaced front brake pads and rotors
Enter parts used (optional): Hawk DTC-60 pads, Girodisc rotors
Enter cost (optional): 1850.00
Enter service location (optional): Track Day Motorsports

✓ Maintenance logged for 2024 Porsche 911 GT3
```

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

## Foundry Local Setup

For AI-powered features, you need Foundry Local running:

1. Install Foundry (see [foundry.black](https://foundry.black) for instructions)
2. Start Foundry with a compatible model:
   ```bash
   foundry serve phi-3.5-mini
   ```
3. Verify it's accessible:
   ```bash
   curl http://localhost:1234/v1/models
   ```

## Configuration

CrewChief can be configured via environment variables or a `.env` file:

```bash
CREWCHIEF_DB_PATH=~/.crewchief/crewchief.db
CREWCHIEF_LLM_BASE_URL=http://localhost:1234/v1
CREWCHIEF_LLM_MODEL=phi-3.5-mini
CREWCHIEF_LLM_ENABLED=true
CREWCHIEF_LLM_TIMEOUT=30
```

## Commands

- `init-garage` - Initialize database and configuration
- `add-car` - Add a new vehicle to your garage
- `list-cars` - Show all vehicles
- `show-car <id>` - Display details for a specific car
- `log-service <id>` - Record a maintenance event
- `history <id>` - View maintenance history for a car
- `summary` - Get AI summary of your garage
- `suggest-maint` - Get AI maintenance recommendations
- `track-prep <id>` - Generate track day checklist

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development documentation.

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
- **Foundry Local** for AI features

See [PRD.md](PRD.md) for complete technical specifications.

## Project Status

✅ **Version 1.0.0** - Core features complete! Phase 1-4 implemented with comprehensive test suite.

**Completed:**
- ✅ Phase 1: Package structure, configuration, basic CLI
- ✅ Phase 2: Pydantic models, SQLite database, CRUD operations
- ✅ Phase 3: LLM integration with Foundry Local
- ✅ Phase 4: AI-powered CLI commands (summary, suggestions, track prep)
- ✅ Phase 5: Comprehensive test suite (models, database, LLM, CLI)

**Remaining:**
- Documentation polish
- Additional error handling edge cases

## License

[License information to be added]

## Contributing

Contributions welcome! Please see development documentation for guidelines.
