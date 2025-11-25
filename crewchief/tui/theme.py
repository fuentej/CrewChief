"""Mainframe-style TUI theme for CrewChief.

Color Paradigm:
- GREEN (#00ff00): Success states, healthy systems, completed actions
- YELLOW (#ffff00): Warnings, caution states, in-progress items
- RED (#ff0000): Errors, critical alerts, failed states, destructive actions
- CYAN (#00ffff): Informational messages, data display, neutral highlights
- BRIGHT CYAN (#00ffff + bold): Focus states, selected items, active elements
- MAGENTA (#ff00ff): Section headers, category labels, secondary accents
- WHITE (#ffffff): Primary text, default content
- GRAY (#808080): Secondary text, disabled states, subtle elements

Usage Guidelines:
- Use StatusBadge widget for all status indicators
- Reference CSS variables ($success, $warning, $error) instead of hard-coded colors
- Keep contrast high for terminal readability
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
    text-style: bold;
}

.panel {
    border: solid $primary;
    background: $panel;
}

.panel-title {
    color: $secondary;
    text-style: bold;
}

/* Status color classes - high contrast */
.status-ready {
    color: $success;
    text-style: bold;
}

.status-warning {
    color: $warning;
    text-style: bold;
}

.status-error {
    color: $error;
    text-style: bold;
}

.status-info {
    color: $accent;
    text-style: bold;
}

/* Focus and selection states */
.focused {
    background: $accent;
    color: $surface;
    text-style: bold;
}

.selected {
    background: $secondary;
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
    text-style: bold;
}

.header {
    color: $secondary;
    text-style: bold;
}

.success-text {
    color: $success;
}

.warning-text {
    color: $warning;
}

.error-text {
    color: $error;
}

.info-text {
    color: $accent;
}

/* Enhanced DataTable styling */
DataTable {
    border: solid $primary;
}

DataTable > .cursor-cell {
    background: $accent;
    color: $surface;
    text-style: bold;
}

DataTable > .odd-row {
    background: $panel;
}

DataTable > .even-row {
    background: $surface;
}

DataTable > .header-cell {
    color: $secondary;
    text-style: bold;
    background: $boost;
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
