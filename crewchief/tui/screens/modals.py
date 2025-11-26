"""Modal forms for CRUD operations."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Label, Input, Button, Select, SelectionList
from textual.binding import Binding
from enum import Enum
from datetime import date


class FormField:
    """Represents a form field."""

    def __init__(
        self,
        name: str,
        label: str,
        field_type: str = "text",
        required: bool = True,
        options: list[tuple[str, str]] | None = None,
        default: str | list[str] | None = None,
    ):
        """Initialize form field.

        Args:
            name: Field identifier
            label: Display label
            field_type: 'text', 'number', 'date', 'select', 'textarea', 'multiselect'
            required: Whether field must have a value
            options: For select fields, list of (value, label) tuples
            default: Default value (str for single fields, list for multiselect)
        """
        self.name = name
        self.label = label
        self.field_type = field_type
        self.required = required
        self.options = options or []
        self.default = default
        self.value: str | list[str] | None = default


class BaseFormModal(ModalScreen):
    """Base class for form modals."""

    DEFAULT_CSS = """
    BaseFormModal {
        align: center middle;
    }

    #form-container {
        width: 80;
        height: auto;
        border: solid $primary;
        background: $boost;
        padding: 1;
    }

    #form-title {
        width: 100%;
        height: 1;
        color: $secondary;
        text-style: bold;
        margin-bottom: 1;
        dock: top;
    }

    #form-fields {
        width: 100%;
        height: auto;
        layout: vertical;
    }

    .form-field-group {
        width: 100%;
        height: auto;
        layout: vertical;
        margin-bottom: 1;
    }

    .form-label {
        width: 100%;
        height: 1;
        color: $text;
        margin-bottom: 1;
    }

    .form-input {
        width: 100%;
        height: auto;
        min-height: 3;
        border: solid $primary;
    }

    .form-select {
        width: 100%;
        height: auto;
        min-height: 3;
        border: solid $primary;
    }

    .form-textarea {
        width: 100%;
        height: auto;
        min-height: 5;
        border: solid $primary;
    }

    #form-buttons {
        width: 100%;
        height: auto;
        layout: horizontal;
        align: center middle;
        margin-top: 1;
        dock: bottom;
    }

    #form-buttons Button {
        margin-right: 1;
    }

    .error-text {
        color: $error;
        margin-bottom: 1;
    }
    """

    def __init__(self, title: str, fields: list[FormField], **kwargs):
        """Initialize form modal.

        Args:
            title: Form title
            fields: List of FormField objects
            **kwargs: Additional Textual parameters
        """
        super().__init__(**kwargs)
        self.title = title
        self.fields = fields
        self.form_data: dict[str, str] = {}
        self.error_message = ""

    def compose(self):
        """Compose form layout."""
        with Container(id="form-container"):
            yield Label(self.title, id="form-title")

            with Vertical(id="form-fields"):
                for field in self.fields:
                    with Vertical(classes="form-field-group"):
                        yield Label(
                            f"{field.label}{'*' if field.required else ''}",
                            classes="form-label",
                        )

                        if field.field_type == "select" and field.options:
                            yield Select(
                                [(str(l), str(v)) for v, l in field.options],
                                id=f"field-{field.name}",
                                classes="form-select",
                            )
                        elif field.field_type == "multiselect" and field.options:
                            yield SelectionList(
                                *[(str(l), str(v)) for v, l in field.options],
                                id=f"field-{field.name}",
                                classes="form-select",
                            )
                        else:
                            css_class = "form-textarea" if field.field_type == "textarea" else "form-input"
                            yield Input(
                                id=f"field-{field.name}",
                                placeholder=f"{field.label}...",
                                classes=css_class,
                            )

            with Horizontal(id="form-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self) -> None:
        """Set field defaults and focus after mount."""
        # Set defaults
        for field in self.fields:
            if field.default:
                try:
                    widget = self.query_one(f"#field-{field.name}")
                    if isinstance(widget, Input):
                        widget.value = field.default
                    elif isinstance(widget, Select) and field.default:
                        widget.value = field.default
                    elif isinstance(widget, SelectionList) and isinstance(field.default, list):
                        for default_val in field.default:
                            try:
                                widget.select_option(str(default_val))
                            except (ValueError, IndexError):
                                pass
                except Exception:
                    pass

        # Set focus on first field
        if self.fields:
            try:
                first_widget = self.query_one(f"#field-{self.fields[0].name}")
                first_widget.focus()
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            if self.validate_form():
                self.collect_form_data()
                self.dismiss(self.form_data)
            else:
                self.show_error("Please fill all required fields")
        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def collect_form_data(self) -> None:
        """Collect all form data into dict."""
        self.form_data = {}
        for field in self.fields:
            try:
                widget = self.query_one(f"#field-{field.name}")
                if isinstance(widget, Input):
                    self.form_data[field.name] = widget.value
                elif isinstance(widget, Select):
                    if widget.value is not None:
                        self.form_data[field.name] = str(widget.value)
                elif isinstance(widget, SelectionList):
                    selected = widget.selected
                    if selected:
                        self.form_data[field.name] = [str(item) for item in selected]
            except Exception:
                pass

    def validate_form(self) -> bool:
        """Validate form data. Override in subclasses for custom validation.

        Returns:
            True if form is valid, False otherwise.
        """
        for field in self.fields:
            if field.required:
                try:
                    widget = self.query_one(f"#field-{field.name}")
                    if isinstance(widget, Input):
                        if not widget.value.strip():
                            return False
                    elif isinstance(widget, Select):
                        if widget.value is None:
                            return False
                    elif isinstance(widget, SelectionList):
                        if not widget.selected:
                            return False
                except Exception:
                    return False
        return True

    def show_error(self, message: str) -> None:
        """Show error message to user."""
        self.error_message = message
        self.app.notify(message, timeout=3)


class ConfirmDeleteModal(ModalScreen):
    """Simple yes/no confirmation for delete operations."""

    DEFAULT_CSS = """
    ConfirmDeleteModal {
        align: center middle;
    }

    #confirm-container {
        width: 60;
        height: auto;
        border: solid $error;
        background: $boost;
        padding: 1;
    }

    #confirm-title {
        width: 100%;
        height: auto;
        color: $error;
        text-style: bold;
        margin-bottom: 1;
    }

    #confirm-message {
        width: 100%;
        height: auto;
        color: $text;
        margin-bottom: 1;
    }

    #confirm-buttons {
        width: 100%;
        height: auto;
        layout: horizontal;
        align: center middle;
    }

    #confirm-buttons Button {
        margin-right: 1;
    }
    """

    def __init__(self, title: str, message: str, **kwargs):
        """Initialize confirmation modal.

        Args:
            title: Dialog title
            message: Confirmation message
            **kwargs: Additional Textual parameters
        """
        super().__init__(**kwargs)
        self.title = title
        self.message = message

    def compose(self):
        """Compose confirmation dialog layout."""
        with Container(id="confirm-container"):
            yield Label(self.title, id="confirm-title")
            yield Label(self.message, id="confirm-message")

            with Horizontal(id="confirm-buttons"):
                yield Button("Delete", id="btn-delete", variant="error")
                yield Button("Cancel", id="btn-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-delete":
            self.dismiss(True)
        else:
            self.dismiss(False)
