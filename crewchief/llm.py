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
    except httpx.RequestError as e:
        raise LLMUnavailableError(
            f"LLM request failed: {e}"
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
    # Strip whitespace and remove markdown code blocks if present
    json_str = content.strip()

    # Handle markdown code blocks by finding actual JSON boundaries
    if "```" in json_str:
        # Find the start of actual JSON (either { or [)
        brace_idx = json_str.find("{")
        bracket_idx = json_str.find("[")

        # Use whichever comes first
        start_idx = -1
        if brace_idx >= 0 and bracket_idx >= 0:
            start_idx = min(brace_idx, bracket_idx)
        elif brace_idx >= 0:
            start_idx = brace_idx
        elif bracket_idx >= 0:
            start_idx = bracket_idx

        if start_idx >= 0:
            # Find the end of JSON by counting braces/brackets properly
            json_str_candidate = json_str[start_idx:]
            open_count = 0
            first_char = json_str_candidate[0]

            # Track depth of nesting while respecting strings
            in_string = False
            escape_next = False
            for i, char in enumerate(json_str_candidate):
                if escape_next:
                    escape_next = False
                    continue
                if char == "\\":
                    escape_next = True
                    continue
                if char == '"':
                    in_string = not in_string
                if not in_string:
                    if char in ("{", "["):
                        open_count += 1
                    elif char in ("}", "]"):
                        open_count -= 1
                        if open_count == 0:
                            json_str = json_str_candidate[:i+1]
                            break

    json_str = json_str.strip()
    if not json_str:
        raise LLMResponseError(f"No JSON content found in response")

    # Try to parse as-is first
    try:
        return response_schema.model_validate_json(json_str)
    except (ValidationError, json.JSONDecodeError) as initial_error:
        # If JSON is incomplete, try to fix it by closing open structures
        fixed_json = json_str

        # First, ensure we don't have markdown code block markers
        if "```" in fixed_json:
            # Find the start of actual JSON (either { or [)
            brace_idx = fixed_json.find("{")
            bracket_idx = fixed_json.find("[")

            # Use whichever comes first
            start_idx = -1
            if brace_idx >= 0 and bracket_idx >= 0:
                start_idx = min(brace_idx, bracket_idx)
            elif brace_idx >= 0:
                start_idx = brace_idx
            elif bracket_idx >= 0:
                start_idx = bracket_idx

            if start_idx >= 0:
                fixed_json = fixed_json[start_idx:]

        # Count open and close braces/brackets
        open_braces = fixed_json.count("{") - fixed_json.count("}")
        open_brackets = fixed_json.count("[") - fixed_json.count("]")

        # Check if there's an unterminated string (ends with unclosed quote)
        # If so, remove the last incomplete string value

        # Count quotes - if odd number, we have an unterminated string
        quote_count = fixed_json.count('"')
        if quote_count % 2 == 1:
            # Odd number of quotes means unterminated string
            last_quote_idx = fixed_json.rfind('"')
            search_back = fixed_json[:last_quote_idx]

            # Find the last meaningful character before the unterminated string
            # We want to go back to find a complete value (quote, bracket, brace)
            for i in range(len(search_back) - 1, -1, -1):
                char = search_back[i]
                if char == ',':
                    # Found a comma - skip it and take everything before
                    fixed_json = search_back[:i]
                    break
                elif char in ('"', ']', '}'):
                    # Found a complete value, keep everything up to and including it
                    fixed_json = search_back[:i+1]
                    break

        # Check if we ended with incomplete/malformed syntax
        # This can happen when truncation occurs mid-structure
        # Look for patterns like: , "key" (no value) or , "key": [] (malformed)
        if fixed_json.rstrip().endswith(('"', ']', '}')):
            # Find the last comma
            last_comma_idx = fixed_json.rfind(',')
            if last_comma_idx >= 0:
                # Check what comes after the comma
                after_comma = fixed_json[last_comma_idx+1:].strip()

                # Check if it looks like an incomplete key-value pair
                if after_comma.startswith('"'):
                    # This is a string (likely a key)
                    # Check if there's a matching closing quote
                    closing_quote_idx = after_comma.rfind('"')
                    if closing_quote_idx > 0:
                        # Extract potential key
                        potential_key = after_comma[1:closing_quote_idx]
                        after_key = after_comma[closing_quote_idx+1:].strip()

                        # If no colon after key, or colon with incomplete value, remove this dangling content
                        if not after_key or not after_key.startswith(':'):
                            # Remove the comma and everything after it
                            fixed_json = fixed_json[:last_comma_idx]
                        elif after_key.startswith(':'):
                            # There's a colon but potentially malformed value
                            # Check if what follows the colon looks incomplete
                            after_colon = after_key[1:].strip()
                            if after_colon in ('[]', '[', ']', '{}', '{', '}', ''):
                                # Likely incomplete, remove and add proper placeholder
                                fixed_json = fixed_json[:last_comma_idx] + f', "{potential_key}": []'
                            elif after_colon.endswith((']', '}')) and not (after_colon.startswith('[') or after_colon.startswith('{')):
                                # Ends with bracket/brace but doesn't start with one - malformed
                                fixed_json = fixed_json[:last_comma_idx] + f', "{potential_key}": []'

        # Now close any open structures
        # IMPORTANT: Recount after removing dangling keys
        open_braces = fixed_json.count("{") - fixed_json.count("}")
        open_brackets = fixed_json.count("[") - fixed_json.count("]")

        if open_braces > 0 or open_brackets > 0:
            # Try different closure orders
            attempts = [
                fixed_json + "]" * open_brackets + "}" * open_braces,  # Brackets first
                fixed_json + "}" * open_braces + "]" * open_brackets,  # Braces first
            ]

            for attempt in attempts:
                try:
                    return response_schema.model_validate_json(attempt)
                except (ValidationError, json.JSONDecodeError):
                    continue

        # If we couldn't fix it, raise the original error with debug info
        raise LLMResponseError(
            f"LLM response does not match expected schema: {initial_error}\n\nExtracted JSON length: {len(json_str)}\nFixed JSON length: {len(fixed_json)}\nFixed JSON (first 100 chars): {repr(fixed_json[:100])}\nFixed JSON (last 200 chars): {repr(fixed_json[-200:])}"
        ) from initial_error


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
        # Strip whitespace and remove markdown code blocks if present
        json_str = response.strip()

        if not json_str:
            raise LLMResponseError(f"Empty response from LLM. Raw response: {repr(response)}")

        # Handle markdown code blocks by finding actual JSON boundaries
        if "```" in json_str:
            # Find the start of actual JSON (either { or [)
            brace_idx = json_str.find("{")
            bracket_idx = json_str.find("[")

            # Use whichever comes first
            start_idx = -1
            if brace_idx >= 0 and bracket_idx >= 0:
                start_idx = min(brace_idx, bracket_idx)
            elif brace_idx >= 0:
                start_idx = brace_idx
            elif bracket_idx >= 0:
                start_idx = bracket_idx

            if start_idx >= 0:
                # Find the end of JSON by counting braces/brackets properly
                json_str_candidate = json_str[start_idx:]
                open_count = 0
                first_char = json_str_candidate[0]

                # Track depth of nesting while respecting strings
                in_string = False
                escape_next = False
                for i, char in enumerate(json_str_candidate):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == "\\":
                        escape_next = True
                        continue
                    if char == '"':
                        in_string = not in_string
                    if not in_string:
                        if char in ("{", "["):
                            open_count += 1
                        elif char in ("}", "]"):
                            open_count -= 1
                            if open_count == 0:
                                json_str = json_str_candidate[:i+1]
                                break

        json_str = json_str.strip()

        # Try to parse as-is first
        try:
            suggestions_data = json.loads(json_str)
        except json.JSONDecodeError as initial_error:
            # If JSON is incomplete, try to fix it by closing open structures
            fixed_json = json_str

            # Check if there's an unterminated string
            quote_count = json_str.count('"')
            if quote_count % 2 == 1:
                # Odd number of quotes means unterminated string
                last_quote_idx = json_str.rfind('"')
                search_back = json_str[:last_quote_idx]
                # Find the last meaningful character before the unterminated string
                for i in range(len(search_back) - 1, -1, -1):
                    char = search_back[i]
                    if char == ',':
                        # Found a comma - skip it and take everything before
                        fixed_json = search_back[:i]
                        break
                    elif char in ('"', ']', '}'):
                        # Found a complete value, keep everything up to and including it
                        fixed_json = search_back[:i+1]
                        break

                # Check if we ended with incomplete/malformed syntax
                # This can happen when truncation occurs mid-structure
                # Look for patterns like: , "key" (no value) or , "key": [] (malformed)
                if fixed_json.rstrip().endswith(('"', ']', '}')):
                    # Find the last comma
                    last_comma_idx = fixed_json.rfind(',')
                    if last_comma_idx >= 0:
                        # Check what comes after the comma
                        after_comma = fixed_json[last_comma_idx+1:].strip()

                        # Check if it looks like an incomplete key-value pair
                        if after_comma.startswith('"'):
                            # This is a string (likely a key)
                            # Check if there's a matching closing quote
                            closing_quote_idx = after_comma.rfind('"')
                            if closing_quote_idx > 0:
                                # Extract potential key
                                potential_key = after_comma[1:closing_quote_idx]
                                after_key = after_comma[closing_quote_idx+1:].strip()

                                # If no colon after key, or colon with incomplete value, remove this dangling content
                                if not after_key or not after_key.startswith(':'):
                                    # Remove the comma and everything after it
                                    fixed_json = fixed_json[:last_comma_idx]
                                elif after_key.startswith(':'):
                                    # There's a colon but potentially malformed value
                                    # Check if what follows the colon looks incomplete
                                    after_colon = after_key[1:].strip()
                                    if after_colon in ('[]', '[', ']', '{}', '{', '}', ''):
                                        # Likely incomplete, remove and add proper placeholder
                                        fixed_json = fixed_json[:last_comma_idx] + f', "{potential_key}": []'
                                    elif after_colon.endswith((']', '}')) and not (after_colon.startswith('[') or after_colon.startswith('{')):
                                        # Ends with bracket/brace but doesn't start with one - malformed
                                        fixed_json = fixed_json[:last_comma_idx] + f', "{potential_key}": []'

            # Now close any open structures
            open_braces = fixed_json.count("{") - fixed_json.count("}")
            open_brackets = fixed_json.count("[") - fixed_json.count("]")

            if open_braces > 0 or open_brackets > 0:
                # Close any open brackets first
                fixed_json += "]" * open_brackets
                # Close any open braces
                fixed_json += "}" * open_braces

                try:
                    suggestions_data = json.loads(fixed_json)
                except json.JSONDecodeError:
                    raise initial_error
            else:
                raise initial_error

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
