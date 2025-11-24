"""Parts manager screen - manage vehicle parts profile."""

from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Label
from textual.binding import Binding

from crewchief.tui.widgets.parts_table import PartsTable
from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.services.parts_service import PartsService
from crewchief.tui.services.garage_service import GarageService


class PartsManagerScreen(Screen):
    """Screen for managing vehicle parts profile."""

    DEFAULT_CSS = """
    PartsManagerScreen {
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
        margin-bottom: 1;
    }

    #parts-table {
        width: 100%;
        height: 1fr;
        border: solid $primary;
    }

    #detail-section {
        width: 100%;
        height: auto;
        border-top: solid $primary;
        padding: 1;
        background: $panel;
    }

    #detail-header {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    #detail-content {
        width: 100%;
        height: auto;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("n", "new_part", "New Part"),
        Binding("e", "edit_part", "Edit"),
        Binding("d", "delete_part", "Delete"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, car_id: int, **kwargs):
        """Initialize parts manager screen.

        Args:
            car_id: The vehicle ID to manage parts for.
        """
        super().__init__(**kwargs)
        self.car_id = car_id
        self.garage_service = GarageService()
        self.parts_service = PartsService()
        self.parts_table: PartsTable | None = None
        self.detail_content: Static | None = None

    def compose(self):
        """Compose parts manager layout."""
        with Container(id="header"):
            yield Label("[ PARTS PROFILE ]", id="title")

        yield PartsTable(id="parts-table")

        with Container(id="detail-section"):
            yield Label("[ PART DETAILS ]", id="detail-header")
            yield Static("Select a part to view details", id="detail-content")

        yield HelpFooter(
            help_text=" [↑↓]Select  [N]ew  [E]dit  [D]elete  [Esc]Back  [?]Help",
            id="help-footer",
        )

    def on_mount(self) -> None:
        """Load parts data when screen mounts."""
        self.load_parts_data()

    def load_parts_data(self) -> None:
        """Load and display parts for the vehicle."""
        car = self.garage_service.get_vehicle(self.car_id)
        if not car:
            self.dismiss()
            return

        # Update title
        title = self.query_one("#title", Label)
        title.update(f"[ PARTS PROFILE: {car.display_name()} ]")

        # Load parts
        parts = self.parts_service.get_parts_for_car(self.car_id)
        self.parts_table = self.query_one("#parts-table", PartsTable)
        self.parts_table.setup_table()
        self.parts_table.populate_parts(parts)

        self.detail_content = self.query_one("#detail-content", Static)

    def on_data_table_row_selected(self) -> None:
        """Update detail pane when row selected."""
        if self.parts_table:
            part = self.parts_table.get_selected_part()
            if part:
                detail_text = (
                    f"Category: {part.part_category.value.replace('_', ' ').title()}\n"
                    f"Brand: {part.brand or '—'}\n"
                    f"Part Number: {part.part_number or '—'}\n"
                    f"Size/Spec: {part.size_spec or '—'}\n\n"
                    f"Notes: {part.notes or 'No notes'}"
                )
                self.detail_content.update(detail_text)

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_new_part(self) -> None:
        """Add a new part to the profile."""
        # Placeholder - form modal coming in extended phase
        self.notify("New part form - coming soon", timeout=3)

    def action_edit_part(self) -> None:
        """Edit selected part."""
        if self.parts_table:
            part = self.parts_table.get_selected_part()
            if part:
                self.notify(f"Edit part {part.id} - coming soon", timeout=3)

    def action_delete_part(self) -> None:
        """Delete selected part."""
        if self.parts_table:
            part = self.parts_table.get_selected_part()
            if part:
                self.notify(f"Delete part {part.id} - coming soon", timeout=3)

    def action_help(self) -> None:
        """Show help screen."""
        self.app.action_help()

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
        self.parts_service.close()
