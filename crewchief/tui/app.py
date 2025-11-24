"""CrewChief TUI - Mainframe-style Terminal User Interface for garage management.

Entry point: crewchief-tui
"""

from textual.app import ComposeResult, App
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Static, Header, Footer

from crewchief.tui.theme import THEME_CSS
from crewchief.tui.widgets import ASCIIBanner


class CrewChiefTUI(App):
    """Main CrewChief TUI application with mainframe aesthetic."""

    TITLE = "CrewChief - Garage Management"
    SUB_TITLE = "Local-first maintenance tracking"

    CSS = THEME_CSS + """
    Screen {
        layout: vertical;
    }

    #banner {
        width: 100%;
        height: auto;
    }

    #content {
        width: 100%;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield ASCIIBanner(id="banner")
        yield Static("TUI screens will go here", id="content")
        yield Footer()

    def on_mount(self) -> None:
        """App startup."""
        self.title = self.TITLE
        self.sub_title = self.SUB_TITLE


def run() -> None:
    """Run the CrewChief TUI application."""
    app = CrewChiefTUI()
    app.run()


if __name__ == "__main__":
    run()
