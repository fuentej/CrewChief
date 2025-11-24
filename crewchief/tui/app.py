"""CrewChief TUI - Mainframe-style Terminal User Interface for garage management.

Entry point: crewchief-tui
"""

from textual.app import ComposeResult, App
from textual.binding import Binding
from textual.message import Message

from crewchief.tui.theme import THEME_CSS
from crewchief.tui.screens.dashboard import DashboardScreen


class CrewChiefTUI(App):
    """Main CrewChief TUI application with mainframe aesthetic."""

    TITLE = "CrewChief - Garage Management"
    SUB_TITLE = "Local-first maintenance tracking"

    CSS = THEME_CSS

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
    ]

    class VehicleSelected(Message):
        """Posted when user selects a vehicle."""

        def __init__(self, car_id: int) -> None:
            super().__init__()
            self.car_id = car_id

    def on_mount(self) -> None:
        """App startup - push dashboard screen."""
        self.title = self.TITLE
        self.sub_title = self.SUB_TITLE
        self.push_screen(DashboardScreen())


def run() -> None:
    """Run the CrewChief TUI application."""
    app = CrewChiefTUI()
    app.run()


if __name__ == "__main__":
    run()
