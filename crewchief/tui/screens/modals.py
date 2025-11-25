"""Modal forms for CRUD operations."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Label, Input, Button, Select
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
        default: str | None = None,
    ):
        """Initialize form field.

        Args:
            name: Field identifier
            label: Display label
            field_type: 'text', 'number', 'date', 'select', 'textarea'
            required: Whether field must have a value
            options: For select fields, list of (value, label) tuples
            default: Default value
        """
        self.name = name
        self.label = label
        self.field_type = field_type
        self.required = required
        self.options = options or []
        self.default = default
        self.value: str | None = default


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
        height: 1;
        border: solid $primary;
    }

    .form-select {
        width: 100%;
        height: 3;
        border: solid $primary;
    }

    .form-textarea {
        width: 100%;
        height: 4;
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
        self.input_widgets: dict[str, Input] = {}
        self.select_widgets: dict[str, Select] = {}
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
                            select = Select(
                                [(str(v), str(l)) for v, l in field.options],
                                id=f"{field.name}",
                                classes="form-select",
                            )
                            yield select
                            self.select_widgets[field.name] = select
                        else:
                            input_type = "text"
                            if field.field_type == "number":
                                input_type = "number"
                            elif field.field_type == "date":
                                input_type = "text"

                            css_class = "form-textarea" if field.field_type == "textarea" else "form-input"
                            input_widget = Input(
                                id=f"{field.name}",
                                placeholder=f"{field.label}...",
                                classes=css_class,
                                type=input_type,
                            )
                            yield input_widget
                            self.input_widgets[field.name] = input_widget

            with Horizontal(id="form-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self) -> None:
        """Set field defaults after mount."""
        for field in self.fields:
            if field.name in self.input_widgets and field.default:
                self.input_widgets[field.name].value = field.default

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
            if field.name in self.input_widgets:
                self.form_data[field.name] = self.input_widgets[field.name].value
            elif field.name in self.select_widgets:
                select = self.select_widgets[field.name]
                if select.value is not None:
                    self.form_data[field.name] = str(select.value)

    def validate_form(self) -> bool:
        """Validate form data. Override in subclasses for custom validation.

        Returns:
            True if form is valid, False otherwise.
        """
        for field in self.fields:
            if field.required:
                if field.name in self.input_widgets:
                    if not self.input_widgets[field.name].value.strip():
                        return False
                elif field.name in self.select_widgets:
                    if self.select_widgets[field.name].value is None:
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
