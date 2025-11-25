"""Car form modal for adding/editing vehicles."""

from datetime import datetime
from crewchief.models import Car, UsageType
from crewchief.tui.screens.modals import BaseFormModal, FormField


class CarFormModal(BaseFormModal):
    """Form for creating/editing vehicles."""

    def __init__(self, car: Car | None = None, **kwargs):
        """Initialize car form.

        Args:
            car: Existing car to edit, or None for new car
            **kwargs: Additional parameters
        """
        self.car = car
        self.is_new = car is None

        # Build fields
        fields = [
            FormField(
                "year",
                "Year",
                field_type="text",
                required=True,
                default=str(car.year) if car else str(datetime.now().year),
            ),
            FormField(
                "make",
                "Make",
                field_type="text",
                required=True,
                default=car.make if car else "",
            ),
            FormField(
                "model",
                "Model",
                field_type="text",
                required=True,
                default=car.model if car else "",
            ),
            FormField(
                "trim",
                "Trim",
                field_type="text",
                required=False,
                default=car.trim or "" if car else "",
            ),
            FormField(
                "vin",
                "VIN",
                field_type="text",
                required=False,
                default=car.vin or "" if car else "",
            ),
            FormField(
                "usage_type",
                "Usage Type",
                field_type="select",
                required=True,
                options=[
                    (ut.value, ut.value.upper())
                    for ut in UsageType
                ],
                default=car.usage_type.value if car else "daily",
            ),
            FormField(
                "current_odometer",
                "Current Odometer (miles)",
                field_type="text",
                required=False,
                default=str(car.current_odometer) if car and car.current_odometer else "",
            ),
            FormField(
                "nickname",
                "Nickname",
                field_type="text",
                required=False,
                default=car.nickname or "" if car else "",
            ),
            FormField(
                "notes",
                "Notes",
                field_type="textarea",
                required=False,
                default=car.notes or "" if car else "",
            ),
        ]

        title = f"{'Edit' if car else 'New'} Vehicle"
        super().__init__(title, fields, **kwargs)

    def validate_form(self) -> bool:
        """Validate car form data."""
        if not super().validate_form():
            return False

        # Validate year is a number between 1900 and 2100
        try:
            year_widget = self.query_one("#field-year")
            year = int(year_widget.value)
            if year < 1900 or year > 2100:
                self.show_error("Year must be between 1900 and 2100")
                return False
        except ValueError:
            self.show_error("Year must be a valid number")
            return False
        except Exception:
            return False

        # Validate odometer if provided
        try:
            odometer_widget = self.query_one("#field-current_odometer")
            if odometer_widget.value:
                odometer = int(odometer_widget.value)
                if odometer < 0:
                    self.show_error("Odometer cannot be negative")
                    return False
        except ValueError:
            self.show_error("Odometer must be a valid number")
            return False
        except Exception:
            pass

        return True

    def collect_form_data(self) -> None:
        """Collect form data into a Car object."""
        super().collect_form_data()

        # Convert string values to proper types
        year = int(self.form_data["year"])
        odometer = (
            int(self.form_data["current_odometer"])
            if self.form_data.get("current_odometer")
            else None
        )
        usage_type = UsageType(self.form_data["usage_type"])

        # Build car object
        car_data = {
            "year": year,
            "make": self.form_data["make"],
            "model": self.form_data["model"],
            "trim": self.form_data.get("trim") or None,
            "vin": self.form_data.get("vin") or None,
            "usage_type": usage_type,
            "current_odometer": odometer,
            "nickname": self.form_data.get("nickname") or None,
            "notes": self.form_data.get("notes") or None,
        }

        # Preserve ID and timestamps if editing
        if self.car:
            car_data["id"] = self.car.id
            car_data["created_at"] = self.car.created_at
            car_data["updated_at"] = datetime.now()

        self.form_data = car_data
