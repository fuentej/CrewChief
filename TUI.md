# CrewChief TUI (Terminal User Interface)

CrewChief includes a full-featured interactive terminal user interface (TUI) built with [Textual](https://textual.textualize.io/), a rich Python framework for building beautiful terminal applications.

## Launching the TUI

```bash
crewchief-tui
```

This launches the interactive dashboard where you can manage your entire garage from the terminal.

## Main Dashboard

The main screen shows three key sections:

**Left Panel:**
- **Garage Fleet** (60%) - Table of all your vehicles with quick status
- **System Status** (40%) - Summary stats (total vehicles, maintenance events, parts tracked, AI service status, database health)

**Right Panel:**
- **Maintenance Log** - Recent maintenance events across all vehicles with date, vehicle, service type, and cost

## Navigation & Key Bindings

### Dashboard Screen
| Key | Action |
|-----|--------|
| **N** | New Car - Add a new vehicle to your garage |
| **V** | View Car - Show detailed information for selected vehicle |
| **E** | Edit Car - Modify selected vehicle details |
| **D** | Delete Car - Remove a vehicle and its history |
| **C** | View Costs - Open cost analysis dashboard |
| **A** | AI Insights - Get AI-powered garage summary and suggestions |
| **?** | Help - Show available commands |
| **Q** | Quit - Exit the TUI |

### Navigation Between Screens
| Key | Action |
|-----|--------|
| **Escape** | Go back to previous screen |
| **↑/↓** | Navigate lists/tables |
| **Enter** | Select item or confirm action |

## Available Screens

### Vehicle Detail Screen
View comprehensive information for a selected vehicle:
- Basic info (year, make, model, VIN, odometer)
- Maintenance history for that vehicle
- Parts profile specific to that car
- Cost tracking for that vehicle

### Costs View
Analyze spending across your garage:
- **Costs by Vehicle** - Total spending per car with visual bar charts
- **Costs by Service Type** - Breakdown of maintenance by category (oil changes, brakes, tires, etc.)
- **Cost Per Mile** - Compare efficiency across vehicles

Switch between single-vehicle view and all-vehicles view to compare spending patterns.

### AI Panel
Get AI-powered insights (requires Azure AI Foundry Local running):
- **Garage Summary** - LLM-generated overview of your fleet's maintenance status
- **Maintenance Suggestions** - AI recommendations for upcoming services by priority
- **Track Prep Checklist** - For track-focused vehicles, get a checklist of critical items before a track day

Press **R** to refresh and regenerate suggestions.

### Parts Manager
Manage your parts catalog for a specific vehicle:
- **View Parts** - Browse all parts in the vehicle's profile
- **Add Part** - Create new part record (category, brand, part number, specs, notes)
- **Edit Part** - Modify existing part information
- **Delete Part** - Remove a part from the profile

Parts are reusable across multiple service logs and build over time as you log maintenance.

| Key | Action |
|-----|--------|
| **N** | New Part |
| **E** | Edit selected part |
| **D** | Delete selected part |
| **V** | View part details |

## Color Scheme

The TUI uses a consistent color scheme for visual feedback:

- **Primary** - Borders and dividers
- **Boost** - Section headers and highlights
- **Panel** - Background for content areas
- **Text** - Default text color
- **Secondary** - Header text
- **Success/Green** - OK status, positive indicators
- **Warning/Orange** - Caution, pending items
- **Error/Red** - Errors, critical items
- **Accent** - Special highlights

## Dashboard Banner

The main dashboard features a rotating banner with racing-themed motivational phrases:

- "If you're not first, you're last!"
- "All your base are below to us"
- "First or last, that's racing"
- "Second place is first loser"
- "No participation trophies"
- "Victory is the only option"
- "Dominate or don't show up"

A new phrase is randomly selected each time you launch the TUI.

## Forms & Data Entry

### Interactive Forms
Forms guide you through adding or editing data:
- Required fields are marked with **\***
- Select dropdowns for predefined options
- Text fields for custom input
- Textarea for longer notes
- **Save** to commit changes or **Cancel** to discard

### Validation
- Required fields must be filled
- Enums (usage type, service type, part category) enforce valid selections
- Database constraints prevent invalid data

## Features

### Real-Time Updates
- All screens refresh data when you return to them
- Changes made in one screen immediately appear in others
- Maintenance log updates automatically as you add services

### Search & Filter
- Vehicle table shows all cars at a glance
- Maintenance log shows recent events across all vehicles
- Sort by clicking table headers

### Status Indicators
- Vehicle status shows maintenance urgency
- System status displays database and AI service health
- Cost indicators use visual bar charts for quick comparison

### Error Handling
- Graceful error messages if database operations fail
- AI features degrade gracefully if Foundry Local is unavailable
- All critical operations have confirmation dialogs

## Keyboard Shortcuts

- **Esc** - Back/Cancel
- **?** - Help
- **Q** - Quit (from dashboard)
- **↑/↓** - Navigate
- **Enter** - Select/Confirm
- **R** - Refresh (in AI panel)

## Tips & Tricks

1. **Quick Navigation** - Use single-letter bindings (N, V, E, D, C, A) for fast operations
2. **Cost Analysis** - Use the costs view to identify expensive maintenance patterns
3. **Parts Profile** - Build your parts catalog over time as you log services for more accurate cost tracking
4. **AI Insights** - Refresh AI panel to get fresh suggestions based on latest maintenance data
5. **Track Prep** - Use track prep checklist 1-2 days before a track event to ensure vehicle readiness

## Troubleshooting

### TUI won't launch
- Ensure your terminal supports 256-color or true-color
- Try setting `TERM=xterm-256color` or `TERM=screen-256color`
- Windows: Use Windows Terminal or similar modern terminal emulator

### Text is garbled or misaligned
- Update Textual: `pip install --upgrade textual`
- Try a different terminal emulator
- Check terminal width is at least 80 columns

### AI features not working
- Ensure Azure AI Foundry Local is running: `foundry service start`
- Verify the model is loaded: `foundry model list`
- Check configuration with `crewchief init-garage`

### Performance is slow
- Large maintenance histories may take time to render
- Consider archiving old vehicles if performance degrades
- Keep terminal window reasonably sized

## Limitations

- **Single-user only** - No multi-user support
- **Local data only** - No cloud sync or backup
- **Terminal-based** - Requires terminal emulator support for colors and Unicode
- **AI optional** - AI features require Foundry Local, CLI works without it

## See Also

- [README.md](README.md) - Main project documentation
- [LESSONS_LEARNED.md](LESSONS_LEARNED.md) - LLM integration patterns
- [PREREQUISITES.md](PREREQUISITES.md) - Setup instructions
