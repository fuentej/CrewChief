"""Garage service adapter - wraps GarageRepository for TUI layer."""

from crewchief.db import GarageRepository
from crewchief.models import Car
from crewchief.settings import get_settings


class GarageService:
    """Service layer for vehicle/garage operations."""

    def __init__(self):
        """Initialize the garage service with repository."""
        settings = get_settings()
        db_path = settings.get_expanded_db_path()
        self.repo = GarageRepository(db_path)

    def get_all_vehicles(self) -> list[Car]:
        """Get all vehicles in the garage.

        Returns:
            List of all Car objects in the garage.
        """
        return self.repo.get_cars()

    def get_vehicle(self, car_id: int) -> Car | None:
        """Get a specific vehicle by ID.

        Args:
            car_id: The vehicle ID.

        Returns:
            Car object if found, None otherwise.
        """
        return self.repo.get_car(car_id)

    def get_vehicle_with_stats(self, car_id: int) -> dict | None:
        """Get vehicle info with related stats.

        Args:
            car_id: The vehicle ID.

        Returns:
            Dict with car, events, and due_services, or None if car not found.
        """
        car = self.repo.get_car(car_id)
        if car is None:
            return None

        events = self.repo.get_maintenance_for_car(car_id, limit=10)
        due = self.repo.get_due_services(car_id)
        parts = self.repo.get_car_parts(car_id)

        return {
            "car": car,
            "events": events,
            "due_services": due,
            "parts": parts,
        }

    def get_garage_stats(self) -> dict:
        """Get garage-wide statistics.

        Returns:
            Dict with total_vehicles, total_events, total_parts, etc.
        """
        cars = self.repo.get_cars()
        all_events = self.repo.get_all_maintenance()

        total_parts = 0
        for car in cars:
            total_parts += len(self.repo.get_car_parts(car.id))

        return {
            "total_vehicles": len(cars),
            "total_maintenance_events": len(all_events),
            "total_parts": total_parts,
        }

    def add_vehicle(self, car: Car) -> Car:
        """Add a new vehicle to the garage.

        Args:
            car: Car object to add.

        Returns:
            Car object with generated ID.
        """
        return self.repo.add_car(car)

    def update_vehicle(self, car: Car) -> Car:
        """Update existing vehicle.

        Args:
            car: Car object with updated fields.

        Returns:
            Updated Car object.
        """
        return self.repo.update_car(car)

    def delete_vehicle(self, car_id: int) -> bool:
        """Delete a vehicle and all related data.

        Args:
            car_id: The vehicle ID to delete.

        Returns:
            True if deleted, False otherwise.
        """
        return self.repo.delete_car(car_id)

    def close(self) -> None:
        """Close database connection."""
        self.repo.close()
