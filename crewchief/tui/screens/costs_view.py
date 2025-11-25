"""Costs view screen - cost analytics and breakdowns."""

from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Label
from textual.binding import Binding

from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.services.garage_service import GarageService


class CostsViewScreen(Screen):
    """Screen showing cost analytics and breakdowns."""

    DEFAULT_CSS = """
    CostsViewScreen {
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
        layout: horizontal;
    }

    #left-panel {
        width: 50%;
        height: 1fr;
        layout: vertical;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }

    #right-panel {
        width: 50%;
        height: 1fr;
        layout: vertical;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }

    .section-header {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    .cost-content {
        width: 100%;
        height: auto;
        color: $text;
        margin-bottom: 2;
    }

    .cost-bar {
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, car_id: int | None = None, **kwargs):
        """Initialize costs view screen.

        Args:
            car_id: If provided, show costs for specific vehicle. Otherwise, show all.
        """
        super().__init__(**kwargs)
        self.car_id = car_id
        self.garage_service = GarageService()

    def compose(self):
        """Compose costs view layout."""
        with Container(id="header"):
            yield Label("[ COST ANALYSIS ]", id="title")

        with Container(id="content-area"):
            # Left panel: Cost by vehicle
            with Vertical(id="left-panel"):
                yield Label("[ COSTS BY VEHICLE ]", classes="section-header")
                yield Static("", id="vehicle-costs", classes="cost-content")

            # Right panel: Cost by service type + cost per mile
            with Vertical(id="right-panel"):
                yield Label("[ COSTS BY SERVICE TYPE ]", classes="section-header")
                yield Static("", id="service-costs", classes="cost-content")

                yield Label("[ COST PER MILE ]", classes="section-header")
                yield Static("", id="cost-per-mile", classes="cost-content")

        yield HelpFooter(
            help_text=" [Esc]Back  [?]Help",
            id="help-footer",
        )

    def on_mount(self) -> None:
        """Load cost data when screen mounts."""
        self.load_cost_data()

    def load_cost_data(self) -> None:
        """Load and display cost analytics."""
        if self.car_id is not None:
            # Single vehicle costs
            self._load_single_vehicle_costs()
        else:
            # All vehicles costs
            self._load_all_vehicles_costs()

    def _load_single_vehicle_costs(self) -> None:
        """Load costs for a single vehicle."""
        car = self.garage_service.get_vehicle(self.car_id)
        if not car:
            self.dismiss()
            return

        # Update title with page name right-justified
        title = self.query_one("#title", Label)
        cost_text = f"[ COST ANALYSIS: {car.display_name()} ]"
        page_title = "COST LEDGER"
        padding = " " * (70 - len(cost_text) - len(page_title))
        title.update(f"{cost_text}{padding}{page_title}")

        # Get cost data from repository
        costs = self.garage_service.repo.get_maintenance_costs(self.car_id)
        car_costs = costs.get(self.car_id, {})

        # Display vehicle total
        vehicle_costs_widget = self.query_one("#vehicle-costs", Static)
        total = car_costs.get("total", 0.0)
        count = car_costs.get("count", 0)
        vehicle_text = f"{car.display_name()}\n"
        vehicle_text += f"  Total Spent: ${total:,.2f}\n"
        vehicle_text += f"  Events: {count}\n"
        vehicle_text += self._make_bar(total, total, width=40)
        vehicle_costs_widget.update(vehicle_text)

        # Display costs by service type
        service_costs_widget = self.query_one("#service-costs", Static)
        by_type = car_costs.get("by_type", {})

        if by_type:
            service_text = ""
            max_cost = max(by_type.values()) if by_type else 1.0

            for service_type in sorted(by_type.keys(), key=lambda k: by_type[k], reverse=True):
                cost = by_type[service_type]
                service_text += f"{service_type.replace('_', ' ').title():<20} ${cost:>9,.2f}\n"
                service_text += self._make_bar(cost, max_cost, width=30) + "\n"
        else:
            service_text = "No cost data available."

        service_costs_widget.update(service_text)

        # Display cost per mile
        cpm_widget = self.query_one("#cost-per-mile", Static)
        cpm_data = self.garage_service.repo.get_cost_per_mile(self.car_id)

        if cpm_data and cpm_data.get("cost_per_mile"):
            cpm_text = f"Total Cost:        ${cpm_data['total_cost']:,.2f}\n"
            cpm_text += f"Total Miles:       {cpm_data['total_miles']:,}\n"
            cpm_text += f"Cost per Mile:     ${cpm_data['cost_per_mile']:.3f}\n"
        else:
            cpm_text = "Insufficient data for cost per mile calculation."

        cpm_widget.update(cpm_text)

    def _load_all_vehicles_costs(self) -> None:
        """Load costs for all vehicles."""
        cars = self.garage_service.get_all_vehicles()
        if not cars:
            self.dismiss()
            return

        # Get cost data for all vehicles
        costs = self.garage_service.repo.get_maintenance_costs(None)

        # Display costs by vehicle
        vehicle_costs_widget = self.query_one("#vehicle-costs", Static)

        if costs:
            vehicle_text = ""
            # Calculate max for bar chart scaling
            max_cost = max((data.get("total", 0) for data in costs.values()), default=1.0)

            # Sort by total cost descending
            sorted_cars = sorted(costs.items(), key=lambda x: x[1].get("total", 0), reverse=True)

            for car_id, car_data in sorted_cars:
                car = self.garage_service.get_vehicle(car_id)
                if car:
                    total = car_data.get("total", 0.0)
                    count = car_data.get("count", 0)
                    vehicle_text += f"{car.display_name():<30} ${total:>9,.2f} ({count} events)\n"
                    vehicle_text += self._make_bar(total, max_cost, width=40) + "\n"
        else:
            vehicle_text = "No cost data available."

        vehicle_costs_widget.update(vehicle_text)

        # Display aggregate costs by service type
        service_costs_widget = self.query_one("#service-costs", Static)

        # Aggregate by service type across all vehicles
        service_totals = {}
        for car_data in costs.values():
            by_type = car_data.get("by_type", {})
            for service_type, cost in by_type.items():
                service_totals[service_type] = service_totals.get(service_type, 0) + cost

        if service_totals:
            service_text = ""
            max_cost = max(service_totals.values()) if service_totals else 1.0

            for service_type in sorted(service_totals.keys(), key=lambda k: service_totals[k], reverse=True):
                cost = service_totals[service_type]
                service_text += f"{service_type.replace('_', ' ').title():<20} ${cost:>9,.2f}\n"
                service_text += self._make_bar(cost, max_cost, width=30) + "\n"
        else:
            service_text = "No cost data available."

        service_costs_widget.update(service_text)

        # Display cost per mile for all vehicles
        cpm_widget = self.query_one("#cost-per-mile", Static)
        cpm_text = ""

        for car in cars:
            cpm_data = self.garage_service.repo.get_cost_per_mile(car.id)
            if cpm_data and cpm_data.get("cost_per_mile"):
                cpm_text += f"{car.display_name():<30} ${cpm_data['cost_per_mile']:.3f}/mi\n"

        if not cpm_text:
            cpm_text = "Insufficient data for cost per mile calculations."

        cpm_widget.update(cpm_text)

    def _make_bar(self, value: float, max_value: float, width: int = 40) -> str:
        """Create an ASCII bar chart.

        Args:
            value: The value to display.
            max_value: The maximum value for scaling.
            width: Width of the bar in characters.

        Returns:
            ASCII bar string.
        """
        if max_value == 0:
            filled = 0
        else:
            filled = int((value / max_value) * width)

        bar = "█" * filled + "░" * (width - filled)
        return f"  {bar}"

    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_help(self) -> None:
        """Show help screen."""
        self.app.action_help()

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
