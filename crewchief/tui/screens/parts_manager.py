"""Parts manager screen - manage vehicle parts profile."""

from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Label
from textual.binding import Binding

from crewchief.models import CarPart
from crewchief.tui.widgets.parts_table import PartsTable
from crewchief.tui.widgets.help_footer import HelpFooter
from crewchief.tui.widgets.ascii_banner import ASCIIBanner
from crewchief.tui.services.parts_service import PartsService
from crewchief.tui.services.garage_service import GarageService
from crewchief.tui.screens.parts_form import PartsFormModal
from crewchief.tui.screens.modals import ConfirmDeleteModal


class PartsManagerScreen(Screen):
    """Screen for managing vehicle parts profile."""

    DEFAULT_CSS = """
    PartsManagerScreen {
        layout: vertical;
    }

    #header {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $boost;
        padding: 1;
        layout: horizontal;
    }

    #title-section {
        width: 50%;
        height: auto;
    }

    #title {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    #header-banner {
        width: 50%;
        height: auto;
        align: right middle;
    }

    #parts-table {
        width: 100%;
        height: 1fr;
        border: solid $primary;
    }

    #detail-section {
        width: 100%;
        height: auto;
        border-top: solid $primary;
        padding: 1;
        background: $panel;
    }

    #detail-header {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
    }

    #detail-content {
        width: 100%;
        height: auto;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("v", "view_part", "View Part"),
        Binding("n", "new_part", "New Part"),
        Binding("e", "edit_part", "Edit"),
        Binding("d", "delete_part", "Delete"),
        Binding("?", "help", "Help"),
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, car_id: int, **kwargs):
        """Initialize parts manager screen.

        Args:
            car_id: The vehicle ID to manage parts for.
        """
        super().__init__(**kwargs)
        self.car_id = car_id
        self.garage_service = GarageService()
        self.parts_service = PartsService()
        self.parts_table: PartsTable | None = None
        self.detail_content: Static | None = None
        self._current_notification = None

    def compose(self):
        """Compose parts manager layout."""
        with Container(id="header"):
            with Container(id="title-section"):
                yield Label("[ PARTS PROFILE ]", id="title")

            with Container(id="header-banner"):
                yield ASCIIBanner(subtitle="THE PARTS SHELF", subtitle_align="center")

        yield PartsTable(id="parts-table")

        with Container(id="detail-section"):
            yield Label("[ PART DETAILS ]", id="detail-header")
            yield Static("Select a part to view details", id="detail-content")

        yield HelpFooter(
            help_text=" [↑↓]Select  [N]ew  [E]dit  [D]elete  [Esc]Back  [?]Help",
            id="help-footer",
        )

    def on_mount(self) -> None:
        """Load parts data when screen mounts."""
        self.load_parts_data()

    def load_parts_data(self) -> None:
        """Load and display parts for the vehicle."""
        car = self.garage_service.get_vehicle(self.car_id)
        if not car:
            self.dismiss()
            return

        # Update title with car name
        title = self.query_one("#title", Label)
        title.update(f"[ PARTS PROFILE: {car.display_name()} ]")

        # Load parts
        parts = self.parts_service.get_parts_for_car(self.car_id)
        self.parts_table = self.query_one("#parts-table", PartsTable)
        self.parts_table.setup_table()
        self.parts_table.populate_parts(parts)

        self.detail_content = self.query_one("#detail-content", Static)

    def on_data_table_row_selected(self) -> None:
        """Update detail pane when row selected."""
        if self.parts_table:
            part = self.parts_table.get_selected_part()
            if part:
                detail_text = (
                    f"Category: {part.part_category.value.replace('_', ' ').title()}\n"
                    f"Brand: {part.brand or '—'}\n"
                    f"Part Number: {part.part_number or '—'}\n"
                    f"Size/Spec: {part.size_spec or '—'}\n\n"
                    f"Notes: {part.notes or 'No notes'}"
                )
                self.detail_content.update(detail_text)

    def action_back(self) -> None:
        """Go back to previous screen."""
        # Dismiss notification when leaving
        if self._current_notification:
            self._current_notification.dismiss()
        self.app.pop_screen()

    def action_view_part(self) -> None:
        """View selected part details."""
        if self.parts_table:
            part = self.parts_table.get_selected_part()
            if part:
                # Dismiss previous notification if it exists
                if self._current_notification:
                    self._current_notification.dismiss()

                detail_text = (
                    f"Category: {part.part_category.value.replace('_', ' ').title()}\n"
                    f"Brand: {part.brand or '—'}\n"
                    f"Part Number: {part.part_number or '—'}\n"
                    f"Size/Spec: {part.size_spec or '—'}\n\n"
                    f"Notes: {part.notes or 'No notes'}"
                )
                self._current_notification = self.notify(detail_text, timeout=0)

    def action_new_part(self) -> None:
        """Add a new part to the profile."""
        def handle_form_result(form_data: dict) -> None:
            """Handle form submission."""
            if form_data:
                try:
                    part = CarPart(**form_data)
                    result = self.parts_service.add_part(part)
                    self.notify("Part added to profile", timeout=2)
                    self.load_parts_data()
                except Exception as e:
                    self.notify(f"Error adding part: {str(e)}", timeout=3)

        self.app.push_screen(
            PartsFormModal(self.car_id),
            callback=handle_form_result,
        )

    def action_edit_part(self) -> None:
        """Edit selected part."""
        if self.parts_table:
            part = self.parts_table.get_selected_part()
            if part:
                def handle_form_result(form_data: dict) -> None:
                    """Handle form submission."""
                    if form_data:
                        try:
                            part_id = form_data.pop("id")
                            self.parts_service.update_part(part_id, **form_data)
                            self.notify("Part updated", timeout=2)
                            self.load_parts_data()
                        except Exception as e:
                            self.notify(f"Error updating part: {str(e)}", timeout=3)

                self.app.push_screen(
                    PartsFormModal(self.car_id, part),
                    callback=handle_form_result,
                )

    def action_delete_part(self) -> None:
        """Delete selected part."""
        if self.parts_table:
            part = self.parts_table.get_selected_part()
            if part:
                def handle_confirm(confirmed: bool) -> None:
                    """Handle delete confirmation."""
                    if confirmed:
                        try:
                            self.parts_service.delete_part(part.id)
                            self.notify("Part deleted", timeout=2)
                            self.load_parts_data()
                        except Exception as e:
                            self.notify(f"Error deleting part: {str(e)}", timeout=3)

                self.app.push_screen(
                    ConfirmDeleteModal(
                        "Delete Part",
                        f"Delete {part.brand or part.part_category.value} part?\nThis cannot be undone.",
                    ),
                    callback=handle_confirm,
                )

    def action_help(self) -> None:
        """Show help screen."""
        self.app.action_help()

    def on_unmount(self) -> None:
        """Clean up when leaving screen."""
        self.garage_service.close()
        self.parts_service.close()
