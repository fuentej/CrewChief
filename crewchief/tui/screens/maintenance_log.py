"""Maintenance log screen - full CRUD for maintenance events."""

from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Label, Button
from textual.binding import Binding

from crewchief.models import MaintenanceEvent
from crewchief.tui.widgets.maintenance_table import MaintenanceTable
from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.services.maintenance_service import MaintenanceService
from crewchief.tui.services.garage_service import GarageService
from crewchief.tui.screens.maintenance_form import MaintenanceEventFormModal
from crewchief.tui.screens.modals import ConfirmDeleteModal


class MaintenanceLogScreen(Screen):
    """Screen showing maintenance log for a specific vehicle."""

    DEFAULT_CSS = """
    MaintenanceLogScreen {
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

    #maintenance-table {
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
        Binding("n", "new_entry", "New Entry"),
        Binding("e", "edit_entry", "Edit"),
        Binding("d", "delete_entry", "Delete"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, car_id: int, **kwargs):
        """Initialize maintenance log screen.

        Args:
            car_id: The vehicle ID to show maintenance log for.
        """
        super().__init__(**kwargs)
        self.car_id = car_id
        self.garage_service = GarageService()
        self.maintenance_service = MaintenanceService()
        self.maintenance_table: MaintenanceTable | None = None
        self.detail_content: Static | None = None

    def compose(self):
        """Compose maintenance log layout."""
        with Container(id="header"):
            yield Label("[ MAINTENANCE LOG ]", id="title")

        yield MaintenanceTable(id="maintenance-table")

        with Container(id="detail-section"):
            yield Label("[ EVENT DETAILS ]", id="detail-header")
            yield Static("Select an entry to view details", id="detail-content")

        yield HelpFooter(
            help_text=" [↑↓]Select  [N]ew  [E]dit  [D]elete  [Esc]Back  [?]Help",
            id="help-footer",
        )

    def on_mount(self) -> None:
        """Load maintenance data when screen mounts."""
        self.load_maintenance_data()

    def load_maintenance_data(self) -> None:
        """Load and display maintenance events for the vehicle."""
        car = self.garage_service.get_vehicle(self.car_id)
        if not car:
            self.dismiss()
            return

        # Update title
        title = self.query_one("#title", Label)
        title.update(f"[ MAINTENANCE LOG: {car.display_name()} ]")

        # Load events
        events = self.maintenance_service.get_events_for_car(self.car_id)
        self.maintenance_table = self.query_one("#maintenance-table", MaintenanceTable)
        self.maintenance_table.setup_table()
        self.maintenance_table.populate_events(events)

        self.detail_content = self.query_one("#detail-content", Static)

    def on_data_table_row_selected(self) -> None:
        """Update detail pane when row selected."""
        if self.maintenance_table:
            event = self.maintenance_table.get_selected_event()
            if event:
                detail_text = (
                    f"Date: {event.service_date}  |  Service Type: {event.service_type.value}\n"
                    f"Odometer: {event.odometer or '—'} mi  |  Cost: ${event.cost or 0:.2f}\n"
                    f"Location: {event.location or '—'}\n\n"
                    f"Description:\n{event.description or 'No description'}\n\n"
                    f"Parts: {event.parts or 'No parts recorded'}"
                )
                self.detail_content.update(detail_text)

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_new_entry(self) -> None:
        """Create a new maintenance entry."""
        self.notify("Coming soon", timeout=2)

    def action_edit_entry(self) -> None:
        """Edit selected maintenance entry."""
        self.notify("Coming soon", timeout=2)

    def action_delete_entry(self) -> None:
        """Delete selected maintenance entry."""
        self.notify("Coming soon", timeout=2)

    def action_help(self) -> None:
        """Show help screen."""
        self.app.action_help()

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
        self.maintenance_service.close()
