"""Mainframe-style TUI theme for CrewChief.

Color scheme inspired by classic mainframe/BBS/AS/400 terminals:
- Green: healthy/success/idle-ready
- Yellow: running/in-progress/warnings
- Red: error/fail/needs attention
- Cyan: selected/focused element
- Magenta: minor accents/section headers
"""

# Textual CSS theme for mainframe aesthetic
THEME_CSS = """
Screen {
    background: $surface;
    color: $text;
}

.banner {
    width: 100%;
    height: 8;
    color: $accent;
    border: heavy $primary;
    background: $boost;
}

.panel {
    border: solid $primary;
    background: $panel;
}

.panel-title {
    color: $secondary;
    text-style: bold;
}

.status-ready {
    color: $success;
}

.status-warning {
    color: $warning;
}

.status-error {
    color: $error;
}

.status-info {
    color: $accent;
}

.focused {
    background: $accent;
    color: $surface;
}

.footer-bar {
    dock: bottom;
    height: 1;
    background: $panel;
    color: $text;
    border-top: solid $primary;
}

.key-hint {
    color: $accent;
}

DataTable {
    border: solid $primary;
}

DataTable > .cursor-cell {
    background: $accent;
    color: $surface;
}

DataTable > .odd-row {
    background: $panel;
}

DataTable > .even-row {
    background: $surface;
}
"""

# Color definitions for specific status indicators
STATUS_COLORS = {
    "ready": "green",
    "warning": "yellow",
    "error": "red",
    "info": "cyan",
    "header": "magenta",
}

# Box-drawing characters for ASCII art
BOX_CHARS = {
    "horizontal": "─",
    "vertical": "│",
    "top_left": "┌",
    "top_right": "┐",
    "bottom_left": "└",
    "bottom_right": "┘",
    "cross": "┼",
    "t_down": "┬",
    "t_up": "┴",
    "t_right": "├",
    "t_left": "┤",
    "heavy_horizontal": "━",
    "heavy_vertical": "┃",
    "heavy_top_left": "┏",
    "heavy_top_right": "┓",
    "heavy_bottom_left": "┗",
    "heavy_bottom_right": "┛",
    "heavy_cross": "╋",
}

# Status indicators
STATUS_INDICATORS = {
    "ready": "●",  # Filled circle
    "warning": "⚠",  # Warning sign
    "error": "✗",  # X mark
    "info": "ℹ",  # Info mark
    "running": "⟳",  # Spinning arrows
}
