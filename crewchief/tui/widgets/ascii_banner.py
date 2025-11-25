"""ASCII art banner widget for CrewChief TUI."""

from textual.widget import Widget
from textual.containers import Container
from textual.reactive import reactive
from rich.text import Text


class ASCIIBanner(Widget):
    """Displays the CrewChief ASCII art banner with optional subtitle."""

    BANNER_TEXT = r"""   ______                 ________    _      ____
  / ____/_______  __  __ / ____/ /_  (_)__  / __/
 / /   / ___/ _ \/ / / // /   / __ \/ / _ \/ /_
/ /___/ /  /  __/ /_/ // /___/ / / / /  __/ __/
\____/_/   \___/\__,_/ \____/_/ /_/_/\___/_/     """

    DEFAULT_CSS = """
    ASCIIBanner {
        width: 100%;
        height: auto;
        background: $boost;
        border: heavy $primary;
        color: $accent;
        text-align: center;
        padding: 1;
    }

    ASCIIBanner .subtitle {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
    }

    ASCIIBanner .subtitle-center {
        text-align: center;
    }

    ASCIIBanner .subtitle-right {
        text-align: right;
    }
    """

    def __init__(self, subtitle: str = "", subtitle_align: str = "right", **kwargs):
        """Initialize banner with optional subtitle.

        Args:
            subtitle: Optional page title to display below banner
            subtitle_align: Alignment for subtitle ("center" or "right")
            **kwargs: Additional widget parameters
        """
        super().__init__(**kwargs)
        self.subtitle = subtitle
        self.subtitle_align = subtitle_align

    def render(self) -> Text:
        """Render the banner with optional subtitle."""
        text = Text(self.BANNER_TEXT, style="bold cyan")

        if self.subtitle:
            text.append("\n")
            # Add padding for right-alignment (approximate terminal width of 80)
            if self.subtitle_align == "right":
                padding = " " * (80 - len(self.subtitle) - 2)
                text.append(padding)
            text.append(self.subtitle, style="bold $secondary")

        return text
