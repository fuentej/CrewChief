"""Dashboard screen - main garage view with vehicles and stats."""

from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Label
from textual.binding import Binding

from crewchief.models import Car
from crewchief.tui.widgets import ASCIIBanner
from crewchief.tui.widgets.vehicle_table import VehicleTable
from crewchief.tui.widgets.stats_panel import StatsPanel
from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.services.garage_service import GarageService
from crewchief.tui.screens.vehicle_detail import VehicleDetailScreen
from crewchief.tui.screens.costs_view import CostsViewScreen
from crewchief.tui.screens.ai_panel import AIPanelScreen
from crewchief.tui.screens.car_form import CarFormModal
from crewchief.tui.screens.modals import ConfirmDeleteModal


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

    #vehicles-section {
        width: 100%;
        height: 60%;
        layout: vertical;
        border-bottom: solid $primary;
        padding-bottom: 1;
    }

    #vehicles-section > #vehicles-header {
        width: 100%;
        height: 1;
        background: $boost;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    #vehicle-table {
        width: 100%;
        height: 1fr;
    }

    #status-section {
        width: 100%;
        height: 40%;
        layout: vertical;
        padding: 1;
    }

    #status-section > #status-header {
        width: 100%;
        height: 1;
        background: $boost;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    #stats-panel {
        width: 100%;
        height: auto;
    }

    #right-panel {
        width: 50%;
        height: 1fr;
        layout: vertical;
        border: solid $primary;
        background: $panel;
    }

    #maintenance-section {
        width: 100%;
        height: 1fr;
        layout: vertical;
        padding: 1;
    }

    #maintenance-section > #maintenance-header {
        width: 100%;
        height: 1;
        background: $boost;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    #maintenance-log {
        width: 100%;
        height: 1fr;
        overflow: auto;
    }

    .maintenance-entry {
        width: 100%;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("n", "new_vehicle", "New Car"),
        Binding("v", "view_vehicle", "View Car"),
        Binding("e", "edit_vehicle", "Edit Car"),
        Binding("d", "delete_vehicle", "Delete Car"),
        Binding("c", "view_costs", "Costs"),
        Binding("a", "view_ai", "AI Insights"),
        Binding("?", "help", "Help"),
        Binding("q", "quit", "Quit"),
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
        yield ASCIIBanner(subtitle="THE GARAGE", subtitle_align="center", id="banner")

        with Container(id="main-content"):
            # Left panel: Vehicle list and system status
            with Vertical(id="left-panel"):
                # Vehicles section
                with Vertical(id="vehicles-section"):
                    yield Static("[ GARAGE FLEET ]", id="vehicles-header")
                    yield VehicleTable(id="vehicle-table")

                # Status section
                with Vertical(id="status-section"):
                    yield Static("[ SYSTEM STATUS ]", id="status-header")
                    yield StatsPanel(id="stats-panel")

            # Right panel: Maintenance log for all cars
            with Vertical(id="right-panel"):
                with Vertical(id="maintenance-section"):
                    yield Static("[ MAINTENANCE LOG ]", id="maintenance-header")
                    yield Static(id="maintenance-log")

        yield HelpFooter(
            help_text=" [N]ew  [V]iew  [E]dit  [D]elete  [C]osts  [A]I  [?]Help  [Q]uit",
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

        # Load maintenance log for all cars
        from crewchief.tui.services.maintenance_service import MaintenanceService
        maint_service = MaintenanceService()
        all_events = maint_service.get_recent_events(limit=1000)

        log_text = ""
        if all_events:
            for event in all_events:
                car = self.garage_service.get_vehicle(event.car_id)
                if car:
                    log_text += f"{event.service_date}  {car.display_name():<25} {event.service_type.value:<15} ${event.cost or 0:.2f}\n"
        else:
            log_text = "No maintenance events yet."

        maintenance_log = self.query_one("#maintenance-log", Static)
        maintenance_log.update(log_text)

        maint_service.close()

    def action_new_vehicle(self) -> None:
        """Create a new vehicle."""
        def handle_form_result(form_data: dict) -> None:
            """Handle form submission."""
            if form_data:
                try:
                    car = Car(**form_data)
                    result = self.garage_service.add_vehicle(car)
                    self.notify("Vehicle added to garage", timeout=2)
                    self.load_data()
                except Exception as e:
                    self.notify(f"Error adding vehicle: {str(e)}", timeout=3)

        self.app.push_screen(CarFormModal(), callback=handle_form_result)

    def action_view_vehicle(self) -> None:
        """View selected vehicle details."""
        if self.vehicle_table:
            car_id = self.vehicle_table.get_selected_car_id()
            if car_id:
                self.app.push_screen(VehicleDetailScreen(car_id=car_id))

    def action_edit_vehicle(self) -> None:
        """Edit selected vehicle."""
        if self.vehicle_table:
            car_id = self.vehicle_table.get_selected_car_id()
            if car_id:
                car = self.garage_service.get_vehicle(car_id)
                if car:
                    def handle_form_result(form_data: dict) -> None:
                        """Handle form submission."""
                        if form_data:
                            try:
                                self.garage_service.update_vehicle(car_id, **form_data)
                                self.notify("Vehicle updated", timeout=2)
                                self.load_data()
                            except Exception as e:
                                self.notify(f"Error updating vehicle: {str(e)}", timeout=3)

                    self.app.push_screen(
                        CarFormModal(car),
                        callback=handle_form_result,
                    )

    def action_delete_vehicle(self) -> None:
        """Delete selected vehicle."""
        if self.vehicle_table:
            car_id = self.vehicle_table.get_selected_car_id()
            if car_id:
                car = self.garage_service.get_vehicle(car_id)
                if car:
                    def handle_confirm(confirmed: bool) -> None:
                        """Handle delete confirmation."""
                        if confirmed:
                            try:
                                self.garage_service.delete_vehicle(car_id)
                                self.notify(f"Deleted {car.display_name()}", timeout=2)
                                self.load_data()
                            except Exception as e:
                                self.notify(f"Error deleting vehicle: {str(e)}", timeout=3)

                    self.app.push_screen(
                        ConfirmDeleteModal(
                            "Delete Vehicle",
                            f"Delete {car.display_name()}?\nThis cannot be undone.",
                        ),
                        callback=handle_confirm,
                    )

    def action_view_costs(self) -> None:
        """View cost analytics for all vehicles."""
        self.app.push_screen(CostsViewScreen())

    def action_view_ai(self) -> None:
        """View AI insights for the garage."""
        self.app.push_screen(AIPanelScreen())

    def action_help(self) -> None:
        """Show help screen."""
        self.app.action_help()

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
