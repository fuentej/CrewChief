"""Help screen - displays keybindings and usage information."""

from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Label
from textual.binding import Binding


class HelpScreen(Screen):
    """Help overlay showing keybindings and navigation."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-panel {
        width: 80;
        height: auto;
        border: heavy $primary;
        background: $boost;
        padding: 1;
    }

    #help-title {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #help-content {
        width: 100%;
        height: auto;
        color: $text;
        overflow: auto;
    }

    .section-header {
        color: $secondary;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    .keybinding {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Close"),
        Binding("q", "back", "Close"),
    ]

    HELP_TEXT = r"""
┌─ MAIN SCREENS ────────────────────────────────────────────────┐
│                                                                │
│  Dashboard (Main Screen)                                      │
│    [V]iew Vehicle       View selected vehicle details         │
│    [C]osts              View cost analytics                   │
│    [A]I Insights        View AI-powered summaries             │
│    [?]Help              Show this help screen                 │
│    [Q]uit               Exit the application                  │
│                                                                │
│  Vehicle Detail Screen                                        │
│    [↑↓]Select           Navigate maintenance history          │
│    [L]og                View full maintenance log             │
│    [P]arts              Manage parts profile                  │
│    [C]osts              View costs for this vehicle           │
│    [A]I                 View AI insights for this vehicle     │
│    [Enter]              View selected event details           │
│    [Esc]Back            Return to dashboard                   │
│                                                                │
│  Maintenance Log Screen                                       │
│    [↑↓]Select           Select maintenance event              │
│    [N]ew Entry          Add new maintenance event             │
│    [E]dit               Edit selected event                   │
│    [D]elete             Delete selected event                 │
│    [Esc]Back            Return to previous screen             │
│                                                                │
│  Parts Manager Screen                                         │
│    [↑↓]Select           Select part                           │
│    [N]ew Part           Add new part to profile               │
│    [E]dit               Edit selected part                    │
│    [D]elete             Delete selected part                  │
│    [Esc]Back            Return to previous screen             │
│                                                                │
│  Costs View Screen                                            │
│    Displays cost analytics with visual bar charts            │
│    [Esc]Back            Return to previous screen             │
│                                                                │
│  AI Panel Screen                                              │
│    Shows AI-powered summaries and suggestions                │
│    [R]efresh            Regenerate AI insights               │
│    [Esc]Back            Return to previous screen             │
│                                                                │
├─ GLOBAL KEYBINDINGS ──────────────────────────────────────────┤
│                                                                │
│  [?]                    Open help (this screen)               │
│  [Q]                    Quit application (from dashboard)     │
│  [Esc]                  Go back / close current screen        │
│                                                                │
├─ NAVIGATION FLOW ────────────────────────────────────────────┤
│                                                                │
│  Dashboard                                                    │
│    └─ Vehicle Detail (V key)                                 │
│       ├─ Maintenance Log (L key)                             │
│       ├─ Parts Manager (P key)                               │
│       ├─ Costs View (C key)                                  │
│       └─ AI Panel (A key)                                    │
│    ├─ Costs View (C key) - all vehicles                      │
│    └─ AI Panel (A key) - all vehicles                        │
│                                                                │
├─ TIPS & TRICKS ──────────────────────────────────────────────┤
│                                                                │
│  • Use arrow keys [↑↓] to navigate tables                    │
│  • Press [Enter] to view details of selected items           │
│  • All costs are shown in USD currency                       │
│  • AI features require Foundry Local running                 │
│  • Cost analytics use data from maintenance history          │
│  • Parts profile auto-populates during maintenance logging   │
│                                                                │
└──────────────────────────────────────────────────────────────┘
    """

    def compose(self):
        """Compose help screen."""
        with Container(id="help-panel"):
            yield Label("[ CREWCHIEF TUI - HELP & KEYBINDINGS ]", id="help-title")
            yield Static(self.HELP_TEXT, id="help-content")

    def action_back(self) -> None:
        """Close help screen."""
        self.app.pop_screen()
