"""Pydantic data models for CrewChief."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


# Enumerations
class UsageType(str, Enum):
    """How the vehicle is primarily used."""

    DAILY = "daily"
    TRACK = "track"
    PROJECT = "project"
    SHOW = "show"
    OTHER = "other"


class ServiceType(str, Enum):
    """Type of maintenance service performed."""

    OIL_CHANGE = "oil_change"
    BRAKES = "brakes"
    TIRES = "tires"
    FLUIDS = "fluids"
    INSPECTION = "inspection"
    MOD = "mod"
    OTHER = "other"


class Priority(str, Enum):
    """Priority level for maintenance suggestions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PartCategory(str, Enum):
    """Category of car part."""

    OIL = "oil"
    OIL_FILTER = "oil_filter"
    TIRES = "tires"
    WIPERS = "wipers"
    AIR_FILTER = "air_filter"
    CABIN_FILTER = "cabin_filter"
    BRAKE_PADS = "brake_pads"
    BRAKE_FLUID = "brake_fluid"
    COOLANT = "coolant"
    TRANSMISSION_FLUID = "transmission_fluid"
    SPARK_PLUGS = "spark_plugs"
    BATTERY = "battery"
    OTHER = "other"


# Core Data Models
class Car(BaseModel):
    """Represents a vehicle in the garage."""

    id: int | None = None
    nickname: str | None = None
    year: int = Field(ge=1900, le=2100)
    make: str
    model: str
    trim: str | None = None
    vin: str | None = None
    usage_type: UsageType
    current_odometer: int | None = Field(default=None, ge=0)
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def display_name(self) -> str:
        """Return a human-readable name for the car."""
        base = f"{self.year} {self.make} {self.model}"
        if self.nickname:
            return f"{self.nickname} ({base})"
        return base


class MaintenanceEvent(BaseModel):
    """Represents a maintenance event for a vehicle."""

    id: int | None = None
    car_id: int
    service_date: date
    odometer: int | None = Field(default=None, ge=0)
    service_type: ServiceType
    description: str | None = None
    parts: str | None = None
    cost: float | None = Field(default=None, ge=0)
    location: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class CarPart(BaseModel):
    """Represents a part in a car's parts profile."""

    id: int | None = None
    car_id: int
    part_category: PartCategory
    brand: str | None = None
    part_number: str | None = None
    size_spec: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# LLM-Specific Models (Not Persisted)
class GarageSnapshot(BaseModel):
    """Snapshot of the garage for LLM context."""

    cars: list[Car]
    maintenance_events: list[MaintenanceEvent]


class MaintenanceSuggestion(BaseModel):
    """AI-generated maintenance suggestion for a specific car."""

    car_id: int
    car_label: str
    suggested_actions: list[str]
    priority: Priority
    reasoning: str


class TrackPrepChecklist(BaseModel):
    """AI-generated track preparation checklist."""

    car_label: str
    critical_items: list[str]
    recommended_items: list[str]
    notes: str | None = None
