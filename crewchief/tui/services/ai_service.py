"""AI service adapter - wraps LLM operations with graceful fallback."""

from crewchief.db import GarageRepository
from crewchief.models import GarageSnapshot, MaintenanceSuggestion, TrackPrepChecklist, Car, MaintenanceEvent
from crewchief.settings import get_settings
from crewchief.llm import (
    generate_garage_summary,
    generate_maintenance_suggestions,
    generate_track_prep_checklist,
    LLMUnavailableError,
    LLMError,
)


class AIService:
    """Service layer for AI/LLM operations with error handling."""

    def __init__(self):
        """Initialize the AI service with repository."""
        settings = get_settings()
        db_path = settings.get_expanded_db_path()
        self.repo = GarageRepository(db_path)
        self.llm_available = True

    def get_garage_summary(self, car_id: int | None = None) -> str:
        """Get AI-generated garage or car summary.

        Args:
            car_id: If provided, summarize specific car. Otherwise, entire garage.

        Returns:
            Summary text. Returns fallback message if LLM unavailable.
        """
        try:
            if car_id is not None:
                car = self.repo.get_car(car_id)
                if car is None:
                    return f"Car with ID {car_id} not found."

                events = self.repo.get_maintenance_for_car(car_id)
                parts = self.repo.get_car_parts(car_id)
                snapshot = GarageSnapshot(cars=[car], maintenance_events=events)
            else:
                cars = self.repo.get_cars()
                if not cars:
                    return "No vehicles in garage."

                all_events = self.repo.get_all_maintenance()
                parts = []
                for car in cars:
                    parts.extend(self.repo.get_car_parts(car.id))

                snapshot = GarageSnapshot(cars=cars, maintenance_events=all_events)

            return generate_garage_summary(snapshot, parts=parts if parts else None)

        except LLMUnavailableError as e:
            self.llm_available = False
            return f"AI unavailable: {str(e)}"
        except LLMError as e:
            return f"AI error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def get_maintenance_suggestions(self, car_id: int | None = None) -> list[MaintenanceSuggestion] | str:
        """Get AI-generated maintenance suggestions.

        Args:
            car_id: If provided, suggestions for specific car. Otherwise, all cars.

        Returns:
            List of MaintenanceSuggestion objects, or error message string.
        """
        try:
            if car_id is not None:
                car = self.repo.get_car(car_id)
                if car is None:
                    return f"Car with ID {car_id} not found."

                events = self.repo.get_maintenance_for_car(car_id)
                parts = self.repo.get_car_parts(car_id)
                snapshot = GarageSnapshot(cars=[car], maintenance_events=events)
            else:
                cars = self.repo.get_cars()
                if not cars:
                    return "No vehicles in garage."

                all_events = self.repo.get_all_maintenance()
                parts = []
                for car in cars:
                    parts.extend(self.repo.get_car_parts(car.id))

                snapshot = GarageSnapshot(cars=cars, maintenance_events=all_events)

            return generate_maintenance_suggestions(snapshot, parts=parts if parts else None)

        except LLMUnavailableError as e:
            self.llm_available = False
            return f"AI unavailable: {str(e)}"
        except LLMError as e:
            return f"AI error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def get_track_prep_checklist(self, car_id: int) -> TrackPrepChecklist | str:
        """Get AI-generated track day preparation checklist.

        Args:
            car_id: The vehicle ID to prepare.

        Returns:
            TrackPrepChecklist object, or error message string.
        """
        try:
            car = self.repo.get_car(car_id)
            if car is None:
                return f"Car with ID {car_id} not found."

            events = self.repo.get_maintenance_for_car(car_id)
            return generate_track_prep_checklist(car, events)

        except LLMUnavailableError as e:
            self.llm_available = False
            return f"AI unavailable: {str(e)}"
        except LLMError as e:
            return f"AI error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def is_llm_available(self) -> bool:
        """Check if LLM service is available.

        Returns:
            True if LLM was successfully used, False if not.
        """
        return self.llm_available

    def close(self) -> None:
        """Close database connection."""
        self.repo.close()
