"""Tests for LLM integration layer."""

import json
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
from pydantic import ValidationError

from crewchief.llm import (
    LLMError,
    LLMResponseError,
    LLMUnavailableError,
    generate_garage_summary,
    generate_maintenance_suggestions,
    generate_track_prep_checklist,
    llm_chat,
)
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


class TestLLMChat:
    """Test the core llm_chat function."""

    @patch("crewchief.llm.httpx.Client")
    @patch("crewchief.llm.get_settings")
    def test_llm_chat_string_response(self, mock_settings, mock_client):
        """Test LLM chat with a string response."""
        # Mock settings
        mock_settings.return_value = Mock(
            llm_enabled=True,
            llm_base_url="http://localhost:1234/v1",
            llm_model="test-model",
            llm_timeout=30,
        )

        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response from LLM"}}]
        }
        mock_response.raise_for_status = Mock()

        # Mock client context manager
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Call llm_chat
        result = llm_chat("System prompt", "User prompt")

        assert result == "Test response from LLM"
        mock_client_instance.post.assert_called_once()

    @patch("crewchief.llm.httpx.Client")
    @patch("crewchief.llm.get_settings")
    def test_llm_chat_with_schema(self, mock_settings, mock_client):
        """Test LLM chat with Pydantic schema validation."""
        # Mock settings
        mock_settings.return_value = Mock(
            llm_enabled=True,
            llm_base_url="http://localhost:1234/v1",
            llm_model="test-model",
            llm_timeout=30,
        )

        # Mock HTTP response with valid JSON
        json_response = {
            "car_label": "2020 Honda Civic",
            "critical_items": ["Check brakes"],
            "recommended_items": ["Set tire pressure"],
        }
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(json_response)}}]
        }
        mock_response.raise_for_status = Mock()

        # Mock client
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Call with schema
        result = llm_chat(
            "System prompt", "User prompt", response_schema=TrackPrepChecklist
        )

        assert isinstance(result, TrackPrepChecklist)
        assert result.car_label == "2020 Honda Civic"
        assert len(result.critical_items) == 1

    @patch("crewchief.llm.get_settings")
    def test_llm_chat_disabled(self, mock_settings):
        """Test that llm_chat raises error when LLM is disabled."""
        mock_settings.return_value = Mock(llm_enabled=False)

        with pytest.raises(LLMUnavailableError) as exc_info:
            llm_chat("System", "User")

        assert "disabled in settings" in str(exc_info.value)

    @patch("crewchief.llm.httpx.Client")
    @patch("crewchief.llm.get_settings")
    def test_llm_chat_connection_error(self, mock_settings, mock_client):
        """Test handling of connection errors."""
        mock_settings.return_value = Mock(
            llm_enabled=True,
            llm_base_url="http://localhost:1234/v1",
            llm_model="test-model",
            llm_timeout=30,
        )

        # Mock connection error
        mock_client_instance = MagicMock()
        mock_client_instance.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(LLMUnavailableError) as exc_info:
            llm_chat("System", "User")

        assert "Cannot connect" in str(exc_info.value)

    @patch("crewchief.llm.httpx.Client")
    @patch("crewchief.llm.get_settings")
    def test_llm_chat_timeout_error(self, mock_settings, mock_client):
        """Test handling of timeout errors."""
        mock_settings.return_value = Mock(
            llm_enabled=True,
            llm_base_url="http://localhost:1234/v1",
            llm_model="test-model",
            llm_timeout=30,
        )

        # Mock timeout
        mock_client_instance = MagicMock()
        mock_client_instance.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(LLMUnavailableError) as exc_info:
            llm_chat("System", "User")

        assert "timed out" in str(exc_info.value)

    @patch("crewchief.llm.httpx.Client")
    @patch("crewchief.llm.get_settings")
    def test_llm_chat_http_error(self, mock_settings, mock_client):
        """Test handling of HTTP status errors."""
        mock_settings.return_value = Mock(
            llm_enabled=True,
            llm_base_url="http://localhost:1234/v1",
            llm_model="test-model",
            llm_timeout=30,
        )

        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(LLMResponseError) as exc_info:
            llm_chat("System", "User")

        assert "500" in str(exc_info.value)

    @patch("crewchief.llm.httpx.Client")
    @patch("crewchief.llm.get_settings")
    def test_llm_chat_invalid_response_format(self, mock_settings, mock_client):
        """Test handling of invalid response format."""
        mock_settings.return_value = Mock(
            llm_enabled=True,
            llm_base_url="http://localhost:1234/v1",
            llm_model="test-model",
            llm_timeout=30,
        )

        # Mock invalid response
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "structure"}
        mock_response.raise_for_status = Mock()

        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(LLMResponseError) as exc_info:
            llm_chat("System", "User")

        assert "Invalid response format" in str(exc_info.value)

    @patch("crewchief.llm.httpx.Client")
    @patch("crewchief.llm.get_settings")
    def test_llm_chat_schema_validation_failure(self, mock_settings, mock_client):
        """Test handling of schema validation failure."""
        mock_settings.return_value = Mock(
            llm_enabled=True,
            llm_base_url="http://localhost:1234/v1",
            llm_model="test-model",
            llm_timeout=30,
        )

        # Mock response with invalid schema
        json_response = {"invalid_field": "value"}
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(json_response)}}]
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        with pytest.raises(LLMResponseError) as exc_info:
            llm_chat(
                "System", "User", response_schema=TrackPrepChecklist
            )

        assert "does not match expected schema" in str(exc_info.value)


class TestGenerateGarageSummary:
    """Test garage summary generation."""

    @patch("crewchief.llm.llm_chat")
    def test_generate_garage_summary_success(self, mock_llm_chat):
        """Test successful garage summary generation."""
        mock_llm_chat.return_value = "Your garage is looking great! You have 2 vehicles."

        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        snapshot = GarageSnapshot(cars=[car], maintenance_events=[])

        result = generate_garage_summary(snapshot)

        assert isinstance(result, str)
        assert "garage" in result.lower()
        mock_llm_chat.assert_called_once()

    @patch("crewchief.llm.llm_chat")
    def test_generate_garage_summary_invalid_response(self, mock_llm_chat):
        """Test error handling when response is not a string."""
        mock_llm_chat.return_value = {"invalid": "response"}

        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        snapshot = GarageSnapshot(cars=[car], maintenance_events=[])

        with pytest.raises(LLMResponseError) as exc_info:
            generate_garage_summary(snapshot)

        assert "Expected string response" in str(exc_info.value)


class TestGenerateMaintenanceSuggestions:
    """Test maintenance suggestion generation."""

    @patch("crewchief.llm.llm_chat")
    def test_generate_suggestions_success(self, mock_llm_chat):
        """Test successful maintenance suggestion generation."""
        mock_response = json.dumps(
            [
                {
                    "car_id": 1,
                    "car_label": "2020 Honda Civic",
                    "suggested_actions": ["Check oil", "Inspect tires"],
                    "priority": "medium",
                    "reasoning": "Regular maintenance needed",
                }
            ]
        )
        mock_llm_chat.return_value = mock_response

        car = Car(id=1, year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        snapshot = GarageSnapshot(cars=[car], maintenance_events=[])

        result = generate_maintenance_suggestions(snapshot)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], MaintenanceSuggestion)
        assert result[0].car_id == 1
        assert result[0].priority == Priority.MEDIUM

    @patch("crewchief.llm.llm_chat")
    def test_generate_suggestions_invalid_json(self, mock_llm_chat):
        """Test error handling for invalid JSON response."""
        mock_llm_chat.return_value = "Not valid JSON"

        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        snapshot = GarageSnapshot(cars=[car], maintenance_events=[])

        with pytest.raises(LLMResponseError) as exc_info:
            generate_maintenance_suggestions(snapshot)

        assert "Failed to parse" in str(exc_info.value)

    @patch("crewchief.llm.llm_chat")
    def test_generate_suggestions_not_array(self, mock_llm_chat):
        """Test error handling when response is not an array."""
        mock_llm_chat.return_value = json.dumps({"not": "an array"})

        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        snapshot = GarageSnapshot(cars=[car], maintenance_events=[])

        with pytest.raises(LLMResponseError) as exc_info:
            generate_maintenance_suggestions(snapshot)

        assert "Expected JSON array" in str(exc_info.value)

    @patch("crewchief.llm.llm_chat")
    def test_generate_suggestions_invalid_schema(self, mock_llm_chat):
        """Test error handling for schema validation failures."""
        mock_response = json.dumps([{"invalid": "schema"}])
        mock_llm_chat.return_value = mock_response

        car = Car(year=2020, make="Honda", model="Civic", usage_type=UsageType.DAILY)
        snapshot = GarageSnapshot(cars=[car], maintenance_events=[])

        with pytest.raises(LLMResponseError) as exc_info:
            generate_maintenance_suggestions(snapshot)

        assert "Failed to parse" in str(exc_info.value)


class TestGenerateTrackPrepChecklist:
    """Test track prep checklist generation."""

    @patch("crewchief.llm.llm_chat")
    def test_generate_checklist_success(self, mock_llm_chat):
        """Test successful checklist generation."""
        mock_checklist = TrackPrepChecklist(
            car_label="2024 Porsche 911 GT3",
            critical_items=["Check brake pads", "Inspect brake fluid"],
            recommended_items=["Set tire pressures", "Torque wheel nuts"],
            notes="Brakes serviced 30 days ago",
        )
        mock_llm_chat.return_value = mock_checklist

        car = Car(
            id=1,
            year=2024,
            make="Porsche",
            model="911 GT3",
            usage_type=UsageType.TRACK,
        )
        event = MaintenanceEvent(
            car_id=1,
            service_date=date(2024, 1, 15),
            service_type=ServiceType.BRAKES,
        )

        result = generate_track_prep_checklist(car, [event])

        assert isinstance(result, TrackPrepChecklist)
        assert result.car_label == "2024 Porsche 911 GT3"
        assert len(result.critical_items) == 2
        assert len(result.recommended_items) == 2

    @patch("crewchief.llm.llm_chat")
    def test_generate_checklist_invalid_response(self, mock_llm_chat):
        """Test error handling when response is not TrackPrepChecklist."""
        mock_llm_chat.return_value = "Not a checklist"

        car = Car(
            year=2024, make="Porsche", model="911 GT3", usage_type=UsageType.TRACK
        )

        with pytest.raises(LLMResponseError) as exc_info:
            generate_track_prep_checklist(car, [])

        assert "Expected TrackPrepChecklist" in str(exc_info.value)

    @patch("crewchief.llm.llm_chat")
    def test_generate_checklist_with_maintenance_history(self, mock_llm_chat):
        """Test checklist generation includes maintenance history."""
        mock_checklist = TrackPrepChecklist(
            car_label="2024 Porsche 911 GT3",
            critical_items=["Check brakes"],
            recommended_items=["Set tires"],
        )
        mock_llm_chat.return_value = mock_checklist

        car = Car(
            id=1,
            year=2024,
            make="Porsche",
            model="911 GT3",
            usage_type=UsageType.TRACK,
        )
        events = [
            MaintenanceEvent(
                car_id=1,
                service_date=date(2024, 1, 15),
                service_type=ServiceType.BRAKES,
                description="New pads installed",
            ),
            MaintenanceEvent(
                car_id=1,
                service_date=date(2024, 2, 1),
                service_type=ServiceType.OIL_CHANGE,
            ),
        ]

        result = generate_track_prep_checklist(car, events)

        # Verify llm_chat was called with proper context
        call_args = mock_llm_chat.call_args
        assert call_args is not None
        # Check that the user_prompt contains maintenance history
        user_prompt = call_args[0][1]
        assert "maintenance_history" in user_prompt.lower() or "2024-01-15" in user_prompt
