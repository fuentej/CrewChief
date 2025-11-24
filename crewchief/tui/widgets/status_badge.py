"""Status badge widget - colored status indicators."""

from textual.widget import Widget
from rich.text import Text


class StatusBadge(Widget):
    """Displays color-coded status indicator."""

    DEFAULT_CSS = """
    StatusBadge {
        width: auto;
        height: auto;
    }
    """

    # Status to (symbol, color) mapping
    STATUS_MAP = {
        "ready": ("●", "green"),
        "warning": ("⚠", "yellow"),
        "error": ("✗", "red"),
        "info": ("ℹ", "cyan"),
        "running": ("⟳", "yellow"),
    }

    def __init__(self, status: str = "info", **kwargs):
        """Initialize badge with status.

        Args:
            status: Status key (ready, warning, error, info, running).
        """
        super().__init__(**kwargs)
        self.status = status

    def render(self) -> Text:
        """Render the status badge."""
        symbol, color = self.STATUS_MAP.get(self.status, ("?", "white"))
        return Text(symbol, style=color)

    def update_status(self, status: str) -> None:
        """Update the status.

        Args:
            status: New status key.
        """
        self.status = status
        self.refresh()
