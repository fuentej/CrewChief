"""Vehicle table widget - displays list of vehicles with status."""

from textual.widgets import DataTable
from textual.binding import Binding
from rich.text import Text
from crewchief.models import Car
from crewchief.tui.services.garage_service import GarageService


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
        super().__init__(cursor_type="row", **kwargs)
        self.vehicles: list[Car] = []
        self.garage_service = GarageService()

    def setup_table(self) -> None:
        """Set up table columns."""
        self.add_columns("ID", "Vehicle", "Usage", "Odometer", "Status")

    def _determine_status(self, car: Car) -> Text:
        """Determine vehicle status based on due services.

        Args:
            car: Car object to check status for.

        Returns:
            Rich Text object with colored status.
        """
        try:
            # Check for due services
            vehicle_stats = self.garage_service.get_vehicle_with_stats(car.id)
            if vehicle_stats and vehicle_stats.get("due_services"):
                due_services = vehicle_stats["due_services"]
                has_overdue = any(service.get("is_due", False) for service in due_services)
                if has_overdue:
                    return Text("✗ OVERDUE", style="bold red")
                else:
                    return Text("⚠ DUE", style="bold yellow")
            return Text("● OK", style="bold green")
        except Exception:
            # Default status if service check fails
            return Text("● OK", style="bold green")

    def populate_vehicles(self, vehicles: list[Car]) -> None:
        """Populate table with vehicles.

        Args:
            vehicles: List of Car objects to display.
        """
        self.vehicles = vehicles

        # Clear existing rows and columns
        self.clear()

        for car in vehicles:
            # Determine status based on due services
            status = self._determine_status(car)

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
