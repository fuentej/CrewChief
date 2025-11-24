"""Tests for Pydantic models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from crewchief.models import (
    Car,
    GarageSnapshot,
    MaintenanceEvent,
    MaintenanceSuggestion,
    Priority,
    ServiceType,
    TrackPrepChecklist,
    UsageType,
)


class TestUsageType:
    """Test UsageType enum."""

    def test_all_values(self):
        """Test all enum values are accessible."""
        assert UsageType.DAILY == "daily"
        assert UsageType.TRACK == "track"
        assert UsageType.PROJECT == "project"
        assert UsageType.SHOW == "show"
        assert UsageType.OTHER == "other"


class TestServiceType:
    """Test ServiceType enum."""

    def test_all_values(self):
        """Test all enum values are accessible."""
        assert ServiceType.OIL_CHANGE == "oil_change"
        assert ServiceType.BRAKES == "brakes"
        assert ServiceType.TIRES == "tires"
        assert ServiceType.FLUIDS == "fluids"
        assert ServiceType.INSPECTION == "inspection"
        assert ServiceType.MOD == "mod"
        assert ServiceType.OTHER == "other"


class TestPriority:
    """Test Priority enum."""

    def test_all_values(self):
        """Test all enum values are accessible."""
        assert Priority.HIGH == "high"
        assert Priority.MEDIUM == "medium"
        assert Priority.LOW == "low"


class TestCar:
    """Test Car model."""

    def test_valid_car_minimal(self):
        """Test creating a car with minimal required fields."""
        car = Car(
            year=2020,
            make="Honda",
            model="Civic",
            usage_type=UsageType.DAILY,
        )
        assert car.year == 2020
        assert car.make == "Honda"
        assert car.model == "Civic"
        assert car.usage_type == UsageType.DAILY
        assert car.id is None
        assert car.nickname is None
        assert car.trim is None
        assert car.vin is None
        assert car.current_odometer is None
        assert car.notes is None
        assert isinstance(car.created_at, datetime)
        assert isinstance(car.updated_at, datetime)

    def test_valid_car_full(self):
        """Test creating a car with all fields."""
        now = datetime.now()
        car = Car(
            id=1,
            nickname="Daily Driver",
            year=2020,
            make="Honda",
            model="Civic",
            trim="Si",
            vin="1HGBH41JXMN109186",
            usage_type=UsageType.DAILY,
            current_odometer=50000,
            notes="Great condition",
            created_at=now,
            updated_at=now,
        )
        assert car.id == 1
        assert car.nickname == "Daily Driver"
        assert car.year == 2020
        assert car.make == "Honda"
        assert car.model == "Civic"
        assert car.trim == "Si"
        assert car.vin == "1HGBH41JXMN109186"
        assert car.usage_type == UsageType.DAILY
        assert car.current_odometer == 50000
        assert car.notes == "Great condition"
        assert car.created_at == now
        assert car.updated_at == now

    def test_display_name_without_nickname(self):
        """Test display_name() method without nickname."""
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        assert car.display_name() == "2020 Honda Civic"

    def test_display_name_with_nickname(self):
        """Test display_name() method with nickname."""
        car = Car(
            nickname="Daily Driver",
            year=2020,
            make="Honda",
            model="Civic",
            usage_type=UsageType.DAILY,
        )
        assert car.display_name() == "Daily Driver (2020 Honda Civic)"

    def test_invalid_year_too_low(self):
        """Test year validation rejects values below 1900."""
        with pytest.raises(ValidationError) as exc_info:
            Car(year=1899, make="Ford", model="Model T", usage_type=UsageType.OTHER)
        assert "year" in str(exc_info.value)

    def test_invalid_year_too_high(self):
        """Test year validation rejects values above 2100."""
        with pytest.raises(ValidationError) as exc_info:
            Car(year=2101, make="Tesla", model="Cybertruck", usage_type=UsageType.DAILY)
        assert "year" in str(exc_info.value)

    def test_invalid_odometer_negative(self):
        """Test odometer validation rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            Car(
                year=2020,
                make="Honda",
                model="Civic",
                usage_type=UsageType.DAILY,
                current_odometer=-1000,
            )
        assert "current_odometer" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Car(year=2020)
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "make" in field_names
        assert "model" in field_names
        assert "usage_type" in field_names

    def test_invalid_usage_type(self):
        """Test that invalid usage_type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Car(
                year=2020,
                make="Honda",
                model="Civic",
                usage_type="invalid_type",  # type: ignore
            )
        assert "usage_type" in str(exc_info.value)


class TestMaintenanceEvent:
    """Test MaintenanceEvent model."""

    def test_valid_event_minimal(self):
        """Test creating an event with minimal required fields."""
        event = MaintenanceEvent(
            car_id=1,
            service_date=date(2024, 1, 15),
            service_type=ServiceType.OIL_CHANGE,
        )
        assert event.car_id == 1
        assert event.service_date == date(2024, 1, 15)
        assert event.service_type == ServiceType.OIL_CHANGE
        assert event.id is None
        assert event.odometer is None
        assert event.description is None
        assert event.parts is None
        assert event.cost is None
        assert event.location is None
        assert isinstance(event.created_at, datetime)

    def test_valid_event_full(self):
        """Test creating an event with all fields."""
        now = datetime.now()
        event = MaintenanceEvent(
            id=1,
            car_id=1,
            service_date=date(2024, 1, 15),
            odometer=50000,
            service_type=ServiceType.OIL_CHANGE,
            description="Full synthetic oil change",
            parts="Mobil 1 5W-30, OEM filter",
            cost=89.99,
            location="Local Shop",
            created_at=now,
        )
        assert event.id == 1
        assert event.car_id == 1
        assert event.service_date == date(2024, 1, 15)
        assert event.odometer == 50000
        assert event.service_type == ServiceType.OIL_CHANGE
        assert event.description == "Full synthetic oil change"
        assert event.parts == "Mobil 1 5W-30, OEM filter"
        assert event.cost == 89.99
        assert event.location == "Local Shop"
        assert event.created_at == now

    def test_invalid_odometer_negative(self):
        """Test odometer validation rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            MaintenanceEvent(
                car_id=1,
                service_date=date(2024, 1, 15),
                service_type=ServiceType.OIL_CHANGE,
                odometer=-100,
            )
        assert "odometer" in str(exc_info.value)

    def test_invalid_cost_negative(self):
        """Test cost validation rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            MaintenanceEvent(
                car_id=1,
                service_date=date(2024, 1, 15),
                service_type=ServiceType.OIL_CHANGE,
                cost=-50.0,
            )
        assert "cost" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            MaintenanceEvent(car_id=1)
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "service_date" in field_names
        assert "service_type" in field_names

    def test_invalid_service_type(self):
        """Test that invalid service_type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            MaintenanceEvent(
                car_id=1,
                service_date=date(2024, 1, 15),
                service_type="invalid_type",  # type: ignore
            )
        assert "service_type" in str(exc_info.value)


class TestGarageSnapshot:
    """Test GarageSnapshot model."""

    def test_empty_snapshot(self):
        """Test creating an empty garage snapshot."""
        snapshot = GarageSnapshot(cars=[], maintenance_events=[])
        assert snapshot.cars == []
        assert snapshot.maintenance_events == []

    def test_snapshot_with_data(self):
        """Test creating a snapshot with cars and events."""
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        event = MaintenanceEvent(
            car_id=1,
            service_date=date(2024, 1, 15),
            service_type=ServiceType.OIL_CHANGE,
        )
        snapshot = GarageSnapshot(cars=[car], maintenance_events=[event])
        assert len(snapshot.cars) == 1
        assert len(snapshot.maintenance_events) == 1
        assert snapshot.cars[0] == car
        assert snapshot.maintenance_events[0] == event


class TestMaintenanceSuggestion:
    """Test MaintenanceSuggestion model."""

    def test_valid_suggestion(self):
        """Test creating a valid maintenance suggestion."""
        suggestion = MaintenanceSuggestion(
            car_id=1,
            car_label="2020 Honda Civic",
            suggested_actions=["Check tire pressure", "Inspect brake pads"],
            priority=Priority.MEDIUM,
            reasoning="Regular maintenance items for this mileage",
        )
        assert suggestion.car_id == 1
        assert suggestion.car_label == "2020 Honda Civic"
        assert len(suggestion.suggested_actions) == 2
        assert suggestion.priority == Priority.MEDIUM
        assert "Regular maintenance" in suggestion.reasoning

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            MaintenanceSuggestion(car_id=1)
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "car_label" in field_names
        assert "suggested_actions" in field_names
        assert "priority" in field_names
        assert "reasoning" in field_names

    def test_invalid_priority(self):
        """Test that invalid priority raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            MaintenanceSuggestion(
                car_id=1,
                car_label="2020 Honda Civic",
                suggested_actions=["Check oil"],
                priority="urgent",  # type: ignore
                reasoning="Test",
            )
        assert "priority" in str(exc_info.value)


class TestTrackPrepChecklist:
    """Test TrackPrepChecklist model."""

    def test_valid_checklist(self):
        """Test creating a valid track prep checklist."""
        checklist = TrackPrepChecklist(
            car_label="2020 Porsche 911 GT3",
            critical_items=["Check brake pads", "Inspect brake fluid"],
            recommended_items=["Set tire pressures", "Torque wheel nuts"],
            notes="Brakes serviced 30 days ago",
        )
        assert checklist.car_label == "2020 Porsche 911 GT3"
        assert len(checklist.critical_items) == 2
        assert len(checklist.recommended_items) == 2
        assert checklist.notes == "Brakes serviced 30 days ago"

    def test_checklist_without_notes(self):
        """Test creating a checklist without optional notes."""
        checklist = TrackPrepChecklist(
            car_label="2020 Porsche 911 GT3",
            critical_items=["Check brake pads"],
            recommended_items=["Set tire pressures"],
        )
        assert checklist.notes is None

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TrackPrepChecklist(car_label="2020 Porsche 911 GT3")
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "critical_items" in field_names
        assert "recommended_items" in field_names

    def test_empty_lists_allowed(self):
        """Test that empty lists are valid for item fields."""
        checklist = TrackPrepChecklist(
            car_label="2020 Honda Civic",
            critical_items=[],
            recommended_items=[],
        )
        assert checklist.critical_items == []
        assert checklist.recommended_items == []
