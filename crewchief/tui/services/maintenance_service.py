"""Maintenance service adapter - wraps maintenance operations for TUI layer."""

from crewchief.db import GarageRepository
from crewchief.models import MaintenanceEvent
from crewchief.settings import get_settings


class MaintenanceService:
    """Service layer for maintenance event operations."""

    def __init__(self):
        """Initialize the maintenance service with repository."""
        settings = get_settings()
        db_path = settings.get_expanded_db_path()
        self.repo = GarageRepository(db_path)

    def get_recent_events(self, limit: int = 10) -> list[MaintenanceEvent]:
        """Get most recent maintenance events across all vehicles.

        Args:
            limit: Maximum number of events to return.

        Returns:
            List of MaintenanceEvent objects, sorted newest first.
        """
        events = self.repo.get_all_maintenance(limit=limit)
        return sorted(events, key=lambda e: e.service_date, reverse=True)

    def get_events_for_car(self, car_id: int, limit: int | None = None) -> list[MaintenanceEvent]:
        """Get maintenance events for a specific vehicle.

        Args:
            car_id: The vehicle ID.
            limit: Maximum number of events to return.

        Returns:
            List of MaintenanceEvent objects for the car.
        """
        return self.repo.get_maintenance_for_car(car_id, limit=limit)

    def get_event(self, event_id: int) -> MaintenanceEvent | None:
        """Get a specific maintenance event.

        Args:
            event_id: The event ID.

        Returns:
            MaintenanceEvent if found, None otherwise.
        """
        return self.repo.get_maintenance_event(event_id)

    def add_event(self, event: MaintenanceEvent) -> MaintenanceEvent:
        """Add a new maintenance event.

        Args:
            event: MaintenanceEvent object to add.

        Returns:
            MaintenanceEvent with generated ID.
        """
        return self.repo.add_maintenance_event(event)

    def update_event(self, event_id: int, **kwargs) -> MaintenanceEvent | None:
        """Update a maintenance event.

        Args:
            event_id: The event ID to update.
            **kwargs: Fields to update (service_date, odometer, cost, etc.).

        Returns:
            Updated MaintenanceEvent if found, None otherwise.
        """
        return self.repo.update_maintenance_event(event_id, **kwargs)

    def delete_event(self, event_id: int) -> bool:
        """Delete a maintenance event.

        Args:
            event_id: The event ID to delete.

        Returns:
            True if deleted, False otherwise.
        """
        return self.repo.delete_maintenance_event(event_id)

    def close(self) -> None:
        """Close database connection."""
        self.repo.close()
