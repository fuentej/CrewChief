"""Parts form modal."""

from crewchief.models import CarPart, PartCategory
from crewchief.tui.screens.modals import BaseFormModal, FormField


class PartsFormModal(BaseFormModal):
    """Form for creating/editing car parts."""

    def __init__(self, car_id: int, part: CarPart | None = None, **kwargs):
        """Initialize parts form.

        Args:
            car_id: Vehicle ID
            part: Existing part to edit, or None for new part
            **kwargs: Additional parameters
        """
        self.car_id = car_id
        self.part = part
        self.is_new = part is None

        # Build fields
        fields = [
            FormField(
                "part_category",
                "Category",
                field_type="select",
                required=True,
                options=[
                    (pc.value, pc.value.replace("_", " ").title())
                    for pc in PartCategory
                ],
                default=part.part_category.value if part else None,
            ),
            FormField(
                "brand",
                "Brand/Manufacturer",
                field_type="text",
                required=False,
                default=part.brand or "" if part else "",
            ),
            FormField(
                "part_number",
                "Part Number",
                field_type="text",
                required=False,
                default=part.part_number or "" if part else "",
            ),
            FormField(
                "size_spec",
                "Size/Specification",
                field_type="text",
                required=False,
                default=part.size_spec or "" if part else "",
            ),
            FormField(
                "notes",
                "Notes",
                field_type="textarea",
                required=False,
                default=part.notes or "" if part else "",
            ),
        ]

        title = f"{'Edit' if part else 'New'} Part"
        super().__init__(title, fields, **kwargs)

    def collect_form_data(self) -> None:
        """Collect form data into a CarPart."""
        super().collect_form_data()

        # Convert string values to proper types
        part_category = PartCategory(self.form_data["part_category"])

        # Build part object (car_id excluded as it shouldn't change during update)
        part_data = {
            "part_category": part_category,
            "brand": self.form_data.get("brand"),
            "part_number": self.form_data.get("part_number"),
            "size_spec": self.form_data.get("size_spec"),
            "notes": self.form_data.get("notes"),
        }

        # Preserve ID if editing
        if self.part:
            part_data["id"] = self.part.id
            part_data["created_at"] = self.part.created_at
            part_data["updated_at"] = self.part.updated_at

        self.form_data = part_data
