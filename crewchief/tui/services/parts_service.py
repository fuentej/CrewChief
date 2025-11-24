"""Parts service adapter - wraps parts operations for TUI layer."""

from crewchief.db import GarageRepository
from crewchief.models import CarPart
from crewchief.settings import get_settings


class PartsService:
    """Service layer for parts profile operations."""

    def __init__(self):
        """Initialize the parts service with repository."""
        settings = get_settings()
        db_path = settings.get_expanded_db_path()
        self.repo = GarageRepository(db_path)

    def get_parts_for_car(self, car_id: int) -> list[CarPart]:
        """Get all parts in a vehicle's profile.

        Args:
            car_id: The vehicle ID.

        Returns:
            List of CarPart objects for the vehicle.
        """
        return self.repo.get_car_parts(car_id)

    def get_part(self, part_id: int) -> CarPart | None:
        """Get a specific part.

        Args:
            part_id: The part ID.

        Returns:
            CarPart if found, None otherwise.
        """
        return self.repo.get_car_part(part_id)

    def add_part(self, part: CarPart) -> CarPart:
        """Add a new part to a vehicle's profile.

        Args:
            part: CarPart object to add.

        Returns:
            CarPart with generated ID.
        """
        return self.repo.add_car_part(part)

    def update_part(self, part_id: int, **kwargs) -> CarPart | None:
        """Update a part.

        Args:
            part_id: The part ID to update.
            **kwargs: Fields to update (brand, part_number, etc.).

        Returns:
            Updated CarPart if found, None otherwise.
        """
        return self.repo.update_car_part(part_id, **kwargs)

    def delete_part(self, part_id: int) -> bool:
        """Delete a part from a vehicle's profile.

        Args:
            part_id: The part ID to delete.

        Returns:
            True if deleted, False otherwise.
        """
        return self.repo.delete_car_part(part_id)

    def close(self) -> None:
        """Close database connection."""
        self.repo.close()
