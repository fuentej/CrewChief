"""ASCII art banner widget for CrewChief TUI."""

import random
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

    # Rotating motivational phrases
    MOTIVATIONAL_PHRASES = [
        "If you're not first, you're last!",
        "All your base are below to us",
        "First or last, that's racing",
        "Second place is first loser",
        "No participation trophies",
        "Victory is the only option",
        "Dominate or don't show up",
    ]

    DEFAULT_CSS = """
    ASCIIBanner {
        width: 100%;
        height: auto;
        background: $boost;
        border: heavy $primary;
        color: $accent;
        text-align: center;
        padding: 0 0;
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
        # Special handling for the new banner design with embedded subtitle
        if "If you're not 1st" in self.BANNER_TEXT or any(phrase in self.BANNER_TEXT for phrase in self.MOTIVATIONAL_PHRASES):
            # Build centered banner with color-coded lines
            lines = self.BANNER_TEXT.split("\n")
            result = Text()
            for line in lines:
                # Center each line dynamically based on terminal width
                centered_line = line.center(80)
                if "CREWCHIEF" in line:
                    # Main title in warning orange
                    result.append(centered_line, style="bold #ff8800")
                elif "GARAGE" in line:
                    # GARAGE in OK green
                    result.append(centered_line, style="bold #00ff00")
                elif line.strip() and any(phrase in line for phrase in self.MOTIVATIONAL_PHRASES):
                    # Rotating phrases in yellow
                    result.append(centered_line, style="bold yellow")
                elif line.strip():  # Other non-empty lines get cyan
                    result.append(centered_line, style="bold cyan")
                else:  # Empty lines stay empty
                    result.append(line)
                result.append("\n")
            return result

        # Standard banner rendering with optional subtitle
        text = Text(self.BANNER_TEXT, style="bold cyan")
        if self.subtitle:
            text.append("\n")
            if self.subtitle_align == "right":
                padding = " " * (80 - len(self.subtitle) - 2)
                text.append(padding)
            text.append(self.subtitle, style="bold magenta")

        return text

    @staticmethod
    def get_alt_banner_1() -> str:
        """Alternative banner design 1: Bigger with side phrases."""
        return r"""
  ___  _   _  ___   ___  _    _  ___  ___   _______  ___  _____
 / __|| \_/ ||  _ \| __|| |  / \|  _\|  __| |_   _|| __|/  ___/
| |__ |  _  || |_||/ /_ | | / _ \| |_ | ||      | |  | |  | |_
 \__ \| | | ||  _ \ \__||_|/ / \ \  _\|_||_     | |  |_|   \__/
 ____/|_| |_||_| \_\\___/ |_|_/ \_\__|          |_|   ___   ___

 If you're not 1st, you're last        2nd place is 1st loser
        """

    @staticmethod
    def get_alt_banner_2() -> str:
        """Alternative banner design 2: Bigger with racing theme."""
        return r"""
   ██████╗ ██████╗ ███████╗██╗    ██╗ ██████╗██╗  ██╗██╗███████╗███████╗
  ██╔════╝██╔════╝ ██╔════╝██║    ██║██╔════╝██║  ██║██║██╔════╝██╔════╝
  ██║     ██║  ███╗█████╗  ██║ █╗ ██║██║     ███████║██║█████╗  █████╗
  ██║     ██║   ██║██╔══╝  ██║███╗██║██║     ██╔══██║██║██╔══╝  ██╔══╝
  ╚██████╗╚██████╔╝███████╗╚███╔███╔╝╚██████╗██║  ██║██║███████╗███████╗
   ╚═════╝ ╚═════╝ ╚══════╝ ╚══╝╚══╝  ╚═════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝

    Rubbing's racing · First to the line · No days off
        """

    @staticmethod
    def get_random_phrase() -> str:
        """Get a random motivational phrase.

        Returns:
            A random phrase from the motivational phrases list.
        """
        return random.choice(ASCIIBanner.MOTIVATIONAL_PHRASES)

    @staticmethod
    def get_alt_banner_3() -> str:
        """Alternative banner design 3: ASCII CREWCHIEF GARAGE with rotating subtitle."""
        phrase = ASCIIBanner.get_random_phrase()
        return f"═══ C R E W C H I E F ═══\n\n🏁 G A R A G E 🏁\n\n{phrase}"
