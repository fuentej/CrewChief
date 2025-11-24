"""Maintenance table widget - displays service history."""

from textual.widgets import DataTable
from crewchief.models import MaintenanceEvent


class MaintenanceTable(DataTable):
    """DataTable subclass for displaying maintenance history."""

    DEFAULT_CSS = """
    MaintenanceTable {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }

    MaintenanceTable > .datatable--cursor {
        background: $accent;
        color: $surface;
    }

    MaintenanceTable > .datatable--header {
        background: $boost;
        color: $primary;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs):
        """Initialize maintenance table."""
        super().__init__(**kwargs)
        self.events: list[MaintenanceEvent] = []

    def setup_table(self) -> None:
        """Set up table columns."""
        self.add_columns("Date", "Service Type", "Odometer", "Cost", "Description")

    def populate_events(self, events: list[MaintenanceEvent]) -> None:
        """Populate table with maintenance events.

        Args:
            events: List of MaintenanceEvent objects to display.
        """
        self.events = events
        self.clear()

        for event in events:
            odometer_str = f"{event.odometer:,} mi" if event.odometer else "—"
            cost_str = f"${event.cost:.2f}" if event.cost else "—"
            description = (event.description or "")[:40]

            self.add_row(
                str(event.service_date),
                event.service_type.value.replace("_", " ").title(),
                odometer_str,
                cost_str,
                description,
            )

    def get_selected_event(self) -> MaintenanceEvent | None:
        """Get currently selected event.

        Returns:
            MaintenanceEvent if selected, None otherwise.
        """
        if not self.events:
            return None

        cursor_row = self.cursor_row
        if 0 <= cursor_row < len(self.events):
            return self.events[cursor_row]

        return None
