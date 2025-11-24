"""Vehicle table widget - displays list of vehicles with status."""

from textual.widgets import DataTable
from textual.binding import Binding
from crewchief.models import Car


class VehicleTable(DataTable):
    """DataTable subclass for displaying vehicles with status indicators."""

    DEFAULT_CSS = """
    VehicleTable {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }

    VehicleTable > .datatable--cursor {
        background: $accent;
        color: $surface;
    }

    VehicleTable > .datatable--header {
        background: $boost;
        color: $primary;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("enter", "select_vehicle", "Select"),
    ]

    def __init__(self, **kwargs):
        """Initialize vehicle table."""
        super().__init__(**kwargs)
        self.vehicles: list[Car] = []

    def setup_table(self) -> None:
        """Set up table columns."""
        self.add_columns("ID", "Vehicle", "Usage", "Odometer", "Status")

    def populate_vehicles(self, vehicles: list[Car]) -> None:
        """Populate table with vehicles.

        Args:
            vehicles: List of Car objects to display.
        """
        self.vehicles = vehicles
        self.clear()

        for car in vehicles:
            # Determine status badge
            status = "● READY"  # Default - would check due services in real implementation

            odometer_str = f"{car.current_odometer:,} mi" if car.current_odometer else "—"

            self.add_row(
                str(car.id),
                car.display_name(),
                car.usage_type.value.upper(),
                odometer_str,
                status,
            )

    def get_selected_car_id(self) -> int | None:
        """Get ID of currently selected car.

        Returns:
            Car ID if selected, None otherwise.
        """
        if not self.vehicles:
            return None

        cursor_row = self.cursor_row
        if 0 <= cursor_row < len(self.vehicles):
            return self.vehicles[cursor_row].id

        return None
