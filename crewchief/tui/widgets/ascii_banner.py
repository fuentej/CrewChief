"""ASCII art banner widget for CrewChief TUI."""

from textual.widget import Widget
from textual.containers import Container
from textual.reactive import reactive
from rich.text import Text


class ASCIIBanner(Widget):
    """Displays the CrewChief ASCII art banner in mainframe style."""

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
    """

    def render(self) -> Text:
        """Render the banner."""
        return Text(self.BANNER_TEXT, style="bold cyan")
