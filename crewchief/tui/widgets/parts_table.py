"""Parts table widget - displays vehicle parts profile."""

from textual.widgets import DataTable
from crewchief.models import CarPart


class PartsTable(DataTable):
    """DataTable subclass for displaying vehicle parts profile."""

    DEFAULT_CSS = """
    PartsTable {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }

    PartsTable > .datatable--cursor {
        background: $accent;
        color: $surface;
    }

    PartsTable > .datatable--header {
        background: $boost;
        color: $primary;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs):
        """Initialize parts table."""
        super().__init__(cursor_type="row", **kwargs)
        self.parts: list[CarPart] = []

    def setup_table(self) -> None:
        """Set up table columns."""
        self.add_columns("ID", "Category", "Brand", "Part Number", "Size/Spec")

    def populate_parts(self, parts: list[CarPart]) -> None:
        """Populate table with parts.

        Args:
            parts: List of CarPart objects to display.
        """
        self.parts = parts

        # Clear existing rows and columns
        self.clear()

        for part in parts:
            self.add_row(
                str(part.id or "—"),
                part.part_category.value.replace("_", " ").title(),
                part.brand or "—",
                part.part_number or "—",
                part.size_spec or "—",
            )

    def get_selected_part(self) -> CarPart | None:
        """Get currently selected part.

        Returns:
            CarPart if selected, None otherwise.
        """
        if not self.parts:
            return None

        cursor_row = self.cursor_row
        if 0 <= cursor_row < len(self.parts):
            return self.parts[cursor_row]

        return None
