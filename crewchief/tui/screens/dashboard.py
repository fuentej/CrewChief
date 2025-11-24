"""Dashboard screen - main garage view with vehicles and stats."""

from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Label
from textual.binding import Binding

from crewchief.tui.widgets import ASCIIBanner
from crewchief.tui.widgets.vehicle_table import VehicleTable
from crewchief.tui.widgets.stats_panel import StatsPanel
from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.services.garage_service import GarageService


class DashboardScreen(Screen):
    """Main dashboard screen showing garage overview."""

    DEFAULT_CSS = """
    DashboardScreen {
        layout: vertical;
    }

    #banner {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    #main-content {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    #left-panel {
        width: 50%;
        height: 1fr;
        layout: vertical;
        border: solid $primary;
        background: $panel;
    }

    #left-panel > #vehicles-header {
        width: 100%;
        height: 1;
        background: $boost;
        color: $secondary;
        text-style: bold;
    }

    #vehicle-table {
        width: 100%;
        height: 1fr;
    }

    #right-panel {
        width: 50%;
        height: 1fr;
        layout: vertical;
        border: solid $primary;
        background: $panel;
    }

    #stats-panel {
        width: 100%;
        height: auto;
        margin: 1 0;
    }

    #recent-section {
        width: 100%;
        height: 1fr;
        border-top: solid $primary;
        margin-top: 1;
        padding-top: 1;
    }

    #recent-section > #recent-header {
        width: 100%;
        height: 1;
        background: $boost;
        color: $secondary;
        text-style: bold;
    }

    #recent-events {
        width: 100%;
        height: 1fr;
        overflow: auto;
    }

    .recent-event {
        width: 100%;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help"),
        Binding("v", "view_vehicle", "View Vehicle"),
    ]

    def __init__(self, **kwargs):
        """Initialize dashboard screen."""
        super().__init__(**kwargs)
        self.garage_service = GarageService()
        self.vehicle_table: VehicleTable | None = None
        self.stats_panel: StatsPanel | None = None
        self.recent_events: Static | None = None
        self.help_footer: HelpFooter | None = None

    def compose(self):
        """Compose dashboard layout."""
        yield ASCIIBanner(id="banner")

        with Container(id="main-content"):
            # Left panel: Vehicle list
            with Vertical(id="left-panel"):
                yield Label("[ GARAGE FLEET ]", id="vehicles-header")
                yield VehicleTable(id="vehicle-table")

            # Right panel: Stats and recent activity
            with Vertical(id="right-panel"):
                yield StatsPanel(title="SYSTEM STATUS", id="stats-panel")

                with Vertical(id="recent-section"):
                    yield Label("[ RECENT ACTIVITY ]", id="recent-header")
                    yield Static(id="recent-events")

        yield HelpFooter(
            help_text=" [V]iew Vehicle  [?]Help  [Q]uit",
            id="help-footer",
        )

    def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.load_data()

    def load_data(self) -> None:
        """Load garage data and populate widgets."""
        # Load vehicles
        vehicles = self.garage_service.get_all_vehicles()

        self.vehicle_table = self.query_one("#vehicle-table", VehicleTable)
        self.vehicle_table.setup_table()
        self.vehicle_table.populate_vehicles(vehicles)

        # Load stats
        stats = self.garage_service.get_garage_stats()

        self.stats_panel = self.query_one("#stats-panel", StatsPanel)
        self.stats_panel.set_stats({
            "Total Vehicles": stats["total_vehicles"],
            "Maintenance Events": stats["total_maintenance_events"],
            "Parts Tracked": stats["total_parts"],
            "AI Service": "● ONLINE" if True else "⚠ OFFLINE",
            "Database": "● HEALTHY",
        })

        # Load recent events
        from crewchief.tui.services.maintenance_service import MaintenanceService
        maint_service = MaintenanceService()
        recent = maint_service.get_recent_events(limit=5)

        events_text = ""
        for event in recent:
            car = self.garage_service.get_vehicle(event.car_id)
            if car:
                events_text += f"{event.service_date}  {car.display_name():<30} {event.service_type.value:<20} ${event.cost or 0:.2f}\n"

        self.recent_events = self.query_one("#recent-events", Static)
        self.recent_events.update(events_text if events_text else "No maintenance events yet.")

        maint_service.close()

    def action_view_vehicle(self) -> None:
        """View selected vehicle details."""
        if self.vehicle_table:
            car_id = self.vehicle_table.get_selected_car_id()
            if car_id:
                self.app.post_message(self.app.VehicleSelected(car_id=car_id))

    def action_help(self) -> None:
        """Show help overlay."""
        # Placeholder - implement help modal in later phase
        pass

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
