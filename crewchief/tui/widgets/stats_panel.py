"""Stats panel widget - box-drawn panel with key-value pairs."""

from textual.widget import Widget
from textual.containers import Container, Vertical
from textual.widgets import Static
from rich.text import Text
from rich.console import RenderableType


class StatsPanel(Widget):
    """Box-drawn panel displaying statistics."""

    DEFAULT_CSS = """
    StatsPanel {
        width: 1fr;
        height: auto;
        border: solid $primary;
        background: $panel;
    }

    StatsPanel > #title {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        background: $boost;
    }

    StatsPanel > #content {
        width: 100%;
        height: auto;
        padding: 0 1;
    }

    StatsPanel .stat-row {
        width: 100%;
        height: 1;
    }

    StatsPanel .stat-key {
        color: $text;
        text-style: bold;
    }

    StatsPanel .stat-value {
        color: $accent;
    }
    """

    def __init__(self, title: str = "", **kwargs):
        """Initialize stats panel with title.

        Args:
            title: Panel title.
        """
        super().__init__(**kwargs)
        self.title_text = title
        self.stats: dict[str, str | int] = {}

    def set_stats(self, stats: dict[str, str | int]) -> None:
        """Update stats to display.

        Args:
            stats: Dictionary of stat_name -> value.
        """
        self.stats = stats
        self.refresh()

    def render(self) -> RenderableType:
        """Render the stats panel."""
        lines = []

        # Title line
        if self.title_text:
            title = f"[ {self.title_text} ]"
            lines.append(Text(title, style="bold magenta"))

        # Stats lines
        for key, value in self.stats.items():
            # Format: "Key: value"
            line = f"{key}:"
            # Pad to align values
            line = line.ljust(25)
            line_text = Text()
            line_text.append(line, style="white")
            line_text.append(str(value), style="cyan")
            lines.append(line_text)

        if not lines:
            return Text("")

        # Combine all lines
        result = Text("\n").join(lines)
        return result
