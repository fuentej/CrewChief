"""Help footer widget - displays keybindings for current screen."""

from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text


class HelpFooter(Widget):
    """Displays context-sensitive help keybindings at bottom of screen."""

    DEFAULT_CSS = """
    HelpFooter {
        width: 100%;
        height: 1;
        background: $panel;
        color: $text;
        border-top: solid $primary;
        dock: bottom;
    }
    """

    help_text: reactive[str] = reactive("")

    def __init__(self, help_text: str = "", **kwargs):
        """Initialize footer with help text.

        Args:
            help_text: Keybinding help text to display.
        """
        super().__init__(**kwargs)
        self.help_text = help_text

    def render(self) -> Text:
        """Render the help footer."""
        if not self.help_text:
            return Text("")

        return Text(self.help_text, style="dim white")

    def update_help(self, help_text: str) -> None:
        """Update the help text.

        Args:
            help_text: New keybinding help text.
        """
        self.help_text = help_text
