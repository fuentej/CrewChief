"""Tests for database repository layer."""

from datetime import date, datetime

import pytest

from crewchief.db import GarageRepository
from crewchief.models import Car, MaintenanceEvent, ServiceType, UsageType


@pytest.fixture
def repo():
    """Create an in-memory database repository for testing."""
    repository = GarageRepository(":memory:")
    repository.init_db()
    yield repository
    repository.close()


class TestGarageRepository:
    """Test GarageRepository database operations."""

    def test_init_db(self, repo):
        """Test that database initialization creates tables."""
        conn = repo._get_connection()
        cursor = conn.cursor()

        # Check cars table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cars'"
        )
        assert cursor.fetchone() is not None

        # Check maintenance_events table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='maintenance_events'"
        )
        assert cursor.fetchone() is not None

    def test_add_car_minimal(self, repo):
        """Test adding a car with minimal fields."""
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        result = repo.add_car(car)

        assert result.id is not None
        assert result.year == 2020
        assert result.make == "Honda"
        assert result.model == "Civic"
        assert result.usage_type == UsageType.DAILY

    def test_add_car_full(self, repo):
        """Test adding a car with all fields."""
        car = Car(
            nickname="Daily Driver",
            year=2020,
            make="Honda",
            model="Civic",
            trim="Si",
            vin="1HGBH41JXMN109186",
            usage_type=UsageType.DAILY,
            current_odometer=50000,
            notes="Great condition",
        )
        result = repo.add_car(car)

        assert result.id is not None
        assert result.nickname == "Daily Driver"
        assert result.trim == "Si"
        assert result.vin == "1HGBH41JXMN109186"
        assert result.current_odometer == 50000
        assert result.notes == "Great condition"

    def test_get_cars_empty(self, repo):
        """Test getting cars from empty database."""
        cars = repo.get_cars()
        assert cars == []

    def test_get_cars_multiple(self, repo):
        """Test getting multiple cars."""
        car1 = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        car2 = Car(
            year=2024, make="Porsche", model="911 GT3", usage_type=UsageType.TRACK
        )

        repo.add_car(car1)
        repo.add_car(car2)

        cars = repo.get_cars()
        assert len(cars) == 2
        assert cars[0].make == "Honda"
        assert cars[1].make == "Porsche"

    def test_get_car_by_id(self, repo):
        """Test getting a specific car by ID."""
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added = repo.add_car(car)

        retrieved = repo.get_car(added.id)
        assert retrieved is not None
        assert retrieved.id == added.id
        assert retrieved.make == "Honda"
        assert retrieved.model == "Civic"

    def test_get_car_nonexistent(self, repo):
        """Test getting a car that doesn't exist."""
        result = repo.get_car(999)
        assert result is None

    def test_update_car(self, repo):
        """Test updating a car."""
        car = Car(
            year=2020,
            make="Honda",
            model="Civic",
            usage_type=UsageType.DAILY,
            current_odometer=50000,
        )
        added = repo.add_car(car)

        # Update odometer and notes
        added.current_odometer = 60000
        added.notes = "Oil changed"
        updated = repo.update_car(added)

        # Verify update
        retrieved = repo.get_car(added.id)
        assert retrieved.current_odometer == 60000
        assert retrieved.notes == "Oil changed"
        assert isinstance(updated.updated_at, datetime)

    def test_add_maintenance_event(self, repo):
        """Test adding a maintenance event."""
        # Add a car first
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        # Add maintenance event
        event = MaintenanceEvent(
            car_id=added_car.id,
            service_date=date(2024, 1, 15),
            odometer=50000,
            service_type=ServiceType.OIL_CHANGE,
            description="Full synthetic oil change",
        )
        result = repo.add_maintenance_event(event)

        assert result.id is not None
        assert result.car_id == added_car.id
        assert result.service_date == date(2024, 1, 15)
        assert result.odometer == 50000
        assert result.service_type == ServiceType.OIL_CHANGE

    def test_get_maintenance_for_car_empty(self, repo):
        """Test getting maintenance events for a car with no events."""
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        events = repo.get_maintenance_for_car(added_car.id)
        assert events == []

    def test_get_maintenance_for_car_multiple(self, repo):
        """Test getting multiple maintenance events for a car."""
        # Add a car
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        # Add multiple events
        event1 = MaintenanceEvent(
            car_id=added_car.id,
            service_date=date(2024, 1, 15),
            service_type=ServiceType.OIL_CHANGE,
        )
        event2 = MaintenanceEvent(
            car_id=added_car.id,
            service_date=date(2024, 2, 20),
            service_type=ServiceType.TIRES,
        )

        repo.add_maintenance_event(event1)
        repo.add_maintenance_event(event2)

        events = repo.get_maintenance_for_car(added_car.id)
        assert len(events) == 2
        # Should be ordered by service_date DESC
        assert events[0].service_type == ServiceType.TIRES
        assert events[1].service_type == ServiceType.OIL_CHANGE

    def test_get_maintenance_for_car_with_limit(self, repo):
        """Test getting maintenance events with a limit."""
        # Add a car
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        # Add three events
        for i in range(3):
            event = MaintenanceEvent(
                car_id=added_car.id,
                service_date=date(2024, 1, 10 + i),
                service_type=ServiceType.OIL_CHANGE,
            )
            repo.add_maintenance_event(event)

        # Get only the most recent 2
        events = repo.get_maintenance_for_car(added_car.id, limit=2)
        assert len(events) == 2

    def test_get_all_maintenance_empty(self, repo):
        """Test getting all maintenance events from empty database."""
        events = repo.get_all_maintenance()
        assert events == []

    def test_get_all_maintenance_multiple_cars(self, repo):
        """Test getting all maintenance events across multiple cars."""
        # Add two cars
        car1 = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        car2 = Car(
            year=2024, make="Porsche", model="911 GT3", usage_type=UsageType.TRACK
        )
        added_car1 = repo.add_car(car1)
        added_car2 = repo.add_car(car2)

        # Add events for both cars
        event1 = MaintenanceEvent(
            car_id=added_car1.id,
            service_date=date(2024, 1, 15),
            service_type=ServiceType.OIL_CHANGE,
        )
        event2 = MaintenanceEvent(
            car_id=added_car2.id,
            service_date=date(2024, 2, 20),
            service_type=ServiceType.BRAKES,
        )

        repo.add_maintenance_event(event1)
        repo.add_maintenance_event(event2)

        events = repo.get_all_maintenance()
        assert len(events) == 2
        # Should be ordered by service_date DESC
        assert events[0].service_type == ServiceType.BRAKES
        assert events[1].service_type == ServiceType.OIL_CHANGE

    def test_get_all_maintenance_with_limit(self, repo):
        """Test getting all maintenance events with a limit."""
        # Add a car
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        # Add five events
        for i in range(5):
            event = MaintenanceEvent(
                car_id=added_car.id,
                service_date=date(2024, 1, 10 + i),
                service_type=ServiceType.OIL_CHANGE,
            )
            repo.add_maintenance_event(event)

        # Get only the most recent 3
        events = repo.get_all_maintenance(limit=3)
        assert len(events) == 3

    def test_connection_management(self):
        """Test connection lifecycle."""
        # Create a fresh repo without using the fixture
        test_repo = GarageRepository(":memory:")

        # Connection should be None initially
        assert test_repo.conn is None

        # Connection should be created on first access
        conn = test_repo._get_connection()
        assert test_repo.conn is not None
        assert conn is test_repo.conn

        # Close should clear connection
        test_repo.close()
        assert test_repo.conn is None

    def test_row_to_car_conversion(self, repo):
        """Test that database rows are correctly converted to Car models."""
        car = Car(
            nickname="Test",
            year=2020,
            make="Honda",
            model="Civic",
            trim="Si",
            vin="1HGBH41JXMN109186",
            usage_type=UsageType.DAILY,
            current_odometer=50000,
            notes="Test notes",
        )
        added = repo.add_car(car)

        # Retrieve and verify all fields
        retrieved = repo.get_car(added.id)
        assert retrieved.id == added.id
        assert retrieved.nickname == "Test"
        assert retrieved.year == 2020
        assert retrieved.make == "Honda"
        assert retrieved.model == "Civic"
        assert retrieved.trim == "Si"
        assert retrieved.vin == "1HGBH41JXMN109186"
        assert retrieved.usage_type == UsageType.DAILY
        assert retrieved.current_odometer == 50000
        assert retrieved.notes == "Test notes"
        assert isinstance(retrieved.created_at, datetime)
        assert isinstance(retrieved.updated_at, datetime)

    def test_row_to_maintenance_event_conversion(self, repo):
        """Test that database rows are correctly converted to MaintenanceEvent models."""
        # Add a car first
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        # Add maintenance event with all fields
        event = MaintenanceEvent(
            car_id=added_car.id,
            service_date=date(2024, 1, 15),
            odometer=50000,
            service_type=ServiceType.OIL_CHANGE,
            description="Full synthetic",
            parts="Mobil 1 5W-30",
            cost=89.99,
            location="Local Shop",
        )
        added = repo.add_maintenance_event(event)

        # Retrieve and verify all fields
        retrieved = repo.get_maintenance_for_car(added_car.id)[0]
        assert retrieved.id == added.id
        assert retrieved.car_id == added_car.id
        assert retrieved.service_date == date(2024, 1, 15)
        assert retrieved.odometer == 50000
        assert retrieved.service_type == ServiceType.OIL_CHANGE
        assert retrieved.description == "Full synthetic"
        assert retrieved.parts == "Mobil 1 5W-30"
        assert retrieved.cost == 89.99
        assert retrieved.location == "Local Shop"
        assert isinstance(retrieved.created_at, datetime)
