"""Vehicle detail screen - shows detailed info for a selected vehicle."""

from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Label, Button
from textual.binding import Binding

from crewchief.tui.widgets.maintenance_table import MaintenanceTable
from crewchief.tui.widgets.stats_panel import StatsPanel
from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.widgets.ascii_banner import ASCIIBanner
from crewchief.tui.services.garage_service import GarageService
from crewchief.tui.services.maintenance_service import MaintenanceService
from crewchief.tui.screens.maintenance_log import MaintenanceLogScreen
from crewchief.tui.screens.parts_manager import PartsManagerScreen
from crewchief.tui.screens.costs_view import CostsViewScreen
from crewchief.tui.screens.ai_panel import AIPanelScreen


class VehicleDetailScreen(Screen):
    """Screen showing detailed info for a specific vehicle."""

    DEFAULT_CSS = """
    VehicleDetailScreen {
        layout: vertical;
    }

    #header-section {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $boost;
        padding: 1;
    }

    #vehicle-info {
        width: 100%;
        height: auto;
    }

    #vehicle-title {
        color: $secondary;
        text-style: bold;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }

    #vehicle-details {
        width: 100%;
        height: auto;
        color: $text;
    }

    #content-area {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    #left-content {
        width: 50%;
        height: 1fr;
        layout: vertical;
        border: solid $primary;
        background: $panel;
    }

    #left-header {
        width: 100%;
        height: 1;
        background: $boost;
        color: $secondary;
        text-style: bold;
    }

    #maintenance-table {
        width: 100%;
        height: 1fr;
    }

    #right-content {
        width: 50%;
        height: 1fr;
        layout: vertical;
        border: solid $primary;
        background: $panel;
        padding: 1 1;
    }

    #right-header {
        width: 100%;
        height: 1;
        background: $boost;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    .due-item {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    #event-detail {
        width: 100%;
        height: 1fr;
        border-top: solid $primary;
        margin-top: 1;
        padding-top: 1;
        overflow: auto;
    }
    """

    BINDINGS = [
        Binding("v", "view_details", "View Car"),
        Binding("l", "view_log", "View Log"),
        Binding("p", "view_parts", "View Parts"),
        Binding("c", "view_costs", "Costs"),
        Binding("a", "view_ai", "AI Insights"),
        Binding("enter", "view_event", "View Event"),
        Binding("?", "help", "Help"),
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, car_id: int, **kwargs):
        """Initialize vehicle detail screen.

        Args:
            car_id: The vehicle ID to display.
        """
        super().__init__(**kwargs)
        self.car_id = car_id
        self.garage_service = GarageService()
        self.maintenance_service = MaintenanceService()
        self.maintenance_table: MaintenanceTable | None = None
        self.due_panel: Static | None = None
        self.event_detail: Static | None = None

    def compose(self):
        """Compose vehicle detail layout."""
        yield ASCIIBanner(subtitle="THE CAR LIFT", id="banner")

        # Header with vehicle info
        with Container(id="header-section"):
            with Container(id="vehicle-info"):
                yield Label("", id="vehicle-title")
                yield Static("", id="vehicle-details")

        # Main content: maintenance table + due services
        with Container(id="content-area"):
            # Left: Maintenance history
            with Vertical(id="left-content"):
                yield Label("[ MAINTENANCE HISTORY ]", id="left-header")
                yield MaintenanceTable(id="maintenance-table")

            # Right: Due services + parts
            with Vertical(id="right-content"):
                yield Label("[ DUE SERVICES & PARTS ]", id="right-header")
                yield Static("", id="due-services")

        # Bottom: Selected event detail
        yield Static("", id="event-detail")

        yield HelpFooter(
            help_text=" [↑↓]Select  [L]og  [P]arts  [C]osts  [A]I  [Enter]View  [Esc]Back",
            id="help-footer",
        )

    def on_mount(self) -> None:
        """Load vehicle data when screen mounts."""
        self.load_vehicle_data()

    def load_vehicle_data(self) -> None:
        """Load and display vehicle data."""
        vehicle_stats = self.garage_service.get_vehicle_with_stats(self.car_id)
        if not vehicle_stats:
            self.dismiss()
            return

        car = vehicle_stats["car"]
        events = vehicle_stats["events"]
        due_services = vehicle_stats["due_services"]
        parts = vehicle_stats["parts"]

        # Update header
        title = self.query_one("#vehicle-title", Label)
        title.update(f"◄ {car.display_name()}")

        details = self.query_one("#vehicle-details", Static)
        details_text = (
            f"Year: {car.year}  |  Make: {car.make}  |  Model: {car.model}  |  Usage: {car.usage_type.value.upper()}\n"
            f"VIN: {car.vin or '—'}  |  Odometer: {car.current_odometer or '—'}"
        )
        details.update(details_text)

        # Load maintenance history
        self.maintenance_table = self.query_one("#maintenance-table", MaintenanceTable)
        self.maintenance_table.setup_table()
        self.maintenance_table.populate_events(events)

        # Load due services
        due_text = ""
        if due_services:
            for service in due_services:
                is_due = service.get("is_due", False)
                status = "⚠ OVERDUE" if is_due else "● OK"
                due_text += f"{status}  {service['service_type']}\n"
        else:
            due_text = "No due services tracked."

        # Load parts
        if parts:
            due_text += "\nParts Profile:\n"
            for part in parts:
                due_text += f"  • {part.part_category.value}: {part.brand or '—'}\n"

        due_panel = self.query_one("#due-services", Static)
        due_panel.update(due_text)

    def action_back(self) -> None:
        """Go back to dashboard."""
        self.app.pop_screen()

    def action_view_details(self) -> None:
        """View detailed car information."""
        car = self.garage_service.get_vehicle(self.car_id)
        if car:
            info = f"{car.display_name()}\n\nYear: {car.year}\nMake: {car.make}\nModel: {car.model}\nTrim: {car.trim or '—'}\nVIN: {car.vin or '—'}\nUsage: {car.usage_type.value}\nOdometer: {car.current_odometer:,} mi\nNotes: {car.notes or '—'}"
            self.notify(info, timeout=5)

    def action_view_log(self) -> None:
        """Open full maintenance log for this vehicle."""
        self.app.push_screen(MaintenanceLogScreen(car_id=self.car_id))

    def action_view_parts(self) -> None:
        """Open parts manager for this vehicle."""
        self.app.push_screen(PartsManagerScreen(car_id=self.car_id))

    def action_view_costs(self) -> None:
        """Open cost analytics for this vehicle."""
        self.app.push_screen(CostsViewScreen(car_id=self.car_id))

    def action_view_ai(self) -> None:
        """Open AI insights for this vehicle."""
        self.app.push_screen(AIPanelScreen(car_id=self.car_id))

    def action_view_event(self) -> None:
        """View selected event details."""
        if self.maintenance_table:
            event = self.maintenance_table.get_selected_event()
            if event:
                detail_text = (
                    f"Date: {event.service_date}  |  Type: {event.service_type.value}\n"
                    f"Odometer: {event.odometer or '—'} mi  |  Cost: ${event.cost or 0:.2f}\n"
                    f"Location: {event.location or '—'}\n\n"
                    f"Description:\n{event.description or 'No description'}\n\n"
                    f"Parts: {event.parts or 'No parts recorded'}"
                )
                detail = self.query_one("#event-detail", Static)
                detail.update(detail_text)

    def action_help(self) -> None:
        """Show help screen."""
        self.app.action_help()

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
        self.maintenance_service.close()
