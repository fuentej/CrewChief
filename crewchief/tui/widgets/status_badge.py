"""Status badge widget - colored status indicators."""

from textual.widget import Widget
from rich.text import Text


class StatusBadge(Widget):
    """Displays color-coded status indicator with theme-aware colors."""

    DEFAULT_CSS = """
    StatusBadge {
        width: auto;
        height: auto;
    }
    """

    # Status to (symbol, color_style) mapping
    # Uses Textual's built-in colors and bold for high contrast
    STATUS_MAP = {
        "ready": ("●", "bold green"),
        "warning": ("⚠", "bold yellow"),
        "error": ("✗", "bold red"),
        "info": ("ℹ", "bold cyan"),
        "running": ("⟳", "bold yellow"),
        "ok": ("●", "bold green"),
        "due": ("⚠", "bold yellow"),
        "overdue": ("✗", "bold red"),
    }

    def __init__(self, status: str = "info", **kwargs):
        """Initialize badge with status.

        Args:
            status: Status key (ready, warning, error, info, running, ok, due, overdue).
        """
        super().__init__(**kwargs)
        self.status = status

    def render(self) -> Text:
        """Render the status badge with theme-aware colors."""
        symbol, style = self.STATUS_MAP.get(self.status, ("?", "bold white"))
        return Text(symbol, style=style)

    def update_status(self, status: str) -> None:
        """Update the status.

        Args:
            status: New status key.
        """
        self.status = status
        self.refresh()
