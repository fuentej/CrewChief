"""Maintenance event form modal."""

from datetime import date
from crewchief.models import MaintenanceEvent, ServiceType
from crewchief.tui.screens.modals import BaseFormModal, FormField


class MaintenanceEventFormModal(BaseFormModal):
    """Form for creating/editing maintenance events."""

    def __init__(self, car_id: int, event: MaintenanceEvent | None = None, **kwargs):
        """Initialize maintenance form.

        Args:
            car_id: Vehicle ID
            event: Existing event to edit, or None for new event
            **kwargs: Additional parameters
        """
        self.car_id = car_id
        self.event = event
        self.is_new = event is None

        # Build fields
        fields = [
            FormField(
                "service_date",
                "Service Date",
                field_type="date",
                required=True,
                default=event.service_date.isoformat() if event else date.today().isoformat(),
            ),
            FormField(
                "service_type",
                "Service Type",
                field_type="select",
                required=True,
                options=[
                    (st.value, st.value.replace("_", " ").title())
                    for st in ServiceType
                ],
                default=event.service_type.value if event else None,
            ),
            FormField(
                "odometer",
                "Odometer (miles)",
                field_type="number",
                required=False,
                default=str(event.odometer) if event and event.odometer else "",
            ),
            FormField(
                "cost",
                "Cost ($)",
                field_type="number",
                required=False,
                default=f"{event.cost:.2f}" if event and event.cost else "",
            ),
            FormField(
                "location",
                "Location",
                field_type="text",
                required=False,
                default=event.location or "" if event else "",
            ),
            FormField(
                "parts",
                "Parts Used",
                field_type="text",
                required=False,
                default=event.parts or "" if event else "",
            ),
            FormField(
                "description",
                "Description/Notes",
                field_type="textarea",
                required=False,
                default=event.description or "" if event else "",
            ),
        ]

        title = f"{'Edit' if event else 'New'} Maintenance Entry"
        super().__init__(title, fields, **kwargs)

    def validate_form(self) -> bool:
        """Validate maintenance form data."""
        if not super().validate_form():
            return False

        # Validate service_date format
        try:
            service_date_widget = self.query_one("#field-service_date")
            date.fromisoformat(service_date_widget.value)
        except ValueError:
            self.show_error("Invalid date format (use YYYY-MM-DD)")
            return False
        except Exception:
            return False

        # Validate odometer if provided
        try:
            odometer_widget = self.query_one("#field-odometer")
            if odometer_widget.value:
                int(odometer_widget.value)
        except ValueError:
            self.show_error("Odometer must be a number")
            return False
        except Exception:
            pass

        # Validate cost if provided
        try:
            cost_widget = self.query_one("#field-cost")
            if cost_widget.value:
                float(cost_widget.value)
        except ValueError:
            self.show_error("Cost must be a valid number")
            return False
        except Exception:
            pass

        return True

    def collect_form_data(self) -> None:
        """Collect form data into a MaintenanceEvent."""
        super().collect_form_data()

        # Convert string values to proper types
        service_date = date.fromisoformat(self.form_data["service_date"])
        service_type = ServiceType(self.form_data["service_type"])
        odometer = (
            int(self.form_data["odometer"])
            if self.form_data.get("odometer")
            else None
        )
        cost = float(self.form_data["cost"]) if self.form_data.get("cost") else None

        # Build event object
        event_data = {
            "car_id": self.car_id,
            "service_date": service_date,
            "service_type": service_type,
            "odometer": odometer,
            "cost": cost,
            "location": self.form_data.get("location") or None,
            "parts": self.form_data.get("parts") or None,
            "description": self.form_data.get("description") or None,
        }

        # Preserve ID and created_at if editing (but don't update them)
        if self.event:
            event_data["id"] = self.event.id

        self.form_data = event_data
