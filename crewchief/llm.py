"""LLM integration layer for Foundry Local."""

import json
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from crewchief.models import (
    Car,
    GarageSnapshot,
    MaintenanceEvent,
    MaintenanceSuggestion,
    TrackPrepChecklist,
)
from crewchief.settings import get_settings


class LLMError(Exception):
    """Raised when LLM integration fails."""

    pass


class LLMUnavailableError(LLMError):
    """Raised when the LLM service is unavailable."""

    pass


class LLMResponseError(LLMError):
    """Raised when the LLM returns an invalid response."""

    pass


def _load_prompt_template(template_name: str) -> str:
    """Load a prompt template from the prompts directory.

    Args:
        template_name: Name of the template file (e.g., 'system_crewchief.txt')

    Returns:
        The template content as a string.

    Raises:
        FileNotFoundError: If the template file doesn't exist.
    """
    prompts_dir = Path(__file__).parent / "prompts"
    template_path = prompts_dir / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")


def llm_chat(
    system_prompt: str,
    user_prompt: str,
    response_schema: type[BaseModel] | None = None,
) -> str | BaseModel:
    """Make a chat completion request to Foundry Local.

    Args:
        system_prompt: The system prompt defining the assistant's behavior.
        user_prompt: The user's prompt/question.
        response_schema: Optional Pydantic model to validate and parse JSON responses.

    Returns:
        Either a string (raw response) or a Pydantic model instance (if schema provided).

    Raises:
        LLMUnavailableError: If the LLM service cannot be reached.
        LLMResponseError: If the response is invalid or cannot be parsed.
    """
    settings = get_settings()

    if not settings.llm_enabled:
        raise LLMUnavailableError("LLM integration is disabled in settings")

    # Prepare the request payload (OpenAI-compatible format)
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }

    # If we expect a JSON response, request JSON mode
    if response_schema:
        payload["response_format"] = {"type": "json_object"}

    # Make the API call
    try:
        with httpx.Client(timeout=settings.llm_timeout) as client:
            response = client.post(
                f"{settings.llm_base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
    except httpx.ConnectError as e:
        raise LLMUnavailableError(
            f"Cannot connect to LLM service at {settings.llm_base_url}. "
            "Is Foundry Local running?"
        ) from e
    except httpx.TimeoutException as e:
        raise LLMUnavailableError(
            f"LLM request timed out after {settings.llm_timeout} seconds"
        ) from e
    except httpx.HTTPStatusError as e:
        raise LLMResponseError(
            f"LLM service returned error: {e.response.status_code} - {e.response.text}"
        ) from e

    # Parse the response
    try:
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise LLMResponseError(f"Invalid response format from LLM: {e}") from e

    # If no schema validation needed, return raw content
    if not response_schema:
        return content

    # Validate against Pydantic schema
    try:
        return response_schema.model_validate_json(content)
    except ValidationError as e:
        raise LLMResponseError(
            f"LLM response does not match expected schema: {e}"
        ) from e


def generate_garage_summary(snapshot: GarageSnapshot) -> str:
    """Generate a natural language summary of the garage.

    Args:
        snapshot: Complete garage data (cars and maintenance events).

    Returns:
        A conversational summary of the garage status.

    Raises:
        LLMError: If summary generation fails.
    """
    # Load prompt templates
    system_prompt = _load_prompt_template("system_crewchief.txt")
    user_template = _load_prompt_template("garage_summary.txt")

    # Build garage data context
    garage_data = {
        "total_cars": len(snapshot.cars),
        "cars": [
            {
                "id": car.id,
                "display_name": car.display_name(),
                "usage_type": car.usage_type.value,
                "current_odometer": car.current_odometer,
                "notes": car.notes,
            }
            for car in snapshot.cars
        ],
        "maintenance_events": [
            {
                "car_id": event.car_id,
                "service_date": event.service_date.isoformat(),
                "service_type": event.service_type.value,
                "description": event.description,
                "odometer": event.odometer,
            }
            for event in snapshot.maintenance_events
        ],
    }

    # Format the user prompt with data
    user_prompt = user_template.format(
        garage_data=json.dumps(garage_data, indent=2)
    )

    # Call LLM
    response = llm_chat(system_prompt, user_prompt)

    if not isinstance(response, str):
        raise LLMResponseError("Expected string response for garage summary")

    return response


def generate_maintenance_suggestions(
    snapshot: GarageSnapshot,
) -> list[MaintenanceSuggestion]:
    """Generate AI-powered maintenance suggestions for all vehicles.

    Args:
        snapshot: Complete garage data (cars and maintenance events).

    Returns:
        List of maintenance suggestions, one per vehicle.

    Raises:
        LLMError: If suggestion generation fails.
    """
    # Load prompt templates
    system_prompt = _load_prompt_template("system_crewchief.txt")
    user_template = _load_prompt_template("maintenance_suggestions.txt")

    # Build garage data context (same as garage_summary)
    garage_data = {
        "total_cars": len(snapshot.cars),
        "cars": [
            {
                "id": car.id,
                "display_name": car.display_name(),
                "usage_type": car.usage_type.value,
                "current_odometer": car.current_odometer,
                "notes": car.notes,
            }
            for car in snapshot.cars
        ],
        "maintenance_events": [
            {
                "car_id": event.car_id,
                "service_date": event.service_date.isoformat(),
                "service_type": event.service_type.value,
                "description": event.description,
                "odometer": event.odometer,
            }
            for event in snapshot.maintenance_events
        ],
    }

    # Format the user prompt
    user_prompt = user_template.format(
        garage_data=json.dumps(garage_data, indent=2)
    )

    # The prompt expects a JSON array, but we need a wrapper for Pydantic validation
    # We'll parse the response as raw JSON first, then validate each item
    response = llm_chat(system_prompt, user_prompt)

    if not isinstance(response, str):
        raise LLMResponseError("Expected string response for maintenance suggestions")

    # Parse JSON array and validate each suggestion
    try:
        suggestions_data = json.loads(response)
        if not isinstance(suggestions_data, list):
            raise LLMResponseError("Expected JSON array of suggestions")

        suggestions = [
            MaintenanceSuggestion.model_validate(item) for item in suggestions_data
        ]
        return suggestions
    except (json.JSONDecodeError, ValidationError) as e:
        raise LLMResponseError(
            f"Failed to parse maintenance suggestions: {e}"
        ) from e


def generate_track_prep_checklist(
    car: Car, maintenance_history: list[MaintenanceEvent]
) -> TrackPrepChecklist:
    """Generate a track day preparation checklist for a specific vehicle.

    Args:
        car: The vehicle to prepare for track day.
        maintenance_history: Recent maintenance events for this vehicle.

    Returns:
        A structured track prep checklist with critical and recommended items.

    Raises:
        LLMError: If checklist generation fails.
    """
    # Load prompt templates
    system_prompt = _load_prompt_template("system_crewchief.txt")
    user_template = _load_prompt_template("track_prep.txt")

    # Build vehicle context
    vehicle_data = {
        "id": car.id,
        "display_name": car.display_name(),
        "year": car.year,
        "make": car.make,
        "model": car.model,
        "trim": car.trim,
        "usage_type": car.usage_type.value,
        "current_odometer": car.current_odometer,
        "notes": car.notes,
    }

    # Build maintenance history context
    maintenance_data = [
        {
            "service_date": event.service_date.isoformat(),
            "service_type": event.service_type.value,
            "description": event.description,
            "odometer": event.odometer,
            "parts": event.parts,
        }
        for event in maintenance_history
    ]

    # Format the user prompt
    user_prompt = user_template.format(
        vehicle_data=json.dumps(vehicle_data, indent=2),
        maintenance_history=json.dumps(maintenance_data, indent=2),
    )

    # Call LLM with schema validation
    response = llm_chat(system_prompt, user_prompt, response_schema=TrackPrepChecklist)

    if not isinstance(response, TrackPrepChecklist):
        raise LLMResponseError("Expected TrackPrepChecklist response")

    return response
