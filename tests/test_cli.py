"""Tests for CLI commands."""

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from crewchief.cli import app
from crewchief.db import GarageRepository
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

runner = CliRunner()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    repo = GarageRepository(db_path)
    repo.init_db()
    yield db_path, repo
    repo.close()

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


def create_settings_mock(db_path: str) -> Mock:
    """Helper to create a properly configured settings mock."""
    settings_mock = Mock()
    settings_mock.db_path = db_path
    settings_mock.get_expanded_db_path.return_value = Path(db_path)
    settings_mock.ensure_config_dir.return_value = None
    return settings_mock


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_version_command(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "CrewChief" in result.stdout

    def test_help_command(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "CrewChief" in result.stdout


class TestInitGarage:
    """Test init-garage command."""

    def test_init_garage_creates_database(self):
        """Test that init-garage creates database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            with patch("crewchief.cli.get_settings") as mock_settings:
                settings_mock = Mock()
                settings_mock.db_path = str(db_path)
                settings_mock.get_expanded_db_path.return_value = db_path
                settings_mock.ensure_config_dir.return_value = None
                mock_settings.return_value = settings_mock
                result = runner.invoke(app, ["init-garage"])

                assert result.exit_code == 0
                assert db_path.exists()
                assert "initialized" in result.stdout.lower()


class TestAddCar:
    """Test add-car command."""

    def test_add_car_interactive(self, temp_db):
        """Test adding a car interactively."""
        db_path, repo = temp_db

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            # Simulate user input: Year, Make, Model, Trim (empty), VIN (empty), Usage type, Odometer (empty), Notes (empty)
            result = runner.invoke(
                app,
                ["add-car"],
                input="2020\nHonda\nCivic\n\n\ndaily\n\n\n",
            )

            assert result.exit_code == 0

            # Verify car was added
            cars = repo.get_cars()
            assert len(cars) == 1
            assert cars[0].make == "Honda"
            assert cars[0].model == "Civic"

    def test_add_car_with_flags(self, temp_db):
        """Test adding a car with command-line flags."""
        db_path, repo = temp_db

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            # Flags provide year, make, model, usage; still need input for optional prompts: Trim, VIN, Odometer, Notes
            result = runner.invoke(
                app,
                [
                    "add-car",
                    "--year",
                    "2020",
                    "--make",
                    "Honda",
                    "--model",
                    "Civic",
                    "--usage",
                    "daily",
                ],
                input="\n\n\n\n",  # Trim (skip), VIN (skip), Odometer (skip), Notes (skip)
            )

            assert result.exit_code == 0

            # Verify car was added
            cars = repo.get_cars()
            assert len(cars) == 1
            assert cars[0].year == 2020
            assert cars[0].make == "Honda"


class TestListCars:
    """Test list-cars command."""

    def test_list_cars_empty(self, temp_db):
        """Test listing cars when garage is empty."""
        db_path, _ = temp_db

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["list-cars"])

            assert result.exit_code == 0
            assert "No cars" in result.stdout or "empty" in result.stdout.lower()

    def test_list_cars_with_data(self, temp_db):
        """Test listing cars with data."""
        db_path, repo = temp_db

        # Add test cars
        car1 = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        car2 = Car(
            year=2024, make="Porsche", model="911 GT3", usage_type=UsageType.TRACK
        )
        repo.add_car(car1)
        repo.add_car(car2)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["list-cars"])

            assert result.exit_code == 0
            assert "Honda" in result.stdout
            assert "Porsche" in result.stdout


class TestShowCar:
    """Test show-car command."""

    def test_show_car_success(self, temp_db):
        """Test showing a specific car."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            nickname="Daily Driver",
            year=2020,
            make="Honda",
            model="Civic",
            usage_type=UsageType.DAILY,
        )
        added = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["show-car", str(added.id)])

            assert result.exit_code == 0
            assert "Honda" in result.stdout
            assert "Civic" in result.stdout
            assert "Daily Driver" in result.stdout

    def test_show_car_not_found(self, temp_db):
        """Test showing a car that doesn't exist."""
        db_path, _ = temp_db

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["show-car", "999"])

            assert result.exit_code != 0
            assert "not found" in result.stdout.lower() or "Error" in result.stdout


class TestUpdateCar:
    """Test update-car command."""

    def test_update_car_vin(self, temp_db):
        """Test updating a car's VIN."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2017,
            make="Toyota",
            model="86",
            usage_type=UsageType.TRACK,
        )
        car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(
                app,
                ["update-car", str(car.id), "--vin", "JF1ZNAA19H9706029"],
            )

            assert result.exit_code == 0
            assert "updated successfully" in result.stdout.lower()

            # Verify VIN was updated
            updated_car = repo.get_car(car.id)
            assert updated_car.vin == "JF1ZNAA19H9706029"

    def test_update_car_multiple_fields(self, temp_db):
        """Test updating multiple fields at once."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2017,
            make="Toyota",
            model="86",
            usage_type=UsageType.TRACK,
        )
        car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(
                app,
                [
                    "update-car",
                    str(car.id),
                    "--vin",
                    "JF1ZNAA19H9706029",
                    "--nickname",
                    "Track Beast",
                    "--odometer",
                    "50000",
                    "--notes",
                    "Track ready",
                ],
            )

            assert result.exit_code == 0

            # Verify all fields were updated
            updated_car = repo.get_car(car.id)
            assert updated_car.vin == "JF1ZNAA19H9706029"
            assert updated_car.nickname == "Track Beast"
            assert updated_car.current_odometer == 50000
            assert updated_car.notes == "Track ready"

    def test_update_car_not_found(self, temp_db):
        """Test updating a non-existent car."""
        db_path, repo = temp_db

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["update-car", "999", "--vin", "TEST123"])

            assert result.exit_code != 0
            assert "not found" in result.stdout.lower() or "Error" in result.stdout

    def test_update_car_no_fields(self, temp_db):
        """Test update-car with no fields specified."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2017,
            make="Toyota",
            model="86",
            usage_type=UsageType.TRACK,
        )
        car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["update-car", str(car.id)])

            assert result.exit_code == 0
            assert "no fields" in result.stdout.lower()


class TestRemoveCar:
    """Test remove-car command."""

    def test_remove_car_with_confirmation(self, temp_db):
        """Test removing a car with confirmation."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2017,
            make="Toyota",
            model="86",
            usage_type=UsageType.TRACK,
        )
        car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            # Simulate user confirming deletion
            result = runner.invoke(app, ["remove-car", str(car.id)], input="y\n")

            assert result.exit_code == 0
            assert "deleted successfully" in result.stdout.lower()

            # Verify car was deleted
            deleted_car = repo.get_car(car.id)
            assert deleted_car is None

    def test_remove_car_with_force(self, temp_db):
        """Test removing a car with --force flag."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2017,
            make="Toyota",
            model="86",
            usage_type=UsageType.TRACK,
        )
        car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["remove-car", str(car.id), "--force"])

            assert result.exit_code == 0
            assert "deleted successfully" in result.stdout.lower()

            # Verify car was deleted
            deleted_car = repo.get_car(car.id)
            assert deleted_car is None

    def test_remove_car_cancel(self, temp_db):
        """Test cancelling car removal."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2017,
            make="Toyota",
            model="86",
            usage_type=UsageType.TRACK,
        )
        car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            # Simulate user cancelling deletion
            result = runner.invoke(app, ["remove-car", str(car.id)], input="n\n")

            assert result.exit_code == 0
            assert "cancelled" in result.stdout.lower()

            # Verify car still exists
            existing_car = repo.get_car(car.id)
            assert existing_car is not None

    def test_remove_car_with_maintenance(self, temp_db):
        """Test removing a car that has maintenance history."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2017,
            make="Toyota",
            model="86",
            usage_type=UsageType.TRACK,
        )
        car = repo.add_car(car)

        # Add maintenance event
        event = MaintenanceEvent(
            car_id=car.id,
            service_date=date.today(),
            service_type=ServiceType.OIL_CHANGE,
        )
        repo.add_maintenance_event(event)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["remove-car", str(car.id), "--force"])

            assert result.exit_code == 0
            assert "deleted successfully" in result.stdout.lower()

            # Verify car and maintenance were deleted
            deleted_car = repo.get_car(car.id)
            assert deleted_car is None
            events = repo.get_maintenance_for_car(car.id)
            assert len(events) == 0

    def test_remove_car_not_found(self, temp_db):
        """Test removing a non-existent car."""
        db_path, repo = temp_db

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["remove-car", "999", "--force"])

            assert result.exit_code != 0
            assert "not found" in result.stdout.lower() or "Error" in result.stdout


class TestLogService:
    """Test log-service command."""

    def test_log_service_interactive(self, temp_db):
        """Test logging maintenance interactively."""
        db_path, repo = temp_db

        # Add test car
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(
                app,
                ["log-service", str(added_car.id), "--service-date", "2024-01-15"],
                input="oil_change\ny\n50000\nFull synthetic\n",
            )

            assert result.exit_code == 0

            # Verify event was added
            events = repo.get_maintenance_for_car(added_car.id)
            assert len(events) == 1
            assert events[0].service_type == ServiceType.OIL_CHANGE

    def test_log_service_with_flags(self, temp_db):
        """Test logging maintenance with command-line flags."""
        db_path, repo = temp_db

        # Add test car
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(
                app,
                [
                    "log-service",
                    str(added_car.id),
                    "--service-date",
                    "2024-01-15",
                    "--service-type",
                    "oil_change",
                    "--odometer",
                    "50000",
                ],
                input="\n",  # Empty description
            )

            assert result.exit_code == 0

            # Verify event was added
            events = repo.get_maintenance_for_car(added_car.id)
            assert len(events) == 1


class TestHistory:
    """Test history command."""

    def test_history_empty(self, temp_db):
        """Test history when no maintenance events exist."""
        db_path, repo = temp_db

        # Add test car
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["history", str(added_car.id)])

            assert result.exit_code == 0
            assert "No maintenance" in result.stdout or "empty" in result.stdout.lower()

    def test_history_with_events(self, temp_db):
        """Test history with maintenance events."""
        db_path, repo = temp_db

        # Add test car and events
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        added_car = repo.add_car(car)

        event = MaintenanceEvent(
            car_id=added_car.id,
            service_date=date(2024, 1, 15),
            service_type=ServiceType.OIL_CHANGE,
            description="Full synthetic",
        )
        repo.add_maintenance_event(event)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["history", str(added_car.id)])

            assert result.exit_code == 0
            assert "oil" in result.stdout.lower()


class TestLLMCommands:
    """Test LLM-powered commands."""

    def test_summary_command(self, temp_db):
        """Test garage summary command."""
        db_path, repo = temp_db

        # Add test data
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            with patch("crewchief.cli.generate_garage_summary") as mock_summary:
                mock_summary.return_value = "Your garage looks great!"

                result = runner.invoke(app, ["summary"])

                assert result.exit_code == 0
                assert "garage" in result.stdout.lower()

    def test_summary_llm_unavailable(self, temp_db):
        """Test summary command when LLM is unavailable."""
        db_path, repo = temp_db

        # Add a car so the command actually tries to generate a summary
        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            with patch("crewchief.cli.generate_garage_summary") as mock_summary:
                from crewchief.llm import LLMUnavailableError

                mock_summary.side_effect = LLMUnavailableError("LLM not running")

                result = runner.invoke(app, ["summary"])

                assert result.exit_code != 0
                assert "unavailable" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_suggest_maint_command(self, temp_db):
        """Test maintenance suggestions command."""
        db_path, repo = temp_db

        # Add test data
        car = Car(id=1, year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            with patch("crewchief.cli.generate_maintenance_suggestions") as mock_suggest:
                mock_suggest.return_value = [
                    MaintenanceSuggestion(
                        car_id=1,
                        car_label="2020 Honda Civic",
                        suggested_actions=["Check oil"],
                        priority=Priority.MEDIUM,
                        reasoning="Regular maintenance",
                    )
                ]

                result = runner.invoke(app, ["suggest-maint"])

                assert result.exit_code == 0
                assert "Honda" in result.stdout or "maintenance" in result.stdout.lower()

    def test_track_prep_command(self, temp_db):
        """Test track prep command."""
        db_path, repo = temp_db

        # Add test car
        car = Car(
            year=2024, make="Porsche", model="911 GT3", usage_type=UsageType.TRACK
        )
        added_car = repo.add_car(car)

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            with patch("crewchief.cli.generate_track_prep_checklist") as mock_checklist:
                mock_checklist.return_value = TrackPrepChecklist(
                    car_label="2024 Porsche 911 GT3",
                    critical_items=["Check brakes"],
                    recommended_items=["Set tire pressure"],
                )

                result = runner.invoke(app, ["track-prep", str(added_car.id)])

                assert result.exit_code == 0
                assert "brake" in result.stdout.lower() or "tire" in result.stdout.lower()

    def test_track_prep_car_not_found(self, temp_db):
        """Test track prep with non-existent car."""
        db_path, _ = temp_db

        with patch("crewchief.cli.get_settings") as mock_settings:
            settings_mock = create_settings_mock(db_path)
            mock_settings.return_value = settings_mock

            result = runner.invoke(app, ["track-prep", "999"])

            if result.exit_code == 0:
                print(f"\nExit code: {result.exit_code}")
                print(f"stdout: {result.stdout}")
                if result.exception:
                    print(f"Exception: {result.exception}")
            assert result.exit_code != 0
            assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()
