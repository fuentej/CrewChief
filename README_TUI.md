# CrewChief TUI - Terminal User Interface Guide

**CrewChief TUI** is a mainframe-style terminal user interface for the CrewChief garage management system. It provides a retro aesthetic with modern functionality for managing your vehicle fleet and maintenance.

## Installation & Running

### Prerequisites
- Python 3.11+
- CrewChief installed with TUI dependencies (textual>=0.47.0)

### Installation

```bash
# Install CrewChief with TUI support
pip install -e ".[dev]"

# Or install textual separately if needed
pip install textual
```

### Running the TUI

```bash
crewchief-tui
```

The TUI will launch with a mainframe-style dashboard showing your garage.

## Quick Start

1. **First launch:** TUI will connect to your existing CrewChief database
2. **Dashboard:** View all vehicles, recent activity, and system stats
3. **Navigate:** Use arrow keys to select items, Enter to view details
4. **Help:** Press `?` at any time to see keybindings

## Screen Guide

### Dashboard (Main Screen)

The main screen showing your entire garage:

- **Left panel:** List of all vehicles in your garage
- **Right panel:** System statistics and recent maintenance activity
- **Footer:** Keybindings and current options

**Keybindings:**
- `[V]` - View selected vehicle details
- `[C]` - View cost analytics for all vehicles
- `[A]` - View AI-powered garage insights
- `[?]` - Show help screen
- `[Q]` - Quit the application

### Vehicle Detail Screen

Detailed view of a specific vehicle:

- **Header:** Vehicle name, year, make, model, usage type
- **Left panel:** Maintenance history table
- **Right panel:** Due services and parts profile
- **Bottom:** Selected event details

**Keybindings:**
- `[↑↓]` - Navigate maintenance history
- `[L]` - Open full maintenance log
- `[P]` - Open parts manager
- `[C]` - View costs for this vehicle
- `[A]` - View AI insights for this vehicle
- `[Enter]` - View selected event details
- `[Esc]` - Go back to dashboard

### Maintenance Log Screen

Full maintenance history for a vehicle:

- **Table:** All maintenance events with date, type, cost, description
- **Detail pane:** Full details of selected event

**Keybindings:**
- `[↑↓]` - Select event
- `[N]` - Add new maintenance entry (coming soon)
- `[E]` - Edit selected entry (coming soon)
- `[D]` - Delete selected entry (coming soon)
- `[Esc]` - Go back

### Parts Manager Screen

Manage your vehicle's parts profile:

- **Table:** All parts with category, brand, part number, specs
- **Detail pane:** Full details of selected part

**Keybindings:**
- `[↑↓]` - Select part
- `[N]` - Add new part (coming soon)
- `[E]` - Edit selected part (coming soon)
- `[D]` - Delete selected part (coming soon)
- `[Esc]` - Go back

### Costs View Screen

Cost analytics with visual breakdown:

- **Left panel:** Costs by vehicle with bar charts
- **Right panel:** Costs by service type + cost per mile calculations
- **Charts:** ASCII bar charts (█ = value, ░ = remainder)

**Keybindings:**
- `[Esc]` - Go back

### AI Panel Screen

AI-powered insights for your garage (requires Foundry Local):

- **Garage Summary:** Natural language overview of fleet health
- **Maintenance Suggestions:** Priority-labeled recommendations
- **Track Prep:** Track day preparation checklist (single vehicle)

**Keybindings:**
- `[R]` - Refresh / regenerate AI insights
- `[Esc]` - Go back

## Global Keybindings

These work from most screens:

- `[?]` - Open help screen (keybindings reference)
- `[Esc]` - Go back / close current screen
- `[Q]` - Quit application (dashboard only)

## Navigation Flow

```
Dashboard (Main)
├─ Vehicle Detail [V]
│  ├─ Maintenance Log [L]
│  ├─ Parts Manager [P]
│  ├─ Costs View [C]
│  └─ AI Panel [A]
├─ Costs View [C] (all vehicles)
└─ AI Panel [A] (all vehicles)
```

All screens support `[Esc]` to go back to the previous screen.

## Features

### Vehicle Management
- View all vehicles in your garage
- See vehicle details (year, make, model, usage type, odometer, VIN)
- Track multiple vehicles with different usage types (daily, track, project, show, other)

### Maintenance Tracking
- View complete maintenance history per vehicle
- See maintenance by type (oil change, brakes, tires, fluids, inspection, mod)
- Track costs for each service
- View service dates and odometer readings
- Add custom notes for each service

### Parts Profile
- Track specific parts for each vehicle
- Organize by category (oil, tires, brakes, filters, etc.)
- Store brand, part number, and size/spec information
- Auto-populated from maintenance logging

### Cost Analytics
- View total costs per vehicle
- Breakdown by service type
- Calculate cost per mile driven
- Visual bar charts for easy comparison
- Compare costs across your entire fleet

### AI-Powered Features
- **Garage Summary:** Natural language overview of your fleet
- **Maintenance Suggestions:** Priority-ranked recommendations for each vehicle
- **Track Prep Checklist:** Generate track day prep checklists with critical and recommended items

### Due Services
- Track maintenance intervals (miles or months)
- See which services are due or overdue
- Visual indicators for vehicle status

## Color Scheme

The TUI uses a mainframe-inspired color scheme:

- **Green (●):** Healthy/ready status
- **Yellow (⚠):** Warning/due status or in-progress
- **Red (✗):** Error/failed status
- **Cyan:** Selected/focused elements
- **Magenta:** Section headers and accents

## Performance & Data

### Local Storage
- All data stored in local SQLite database (`~/.crewchief/crewchief.db`)
- No cloud sync or remote servers
- Fast local access

### AI Features
- Requires Foundry Local running on your machine
- If Foundry Local is unavailable, AI features show graceful error messages
- Refresh (R key) to retry when service comes online

## Troubleshooting

### "Database not found"
Run `crewchief init-garage` from the command line to initialize the database.

### "LLM service unavailable"
AI features require Foundry Local running. Start it with:
```bash
foundry serve phi-3-5-mini
```

### Table navigation not working
Make sure you're in the table widget (cursor should show the selected row). Use arrow keys `[↑↓]` to navigate.

### Help text overlapping with content
Press `[Esc]` to close the help screen and return to the main content.

## Keyboard Navigation Tips

1. **Arrow keys:** Navigate up/down in tables and lists
2. **Enter:** View details or confirm selection
3. **Letters:** Quick access to functions (V, C, A, etc.)
4. **Esc:** Always goes back one screen
5. **?:** Help is available on every screen

## Advanced Usage

### Cost Analysis
- Use costs view to identify expensive maintenance
- Compare cost per mile across vehicles
- Plan maintenance budgets

### Maintenance Planning
- Use AI suggestions for priority maintenance
- Track intervals to stay on schedule
- Log all work to build accurate history

### Track Prep
- Generate vehicle-specific checklists
- Verify critical items before track days
- Use maintenance history context for recommendations

## Known Limitations

1. **Add/Edit/Delete Forms:** Currently show "coming soon" notifications. Use CLI (`crewchief` command) for these operations.
2. **Help Screen:** Static reference only. No interactive tutorials.
3. **Export/Import:** Not available in TUI. Use CLI for data export.
4. **Single Vehicle Operations:** Track prep only works on single vehicles, not the fleet.
5. **LLM Required:** Some screens need Foundry Local running for full functionality.

## Tips & Best Practices

1. **Keep maintenance history current:** AI suggestions are better with complete data
2. **Add parts to profile:** Makes future maintenance logging faster
3. **Set maintenance intervals:** Track-related services especially important for track cars
4. **Use vehicle notes:** Add context about modifications and usage patterns
5. **Regular backups:** Your database is in `~/.crewchief/crewchief.db` - back it up

## Support

For issues or feature requests:
1. Check the help screen (`?` key) for keybindings
2. Review the command-line version with `crewchief --help`
3. See main [README.md](README.md) for general CrewChief documentation

## Future Enhancements

Planned features for future TUI releases:

- Modal forms for adding/editing maintenance events
- Real-time database search and filtering
- Customizable color themes
- Export to CSV/JSON
- Multi-vehicle comparison views
- Service interval warnings
- Printable checklists

## Version

**CrewChief TUI v1.0.0** - Production Ready

Built with [Textual](https://textual.textualize.io/) and [Rich](https://rich.readthedocs.io/)
