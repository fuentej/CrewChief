"""AI panel screen - LLM-powered summaries and suggestions."""

from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Label, Button
from textual.binding import Binding

from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.services.ai_service import AIService
from crewchief.tui.services.garage_service import GarageService


class AIPanelScreen(Screen):
    """Screen showing AI-powered garage insights."""

    DEFAULT_CSS = """
    AIPanelScreen {
        layout: vertical;
    }

    #header {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $boost;
        padding: 1;
    }

    #title {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
    }

    #content-area {
        width: 100%;
        height: 1fr;
        layout: vertical;
        overflow: auto;
    }

    .ai-section {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }

    .ai-header {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    .ai-content {
        width: 100%;
        height: auto;
        color: $text;
    }

    .ai-loading {
        color: $warning;
        text-style: bold;
    }

    .ai-error {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, car_id: int | None = None, **kwargs):
        """Initialize AI panel screen.

        Args:
            car_id: If provided, show AI insights for specific vehicle.
        """
        super().__init__(**kwargs)
        self.car_id = car_id
        self.garage_service = GarageService()
        self.ai_service = AIService()

    def compose(self):
        """Compose AI panel layout."""
        with Container(id="header"):
            yield Label("[ AI INSIGHTS ]", id="title")

        with Container(id="content-area"):
            # Garage Summary
            yield Static("", classes="ai-section")

            # Maintenance Suggestions
            yield Static("", classes="ai-section")

            # Track Prep (single vehicle only)
            if self.car_id:
                yield Static("", classes="ai-section")

        yield HelpFooter(
            help_text=" [R]efresh  [Esc]Back  [?]Help",
            id="help-footer",
        )

    def on_mount(self) -> None:
        """Load AI data when screen mounts."""
        self.load_ai_data()

    def load_ai_data(self) -> None:
        """Load and display AI insights."""
        sections = self.query(".ai-section")

        if len(sections) >= 1:
            self._load_garage_summary(sections[0])

        if len(sections) >= 2:
            self._load_maintenance_suggestions(sections[1])

        if self.car_id and len(sections) >= 3:
            self._load_track_prep(sections[2])

    def _load_garage_summary(self, section: Static) -> None:
        """Load and display garage summary.

        Args:
            section: The widget to display summary in.
        """
        try:
            section.update(Static("⟳ Generating garage summary...", classes="ai-loading").render())

            summary = self.ai_service.get_garage_summary(self.car_id)

            if isinstance(summary, str):
                content = f"[ GARAGE SUMMARY ]\n\n{summary}"
                section.update(content)
            else:
                section.update("[ ERROR ] Failed to generate summary", classes="ai-error")

        except Exception as e:
            section.update(f"[ ERROR ] {str(e)}", classes="ai-error")

    def _load_maintenance_suggestions(self, section: Static) -> None:
        """Load and display maintenance suggestions.

        Args:
            section: The widget to display suggestions in.
        """
        try:
            suggestions = self.ai_service.get_maintenance_suggestions(self.car_id)

            if isinstance(suggestions, str):
                # Error message
                content = f"[ MAINTENANCE SUGGESTIONS ]\n\n{suggestions}"
                section.update(content, classes="ai-error")
            else:
                # List of suggestions
                content = "[ MAINTENANCE SUGGESTIONS ]\n\n"

                if suggestions:
                    for sugg in suggestions:
                        content += f"🏎️  {sugg.car_label} ({sugg.priority.upper()})\n"
                        for action in sugg.suggested_actions:
                            content += f"   • {action}\n"
                        content += f"\n   Reasoning: {sugg.reasoning}\n\n"
                else:
                    content += "No suggestions available."

                section.update(content)

        except Exception as e:
            section.update(f"[ ERROR ] {str(e)}", classes="ai-error")

    def _load_track_prep(self, section: Static) -> None:
        """Load and display track prep checklist.

        Args:
            section: The widget to display checklist in.
        """
        try:
            checklist = self.ai_service.get_track_prep_checklist(self.car_id)

            if isinstance(checklist, str):
                # Error message
                content = f"[ TRACK DAY PREP ]\n\n{checklist}"
                section.update(content, classes="ai-error")
            else:
                # Checklist object
                content = f"[ TRACK DAY PREP: {checklist.car_label} ]\n\n"

                if checklist.critical_items:
                    content += "❗ CRITICAL ITEMS\n"
                    for item in checklist.critical_items:
                        content += f"  ☐ {item}\n"
                    content += "\n"

                if checklist.recommended_items:
                    content += "⚙️  RECOMMENDED ITEMS\n"
                    for item in checklist.recommended_items:
                        content += f"  ☐ {item}\n"
                    content += "\n"

                if checklist.notes:
                    content += f"📝 NOTES\n{checklist.notes}\n"

                section.update(content)

        except Exception as e:
            section.update(f"[ ERROR ] {str(e)}", classes="ai-error")

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh AI data."""
        self.load_ai_data()

    def action_help(self) -> None:
        """Show help screen."""
        self.app.action_help()

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
        self.ai_service.close()
