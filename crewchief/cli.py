"""CLI interface for CrewChief using Typer."""

from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated

from crewchief import __version__
from crewchief.db import GarageRepository
from crewchief.llm import (
    LLMError,
    LLMUnavailableError,
    generate_garage_summary,
    generate_maintenance_suggestions,
    generate_track_prep_checklist,
)
from crewchief.models import (
    Car,
    CarPart,
    GarageSnapshot,
    MaintenanceEvent,
    MaintenanceInterval,
    PartCategory,
    ServiceType,
    UsageType,
)
from crewchief.settings import get_settings

app = typer.Typer(
    name="crewchief",
    help="CrewChief - Local-first garage and maintenance assistant powered by Foundry Local",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"CrewChief v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """CrewChief - Your local garage and maintenance assistant."""
    pass


def get_repository() -> GarageRepository:
    """Get a repository instance with the configured database path."""
    settings = get_settings()
    db_path = settings.get_expanded_db_path()

    if not db_path.exists():
        console.print(
            "[red]Error:[/red] Database not found. Please run [bold]crewchief init-garage[/bold] first."
        )
        raise typer.Exit(code=1)

    return GarageRepository(db_path)


@app.command()
def commands() -> None:
    """List all available commands grouped by category."""
    console.print("\n[bold cyan]CrewChief Commands[/bold cyan]\n")

    # Setup
    console.print("[bold yellow]Setup[/bold yellow]")
    console.print("  init-garage        Initialize the garage database")
    console.print()

    # Car Management
    console.print("[bold yellow]Car Management[/bold yellow]")
    console.print("  add-car            Add a new car to your garage")
    console.print("  list-cars          List all cars")
    console.print("  show-car <id>      Show detailed info for a car")
    console.print("  update-car <id>    Update car information")
    console.print("  remove-car <id>    Remove a car and its history")
    console.print()

    # Maintenance Logging
    console.print("[bold yellow]Maintenance Logging[/bold yellow]")
    console.print("  log-service <id>   Log a maintenance event")
    console.print("  history <id>       View maintenance history")
    console.print("  update-service <id> Edit a maintenance record")
    console.print("  delete-service <id> Delete a maintenance record")
    console.print()

    # Parts Profile
    console.print("[bold yellow]Parts Profile[/bold yellow]")
    console.print("  add-part <id>      Add a part (oil, tires, filters, etc.)")
    console.print("  list-parts <id>    List all parts for a car")
    console.print("  update-part <id>   Edit a part")
    console.print("  delete-part <id>   Delete a part")
    console.print()

    # Cost Analysis
    console.print("[bold yellow]Cost Analysis[/bold yellow]")
    console.print("  cost-summary [id]  Cost breakdown (single car or all)")
    console.print("  cost-compare       Compare costs across all cars")
    console.print()

    # Maintenance Intervals
    console.print("[bold yellow]Maintenance Intervals[/bold yellow]")
    console.print("  set-interval <id>  Set service intervals (miles/months)")
    console.print("  check-due [id]     Check which services are due")
    console.print()

    # AI Features
    console.print("[bold yellow]AI Features (LLM-powered)[/bold yellow]")
    console.print("  summary [id]       AI-generated garage/car summary")
    console.print("  suggest-maint [id] AI maintenance suggestions")
    console.print("  track-prep <id>    Generate track day checklist")
    console.print()

    console.print("[dim]Run 'crewchief <command> --help' for detailed help on any command[/dim]")
    console.print()


@app.command()
def init_garage() -> None:
    """Initialize the garage database and configuration."""
    settings = get_settings()
    settings.ensure_config_dir()

    db_path = settings.get_expanded_db_path()

    if db_path.exists():
        console.print(f"[yellow]Database already exists at:[/yellow] {db_path}")
        if not typer.confirm("Do you want to reinitialize? This will NOT delete data."):
            raise typer.Exit()

    repo = GarageRepository(db_path)
    repo.init_db()
    repo.close()

    # Auto-detect Foundry Local and create .env file
    env_path = Path.cwd() / ".env"

    if not env_path.exists():
        console.print("\n[cyan]Checking for Azure AI Foundry Local...[/cyan]")

        try:
            import subprocess
            result = subprocess.run(
                ["foundry", "service", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Try to extract the endpoint URL from the output
                import re
                match = re.search(r'http://(?:localhost|127\.0\.0\.1):(\d+)', result.stdout)

                if match:
                    port = match.group(1)
                    # Use localhost for consistency
                    llm_url = f"http://localhost:{port}/v1"

                    # Try to get the actual model name
                    model_name = "phi-3.5-mini"  # Default fallback
                    try:
                        import requests
                        models_response = requests.get(f"{llm_url}/models", timeout=5)
                        if models_response.status_code == 200:
                            models_data = models_response.json()
                            if models_data.get("data") and len(models_data["data"]) > 0:
                                model_name = models_data["data"][0]["id"]
                    except (requests.RequestException, ValueError):
                        pass  # Use default if detection fails

                    # Create .env file
                    env_content = f"""# CrewChief Configuration
CREWCHIEF_LLM_BASE_URL={llm_url}
CREWCHIEF_LLM_MODEL={model_name}
CREWCHIEF_LLM_ENABLED=true
CREWCHIEF_LLM_TIMEOUT=30
"""
                    env_path.write_text(env_content)
                    console.print(f"[green]✓[/green] Created .env file with Foundry Local endpoint: {llm_url}")
                    console.print(f"[dim]Model: {model_name}[/dim]")
                else:
                    console.print("[yellow]⚠[/yellow] Foundry Local detected but couldn't find endpoint URL")
                    console.print("[dim]You may need to create .env manually - see PREREQUISITES.md[/dim]")
            else:
                console.print("[yellow]⚠[/yellow] Foundry Local not running")
                console.print("[dim]AI features require Foundry Local - see PREREQUISITES.md[/dim]")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            console.print("[yellow]⚠[/yellow] Foundry Local not installed")
            console.print("[dim]AI features require Foundry Local - see PREREQUISITES.md[/dim]")
        except OSError as e:
            console.print(f"[yellow]⚠[/yellow] Could not auto-detect Foundry Local: {e}")
            console.print("[dim]You can create .env manually if needed - see PREREQUISITES.md[/dim]")

    console.print("\n[green]✓[/green] Garage initialized successfully!")
    console.print(f"[dim]Database:[/dim] {db_path}")
    console.print(f"[dim]Config dir:[/dim] {db_path.parent}")


@app.command()
def add_car(
    nickname: Annotated[str | None, typer.Option(help="Nickname for the car")] = None,
    year: Annotated[int | None, typer.Option(help="Year")] = None,
    make: Annotated[str | None, typer.Option(help="Make")] = None,
    model: Annotated[str | None, typer.Option(help="Model")] = None,
    trim: Annotated[str | None, typer.Option(help="Trim level")] = None,
    vin: Annotated[str | None, typer.Option(help="VIN")] = None,
    usage: Annotated[str | None, typer.Option(help="Usage type (daily/track/project/show/other)")] = None,
    odometer: Annotated[int | None, typer.Option(help="Current odometer reading")] = None,
    notes: Annotated[str | None, typer.Option(help="Additional notes")] = None,
) -> None:
    """Add a new car to the garage."""
    repo = get_repository()

    # Interactive prompts for required fields
    if year is None:
        year = typer.prompt("Year", type=int)

    if make is None:
        make = typer.prompt("Make")

    if model is None:
        model = typer.prompt("Model")

    # Optional fields in interactive mode
    if trim is None:
        trim_input = typer.prompt("Trim (optional, press Enter to skip)", default="", show_default=False)
        trim = trim_input if trim_input else None

    if vin is None:
        vin_input = typer.prompt("VIN (optional, press Enter to skip)", default="", show_default=False)
        vin = vin_input if vin_input else None

    if usage is None:
        console.print("\nUsage types: daily, track, project, show, other")
        usage = typer.prompt("Usage type", default="daily")

    if odometer is None:
        odometer_input = typer.prompt("Current odometer (optional, press Enter to skip)", default="", show_default=False)
        odometer = int(odometer_input) if odometer_input else None

    if notes is None:
        notes_input = typer.prompt("Notes (optional, press Enter to skip)", default="", show_default=False)
        notes = notes_input if notes_input else None

    # Validate and convert usage type
    try:
        usage_type = UsageType(usage.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid usage type '{usage}'. Must be one of: daily, track, project, show, other")
        raise typer.Exit(code=1)

    # Create car object
    car = Car(
        nickname=nickname,
        year=year,
        make=make,
        model=model,
        trim=trim,
        vin=vin,
        usage_type=usage_type,
        current_odometer=odometer,
        notes=notes,
    )

    # Add to database
    car = repo.add_car(car)
    repo.close()

    console.print(f"\n[green]✓[/green] Car added successfully! [dim](ID: {car.id})[/dim]")
    console.print(f"[bold]{car.display_name()}[/bold]")


@app.command()
def list_cars() -> None:
    """List all cars in the garage."""
    repo = get_repository()
    cars = repo.get_cars()
    repo.close()

    if not cars:
        console.print("[yellow]No cars in garage.[/yellow] Add one with [bold]crewchief add-car[/bold]")
        return

    table = Table(title="Garage")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nickname", style="magenta")
    table.add_column("Vehicle", style="green")
    table.add_column("Usage", style="blue")
    table.add_column("Odometer", justify="right")

    for car in cars:
        vehicle_name = f"{car.year} {car.make} {car.model}"
        odometer = str(car.current_odometer) if car.current_odometer else "—"

        table.add_row(
            str(car.id),
            car.nickname or "—",
            vehicle_name,
            car.usage_type.value,
            odometer,
        )

    console.print(table)


@app.command()
def show_car(car_id: int) -> None:
    """Show details for a specific car."""
    repo = get_repository()
    car = repo.get_car(car_id)

    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    # Get recent maintenance
    events = repo.get_maintenance_for_car(car_id, limit=5)
    repo.close()

    # Display car details
    console.print(f"\n[bold]{car.display_name()}[/bold] [dim](ID: {car.id})[/dim]\n")

    details_table = Table(show_header=False, box=None)
    details_table.add_column("Field", style="cyan")
    details_table.add_column("Value")

    details_table.add_row("Year", str(car.year))
    details_table.add_row("Make", car.make)
    details_table.add_row("Model", car.model)
    if car.trim:
        details_table.add_row("Trim", car.trim)
    if car.vin:
        details_table.add_row("VIN", car.vin)
    details_table.add_row("Usage", car.usage_type.value)
    if car.current_odometer:
        details_table.add_row("Odometer", f"{car.current_odometer:,} miles")
    if car.notes:
        details_table.add_row("Notes", car.notes)

    console.print(details_table)

    # Display recent maintenance
    if events:
        console.print(f"\n[bold]Recent Maintenance[/bold] (last {len(events)} events)\n")
        for event in events:
            console.print(
                f"  [cyan]{event.service_date}[/cyan] - "
                f"[green]{event.service_type.value.replace('_', ' ').title()}[/green]"
            )
            if event.description:
                console.print(f"    {event.description}")
    else:
        console.print("\n[dim]No maintenance history recorded[/dim]")


@app.command()
def update_car(
    car_id: int,
    nickname: Annotated[str | None, typer.Option(help="Nickname")] = None,
    trim: Annotated[str | None, typer.Option(help="Trim level")] = None,
    vin: Annotated[str | None, typer.Option(help="VIN")] = None,
    usage: Annotated[str | None, typer.Option(help="Usage type (daily/track/project/show/other)")] = None,
    odometer: Annotated[int | None, typer.Option(help="Current odometer reading")] = None,
    notes: Annotated[str | None, typer.Option(help="Additional notes")] = None,
) -> None:
    """Update an existing car's information."""
    repo = get_repository()
    car = repo.get_car(car_id)

    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    # Update only fields that were provided
    updated = False

    if nickname is not None:
        car.nickname = nickname
        updated = True

    if trim is not None:
        car.trim = trim
        updated = True

    if vin is not None:
        car.vin = vin
        updated = True

    if usage is not None:
        try:
            car.usage_type = UsageType(usage.lower())
            updated = True
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid usage type '{usage}'. Must be one of: daily, track, project, show, other")
            repo.close()
            raise typer.Exit(code=1)

    if odometer is not None:
        car.current_odometer = odometer
        updated = True

    if notes is not None:
        car.notes = notes
        updated = True

    if not updated:
        console.print("[yellow]No fields specified to update[/yellow]")
        console.print("Use --help to see available options")
        repo.close()
        raise typer.Exit(code=0)

    # Update timestamp
    car.updated_at = datetime.now()

    # Save to database
    car = repo.update_car(car)
    repo.close()

    console.print(f"\n[green]✓[/green] Car updated successfully!")
    console.print(f"[bold]{car.display_name()}[/bold]")


@app.command()
def remove_car(
    car_id: int,
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
) -> None:
    """Remove a car and all its maintenance history."""
    repo = get_repository()
    car = repo.get_car(car_id)

    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    # Show what will be deleted
    console.print(f"\n[yellow]⚠ Warning:[/yellow] This will permanently delete:")
    console.print(f"  • [bold]{car.display_name()}[/bold] (ID: {car.id})")

    # Check if there are maintenance events
    events = repo.get_maintenance_for_car(car_id)
    if events:
        console.print(f"  • {len(events)} maintenance event(s)")

    # Confirm deletion
    if not force:
        if not typer.confirm("\nAre you sure you want to delete this car?", default=False):
            console.print("Cancelled")
            repo.close()
            raise typer.Exit(code=0)

    # Delete the car
    if repo.delete_car(car_id):
        repo.close()
        console.print(f"\n[green]✓[/green] Car deleted successfully")
    else:
        repo.close()
        console.print(f"[red]Error:[/red] Failed to delete car")
        raise typer.Exit(code=1)


@app.command()
def log_service(
    car_id: int,
    service_type: Annotated[str | None, typer.Option(help="Service type (oil_change/brakes/tires/fluids/inspection/mod/other)")] = None,
    service_date: Annotated[str | None, typer.Option(help="Service date (YYYY-MM-DD, default: today)")] = None,
    odometer: Annotated[int | None, typer.Option(help="Odometer reading")] = None,
    description: Annotated[str | None, typer.Option(help="Description of work")] = None,
    parts: Annotated[str | None, typer.Option(help="Parts used")] = None,
    cost: Annotated[float | None, typer.Option(help="Cost of service")] = None,
    location: Annotated[str | None, typer.Option(help="Location (shop name or DIY)")] = None,
) -> None:
    """Log a maintenance event for a car."""
    repo = get_repository()

    # Verify car exists
    car = repo.get_car(car_id)
    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    console.print(f"Logging service for: [bold]{car.display_name()}[/bold]\n")

    # Interactive prompts
    if service_type is None:
        console.print("Service types: oil_change, brakes, tires, fluids, inspection, mod, other")
        service_type = typer.prompt("Service type", default="oil_change")

    # Validate service type
    try:
        service_type_enum = ServiceType(service_type.lower())
    except ValueError:
        console.print(
            f"[red]Error:[/red] Invalid service type '{service_type}'. "
            f"Must be one of: oil_change, brakes, tires, fluids, inspection, mod, other"
        )
        repo.close()
        raise typer.Exit(code=1)

    # Show relevant parts from profile
    car_parts = repo.get_car_parts(car_id)
    if car_parts:
        # Map service types to relevant part categories
        relevant_categories = {
            ServiceType.OIL_CHANGE: [PartCategory.OIL, PartCategory.OIL_FILTER],
            ServiceType.TIRES: [PartCategory.TIRES],
            ServiceType.BRAKES: [PartCategory.BRAKE_PADS, PartCategory.BRAKE_FLUID],
            ServiceType.FLUIDS: [PartCategory.COOLANT, PartCategory.TRANSMISSION_FLUID, PartCategory.BRAKE_FLUID],
        }

        relevant_parts = [
            p for p in car_parts
            if service_type_enum in relevant_categories
            and p.part_category in relevant_categories[service_type_enum]
        ]

        if relevant_parts:
            console.print("\n[cyan]Parts from profile:[/cyan]")
            for part in relevant_parts:
                part_info = f"  {part.part_category.value.replace('_', ' ').title()}"
                if part.brand:
                    part_info += f": {part.brand}"
                if part.part_number:
                    part_info += f" ({part.part_number})"
                if part.size_spec:
                    part_info += f" - {part.size_spec}"
                console.print(part_info)
            console.print()

    # Parse or prompt for date
    if service_date is None:
        # Prompt for date with option to use today
        date_input = typer.prompt(
            "Service date (YYYY-MM-DD, or press Enter for today)",
            default="",
            show_default=False
        )
        if date_input.strip():
            try:
                service_date_obj = date.fromisoformat(date_input)
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-20)")
                repo.close()
                raise typer.Exit(code=1)
        else:
            service_date_obj = date.today()
            console.print(f"Using today: {service_date_obj}")
    else:
        try:
            service_date_obj = date.fromisoformat(service_date)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid date format. Use YYYY-MM-DD")
            repo.close()
            raise typer.Exit(code=1)

    # Optional prompts
    if odometer is None and typer.confirm("Record odometer reading?", default=False):
        while True:
            odometer = typer.prompt("Odometer", type=int)

            # Validate odometer against current_odometer
            if car.current_odometer is not None and odometer < car.current_odometer:
                console.print(
                    f"[yellow]Warning:[/yellow] Service odometer ({odometer:,}) is less than car's current odometer ({car.current_odometer:,})"
                )
                if not typer.confirm("Accept this odometer reading?"):
                    continue
                break
            elif car.current_odometer is not None and odometer > car.current_odometer:
                console.print(
                    f"[cyan]Note:[/cyan] Service odometer ({odometer:,}) is higher than current odometer ({car.current_odometer:,})"
                )
                if typer.confirm("Update car's current odometer to this value?"):
                    car.current_odometer = odometer
                    repo.update_car(car)
            break

    if description is None:
        description = typer.prompt("Description (optional)", default="", show_default=False)
        if not description:
            description = None

    # Create event
    event = MaintenanceEvent(
        car_id=car_id,
        service_date=service_date_obj,
        odometer=odometer,
        service_type=service_type_enum,
        description=description,
        parts=parts,
        cost=cost,
        location=location,
    )

    # Add to database
    event = repo.add_maintenance_event(event)

    # Update interval tracking if configured
    repo.update_interval_after_service(car_id, service_type_enum, service_date_obj, odometer)

    repo.close()

    console.print(f"\n[green]✓[/green] Service logged successfully! [dim](ID: {event.id})[/dim]")


@app.command()
def history(car_id: int) -> None:
    """View maintenance history for a car."""
    repo = get_repository()

    car = repo.get_car(car_id)
    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    events = repo.get_maintenance_for_car(car_id)
    repo.close()

    console.print(f"\n[bold]Maintenance History: {car.display_name()}[/bold]\n")

    if not events:
        console.print("[yellow]No maintenance history recorded[/yellow]")
        return

    table = Table()
    table.add_column("Date", style="cyan")
    table.add_column("Odometer", justify="right")
    table.add_column("Type", style="green")
    table.add_column("Description")
    table.add_column("Cost", justify="right")

    for event in events:
        odometer = f"{event.odometer:,}" if event.odometer else "—"
        cost = f"${event.cost:,.2f}" if event.cost is not None else "—"
        service_type_display = event.service_type.value.replace("_", " ").title()

        table.add_row(
            str(event.service_date),
            odometer,
            service_type_display,
            event.description or "—",
            cost,
        )

    console.print(table)


@app.command()
def update_service(event_id: int) -> None:
    """Edit a maintenance record."""
    repo = get_repository()

    # Get the event
    event = repo.get_maintenance_event(event_id)
    if event is None:
        console.print(f"[red]Error:[/red] Maintenance record with ID {event_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    # Get the car for context
    car = repo.get_car(event.car_id)

    console.print(f"\n[bold]Editing Service Record (ID: {event_id})[/bold]")
    console.print(f"Car: {car.display_name() if car else 'Unknown'}")
    console.print(f"Service Date: {event.service_date}")
    console.print(f"Service Type: {event.service_type.value.replace('_', ' ').title()}\n")

    # Show current values
    console.print("[dim]Leave blank to keep current value[/dim]\n")
    current_odometer = f"{event.odometer:,}" if event.odometer else "—"
    console.print(f"Current odometer: {current_odometer}")

    # Prompt for updates
    odometer_input = typer.prompt("New odometer (or press Enter to skip)", default="", show_default=False)
    odometer = None
    if odometer_input.strip():
        try:
            odometer = int(odometer_input)
        except ValueError:
            console.print("[red]Error:[/red] Odometer must be a number")
            repo.close()
            raise typer.Exit(code=1)

    description_input = typer.prompt("Description (or press Enter to skip)", default="", show_default=False)
    description = description_input if description_input.strip() else None

    parts_input = typer.prompt("Parts (or press Enter to skip)", default="", show_default=False)
    parts = parts_input if parts_input.strip() else None

    cost_input = typer.prompt("Cost (or press Enter to skip)", default="", show_default=False)
    cost = None
    if cost_input.strip():
        try:
            cost = float(cost_input)
        except ValueError:
            console.print("[red]Error:[/red] Cost must be a number")
            repo.close()
            raise typer.Exit(code=1)

    location_input = typer.prompt("Location (or press Enter to skip)", default="", show_default=False)
    location = location_input if location_input.strip() else None

    # Update the event
    updated_event = repo.update_maintenance_event(
        event_id,
        odometer=odometer,
        description=description,
        parts=parts,
        cost=cost,
        location=location,
    )

    repo.close()

    console.print(f"\n[green]✓[/green] Service record updated successfully!")


@app.command()
def delete_service(event_id: int) -> None:
    """Delete a maintenance record."""
    repo = get_repository()

    # Get the event to display info
    event = repo.get_maintenance_event(event_id)
    if event is None:
        console.print(f"[red]Error:[/red] Maintenance record with ID {event_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    # Get the car for context
    car = repo.get_car(event.car_id)

    console.print(f"\n[bold]Delete Service Record[/bold]")
    console.print(f"Car: {car.display_name() if car else 'Unknown'}")
    console.print(f"Date: {event.service_date}")
    console.print(f"Type: {event.service_type.value.replace('_', ' ').title()}")
    if event.description:
        console.print(f"Description: {event.description}")

    if not typer.confirm("\nAre you sure you want to delete this record?"):
        console.print("Cancelled.")
        repo.close()
        raise typer.Exit()

    # Delete the event
    deleted = repo.delete_maintenance_event(event_id)

    repo.close()

    if deleted:
        console.print(f"\n[green]✓[/green] Service record deleted successfully!")
    else:
        console.print(f"[red]Error:[/red] Could not delete record")
        raise typer.Exit(code=1)


@app.command()
def add_part(car_id: int) -> None:
    """Add a part to a car's parts profile."""
    repo = get_repository()

    # Verify car exists
    car = repo.get_car(car_id)
    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    console.print(f"Adding part for: [bold]{car.display_name()}[/bold]\n")

    # Show available categories
    console.print("Part categories:")
    for category in PartCategory:
        console.print(f"  - {category.value}")

    # Prompt for category
    category_input = typer.prompt("\nPart category")
    try:
        category = PartCategory(category_input.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid category '{category_input}'")
        repo.close()
        raise typer.Exit(code=1)

    # Prompt for details
    brand = typer.prompt("Brand (optional)", default="", show_default=False)
    brand = brand if brand.strip() else None

    part_number = typer.prompt("Part number (optional)", default="", show_default=False)
    part_number = part_number if part_number.strip() else None

    size_spec = typer.prompt("Size/Spec (optional)", default="", show_default=False)
    size_spec = size_spec if size_spec.strip() else None

    notes = typer.prompt("Notes (optional)", default="", show_default=False)
    notes = notes if notes.strip() else None

    # Create and save part
    part = CarPart(
        car_id=car_id,
        part_category=category,
        brand=brand,
        part_number=part_number,
        size_spec=size_spec,
        notes=notes,
    )

    part = repo.add_car_part(part)
    repo.close()

    console.print(f"\n[green]✓[/green] Part added successfully! [dim](ID: {part.id})[/dim]")


@app.command()
def list_parts(car_id: int) -> None:
    """List all parts for a car."""
    repo = get_repository()

    car = repo.get_car(car_id)
    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    parts = repo.get_car_parts(car_id)
    repo.close()

    console.print(f"\n[bold]Parts Profile: {car.display_name()}[/bold]\n")

    if not parts:
        console.print("[yellow]No parts recorded[/yellow]")
        return

    table = Table()
    table.add_column("ID", style="dim")
    table.add_column("Category", style="cyan")
    table.add_column("Brand")
    table.add_column("Part Number")
    table.add_column("Size/Spec")

    for part in parts:
        category_display = part.part_category.value.replace("_", " ").title()
        table.add_row(
            str(part.id),
            category_display,
            part.brand or "—",
            part.part_number or "—",
            part.size_spec or "—",
        )

    console.print(table)


@app.command()
def update_part(part_id: int) -> None:
    """Edit a part in a car's parts profile."""
    repo = get_repository()

    # Get the part
    part = repo.get_car_part(part_id)
    if part is None:
        console.print(f"[red]Error:[/red] Part with ID {part_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    # Get the car for context
    car = repo.get_car(part.car_id)

    console.print(f"\n[bold]Editing Part (ID: {part_id})[/bold]")
    console.print(f"Car: {car.display_name() if car else 'Unknown'}")
    console.print(f"Category: {part.part_category.value.replace('_', ' ').title()}\n")

    # Show current values
    console.print("[dim]Leave blank to keep current value[/dim]\n")

    # Prompt for updates
    brand_input = typer.prompt("Brand (or press Enter to skip)", default="", show_default=False)
    brand = brand_input if brand_input.strip() else None

    part_number_input = typer.prompt("Part number (or press Enter to skip)", default="", show_default=False)
    part_number = part_number_input if part_number_input.strip() else None

    size_spec_input = typer.prompt("Size/Spec (or press Enter to skip)", default="", show_default=False)
    size_spec = size_spec_input if size_spec_input.strip() else None

    notes_input = typer.prompt("Notes (or press Enter to skip)", default="", show_default=False)
    notes = notes_input if notes_input.strip() else None

    # Update the part
    updated_part = repo.update_car_part(
        part_id,
        brand=brand,
        part_number=part_number,
        size_spec=size_spec,
        notes=notes,
    )

    repo.close()

    console.print(f"\n[green]✓[/green] Part updated successfully!")


@app.command()
def delete_part(part_id: int) -> None:
    """Delete a part from a car's parts profile."""
    repo = get_repository()

    # Get the part to display info
    part = repo.get_car_part(part_id)
    if part is None:
        console.print(f"[red]Error:[/red] Part with ID {part_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    # Get the car for context
    car = repo.get_car(part.car_id)

    console.print(f"\n[bold]Delete Part[/bold]")
    console.print(f"Car: {car.display_name() if car else 'Unknown'}")
    console.print(f"Category: {part.part_category.value.replace('_', ' ').title()}")
    if part.brand:
        console.print(f"Brand: {part.brand}")
    if part.part_number:
        console.print(f"Part Number: {part.part_number}")

    if not typer.confirm("\nAre you sure you want to delete this part?"):
        console.print("Cancelled.")
        repo.close()
        raise typer.Exit()

    # Delete the part
    deleted = repo.delete_car_part(part_id)

    repo.close()

    if deleted:
        console.print(f"\n[green]✓[/green] Part deleted successfully!")
    else:
        console.print(f"[red]Error:[/red] Could not delete part")
        raise typer.Exit(code=1)


@app.command()
def cost_summary(
    car_id: Annotated[int | None, typer.Argument(help="Car ID (optional, shows all if omitted)")] = None,
) -> None:
    """Display maintenance cost breakdown for a car or all cars."""
    repo = get_repository()

    try:
        if car_id is not None:
            # Single car costs
            car = repo.get_car(car_id)
            if car is None:
                console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
                repo.close()
                raise typer.Exit(code=1)

            costs = repo.get_maintenance_costs(car_id)
            cost_per_mile = repo.get_cost_per_mile(car_id)

            console.print(f"\n[bold cyan]💰 Cost Summary: {car.display_name()}[/bold cyan]\n")

            if not costs or car_id not in costs:
                console.print("[yellow]No maintenance records with costs found[/yellow]")
                repo.close()
                return

            car_costs = costs[car_id]

            # Summary stats
            console.print(f"[bold]Total Maintenance Cost:[/bold] ${car_costs['total']:,.2f}")
            console.print(f"[bold]Services Logged:[/bold] {car_costs['count']}")
            console.print(f"[bold]Total Miles:[/bold] {cost_per_mile['total_miles']:,}")
            if cost_per_mile["cost_per_mile"] > 0:
                console.print(f"[bold]Cost per Mile:[/bold] ${cost_per_mile['cost_per_mile']:.2f}")

            # Breakdown by service type
            if car_costs["by_type"]:
                console.print("\n[bold]Breakdown by Service Type:[/bold]\n")
                table = Table()
                table.add_column("Service Type", style="cyan")
                table.add_column("Count", justify="right")
                table.add_column("Total", justify="right", style="green")
                table.add_column("Avg", justify="right")
                table.add_column("Min", justify="right")
                table.add_column("Max", justify="right")

                for service_type, stats in sorted(car_costs["by_type"].items()):
                    table.add_row(
                        service_type.replace("_", " ").title(),
                        str(stats["count"]),
                        f"${stats['total']:,.2f}",
                        f"${stats['average']:.2f}" if stats["average"] else "—",
                        f"${stats['min']:.2f}" if stats["min"] else "—",
                        f"${stats['max']:.2f}" if stats["max"] else "—",
                    )

                console.print(table)

        else:
            # All cars costs
            costs = repo.get_maintenance_costs()

            if not costs:
                console.print("[yellow]No maintenance records with costs found[/yellow]")
                repo.close()
                return

            console.print("\n[bold cyan]💰 Maintenance Costs by Car[/bold cyan]\n")

            # Get all cars for display
            cars = {car.id: car for car in repo.get_cars()}

            total_all = 0
            table = Table()
            table.add_column("Car", style="cyan")
            table.add_column("Total Cost", justify="right", style="green")
            table.add_column("Services", justify="right")
            table.add_column("Avg per Service", justify="right")

            for car_id_val, car_costs in sorted(costs.items()):
                car_name = cars[car_id_val].display_name() if car_id_val in cars else f"Car {car_id_val}"
                avg_per_service = (
                    car_costs["total"] / car_costs["count"] if car_costs["count"] > 0 else 0
                )

                table.add_row(
                    car_name,
                    f"${car_costs['total']:,.2f}",
                    str(car_costs["count"]),
                    f"${avg_per_service:.2f}",
                )
                total_all += car_costs["total"]

            console.print(table)
            console.print(f"\n[bold]Total Across All Cars:[/bold] ${total_all:,.2f}")

    finally:
        repo.close()


@app.command()
def cost_compare() -> None:
    """Compare maintenance costs across all cars."""
    repo = get_repository()

    try:
        cars = repo.get_cars()
        if not cars:
            console.print("[yellow]No cars in garage[/yellow]")
            return

        console.print("\n[bold cyan]📊 Cost Comparison[/bold cyan]\n")

        # Calculate stats for each car
        car_stats = []
        for car in cars:
            costs = repo.get_maintenance_costs(car.id)
            cost_per_mile = repo.get_cost_per_mile(car.id)

            if car.id in costs:
                total_cost = costs[car.id]["total"]
                service_count = costs[car.id]["count"]
            else:
                total_cost = 0
                service_count = 0

            car_stats.append(
                {
                    "car": car,
                    "total_cost": total_cost,
                    "service_count": service_count,
                    "cost_per_mile": cost_per_mile["cost_per_mile"],
                    "miles_driven": cost_per_mile["total_miles"],
                    "avg_per_service": total_cost / service_count if service_count > 0 else 0,
                }
            )

        # Sort by total cost (descending)
        car_stats.sort(key=lambda x: x["total_cost"], reverse=True)

        # Display comparison table
        table = Table()
        table.add_column("Car", style="cyan")
        table.add_column("Total Cost", justify="right", style="green")
        table.add_column("Services", justify="right")
        table.add_column("Avg/Service", justify="right")
        table.add_column("Cost/Mile", justify="right")
        table.add_column("Miles", justify="right")

        for stat in car_stats:
            table.add_row(
                stat["car"].display_name(),
                f"${stat['total_cost']:,.2f}",
                str(stat["service_count"]),
                f"${stat['avg_per_service']:.2f}",
                f"${stat['cost_per_mile']:.2f}" if stat["cost_per_mile"] > 0 else "—",
                f"{stat['miles_driven']:,}" if stat["miles_driven"] > 0 else "—",
            )

        console.print(table)

        # Calculate averages
        total_cost_all = sum(s["total_cost"] for s in car_stats)
        avg_cost_per_car = total_cost_all / len(car_stats) if car_stats else 0
        avg_cost_per_service = sum(
            s["total_cost"] for s in car_stats
        ) / sum(s["service_count"] for s in car_stats if s["service_count"] > 0) if sum(
            s["service_count"] for s in car_stats
        ) > 0 else 0

        console.print(f"\n[bold]Averages:[/bold]")
        console.print(f"  Cost per car: ${avg_cost_per_car:,.2f}")
        console.print(f"  Cost per service: ${avg_cost_per_service:.2f}")

    finally:
        repo.close()


@app.command()
def set_interval(car_id: int) -> None:
    """Set maintenance interval for a car service type."""
    repo = get_repository()

    # Verify car exists
    car = repo.get_car(car_id)
    if car is None:
        console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
        repo.close()
        raise typer.Exit(code=1)

    console.print(f"Setting maintenance interval for: [bold]{car.display_name()}[/bold]\n")

    # Show available service types
    console.print("Service types:")
    for service_type in ServiceType:
        console.print(f"  - {service_type.value}")

    # Prompt for service type
    service_type_input = typer.prompt("\nService type")
    try:
        service_type = ServiceType(service_type_input.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid service type '{service_type_input}'")
        repo.close()
        raise typer.Exit(code=1)

    # Prompt for intervals
    console.print(f"\n[dim]Set at least one interval (miles or months)[/dim]")

    interval_miles_input = typer.prompt("Interval in miles (or press Enter to skip)", default="", show_default=False)
    interval_miles = int(interval_miles_input) if interval_miles_input.strip() else None

    interval_months_input = typer.prompt("Interval in months (or press Enter to skip)", default="", show_default=False)
    interval_months = int(interval_months_input) if interval_months_input.strip() else None

    if not interval_miles and not interval_months:
        console.print("[red]Error:[/red] Must set at least one interval (miles or months)")
        repo.close()
        raise typer.Exit(code=1)

    # Optional: Set last service tracking
    last_service_date_input = typer.prompt(
        "Last service date (YYYY-MM-DD, or press Enter to skip)", default="", show_default=False
    )
    last_service_date = None
    if last_service_date_input.strip():
        try:
            last_service_date = date.fromisoformat(last_service_date_input)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid date format. Use YYYY-MM-DD (e.g., 2025-05-16), not '{last_service_date_input}'")
            repo.close()
            raise typer.Exit(code=1)

    last_service_odometer_input = typer.prompt(
        "Last service odometer (or press Enter to skip)", default="", show_default=False
    )
    last_service_odometer = int(last_service_odometer_input) if last_service_odometer_input.strip() else None

    notes_input = typer.prompt("Notes (optional)", default="", show_default=False)
    notes = notes_input if notes_input.strip() else None

    # Create and save interval
    interval = MaintenanceInterval(
        car_id=car_id,
        service_type=service_type,
        interval_miles=interval_miles,
        interval_months=interval_months,
        last_service_date=last_service_date,
        last_service_odometer=last_service_odometer,
        notes=notes,
    )

    interval = repo.set_maintenance_interval(interval)
    repo.close()

    console.print(f"\n[green]✓[/green] Maintenance interval set successfully!")


@app.command()
def check_due(
    car_id: Annotated[int | None, typer.Argument(help="Car ID (optional, checks all if omitted)")] = None,
) -> None:
    """Check which maintenance services are due or coming up."""
    repo = get_repository()

    try:
        if car_id is not None:
            # Single car check
            car = repo.get_car(car_id)
            if car is None:
                console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
                repo.close()
                raise typer.Exit(code=1)

            cars_to_check = [car]
        else:
            # All cars
            cars_to_check = repo.get_cars()
            if not cars_to_check:
                console.print("[yellow]No cars in garage[/yellow]")
                return

        console.print("\n[bold cyan]⏰ Maintenance Due Check[/bold cyan]\n")

        found_due = False
        for car in cars_to_check:
            due_services = repo.get_due_services(car.id)

            # Filter to only due services
            due_only = [s for s in due_services if s["is_due"]]

            if due_only:
                found_due = True
                console.print(f"[bold]{car.display_name()}[/bold]")

                for service in due_only:
                    service_name = service["service_type"].value.replace("_", " ").title()
                    console.print(f"  • {service_name}: [yellow]{service['reason']}[/yellow]")

                console.print()

        if not found_due:
            if car_id is not None:
                console.print(f"[green]✓[/green] {cars_to_check[0].display_name()} has no overdue services")
            else:
                console.print("[green]✓[/green] No overdue services across all cars")

    finally:
        repo.close()


# Phase 4: LLM-powered features
@app.command()
def summary(
    car_id: Annotated[int | None, typer.Argument(help="Car ID (optional, shows garage summary if omitted)")] = None,
) -> None:
    """Get an AI-generated summary of your garage or a specific car."""
    repo = get_repository()

    try:
        if car_id is not None:
            # Single car summary
            car = repo.get_car(car_id)
            if car is None:
                console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
                repo.close()
                raise typer.Exit(code=1)

            cars = [car]
            all_maintenance = repo.get_maintenance_for_car(car_id)
            car_parts = repo.get_car_parts(car_id)

            console.print(f"[dim]Generating summary for {car.display_name()}...[/dim]")
        else:
            # Garage-wide summary
            cars = repo.get_cars()
            if not cars:
                console.print("[yellow]No cars in garage yet. Use 'crewchief add-car' to get started.[/yellow]")
                return

            all_maintenance = repo.get_all_maintenance()
            # Get all parts for all cars
            car_parts = []
            for car in cars:
                car_parts.extend(repo.get_car_parts(car.id))

            console.print("[dim]Generating garage summary...[/dim]")

        # Build snapshot for LLM
        snapshot = GarageSnapshot(cars=cars, maintenance_events=all_maintenance)

        # Generate summary (pass parts as additional context)
        summary_text = generate_garage_summary(snapshot, parts=car_parts if car_parts else None)

        # Display result
        if car_id is not None:
            console.print(f"\n[bold cyan]🏁 Summary: {cars[0].display_name()}[/bold cyan]")
        else:
            console.print("\n[bold cyan]🏁 Garage Summary[/bold cyan]")
        console.print(f"\n{summary_text}\n")

    except LLMUnavailableError as e:
        console.print(f"[red]LLM service unavailable:[/red] {e}")
        console.print("[yellow]Make sure Foundry Local is running: foundry serve phi-3.5-mini[/yellow]")
        raise typer.Exit(code=1)
    except LLMError as e:
        console.print(f"[red]LLM error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error generating summary:[/red] {e}")
        raise typer.Exit(code=1)
    finally:
        repo.close()


@app.command()
def suggest_maint(
    car_id: Annotated[int | None, typer.Argument(help="Car ID (optional, shows suggestions for all cars if omitted)")] = None,
) -> None:
    """Get AI-powered maintenance suggestions for a car or all vehicles."""
    repo = get_repository()

    try:
        if car_id is not None:
            # Single car suggestions
            car = repo.get_car(car_id)
            if car is None:
                console.print(f"[red]Error:[/red] Car with ID {car_id} not found")
                repo.close()
                raise typer.Exit(code=1)

            cars = [car]
            all_maintenance = repo.get_maintenance_for_car(car_id)
            car_parts = repo.get_car_parts(car_id)

            console.print(f"[dim]Analyzing maintenance needs for {car.display_name()}...[/dim]")
        else:
            # Garage-wide suggestions
            cars = repo.get_cars()
            if not cars:
                console.print("[yellow]No cars in garage yet. Use 'crewchief add-car' to get started.[/yellow]")
                return

            all_maintenance = repo.get_all_maintenance()
            # Get all parts for all cars
            car_parts = []
            for car in cars:
                car_parts.extend(repo.get_car_parts(car.id))

            console.print("[dim]Analyzing maintenance needs...[/dim]")

        # Build snapshot for LLM
        snapshot = GarageSnapshot(cars=cars, maintenance_events=all_maintenance)

        # Generate suggestions (pass parts as additional context)
        suggestions = generate_maintenance_suggestions(snapshot, parts=car_parts if car_parts else None)

        # Display results
        console.print("\n[bold cyan]🔧 Maintenance Suggestions[/bold cyan]\n")

        for suggestion in suggestions:
            # Priority color coding
            priority_colors = {
                "high": "red",
                "medium": "yellow",
                "low": "green",
            }
            priority_color = priority_colors.get(suggestion.priority.value, "white")

            console.print(f"[bold]{suggestion.car_label}[/bold]")
            console.print(f"Priority: [{priority_color}]{suggestion.priority.value.upper()}[/{priority_color}]")
            console.print(f"\n{suggestion.reasoning}\n")
            console.print("[bold]Suggested Actions:[/bold]")
            for action in suggestion.suggested_actions:
                console.print(f"  • {action}")
            console.print()

    except LLMUnavailableError as e:
        console.print(f"[red]LLM service unavailable:[/red] {e}")
        console.print("[yellow]Make sure Foundry Local is running: foundry serve phi-3.5-mini[/yellow]")
    except LLMError as e:
        console.print(f"[red]LLM error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Error generating suggestions:[/red] {e}")
    finally:
        repo.close()


@app.command()
def track_prep(car_id: int) -> None:
    """Generate a track day preparation checklist for a specific car.

    Args:
        car_id: The ID of the car to prepare for track day
    """
    repo = get_repository()

    try:
        # Get the car
        car = repo.get_car(car_id)
        if not car:
            console.print(f"[red]Car with ID {car_id} not found.[/red]")
            console.print("Use 'crewchief list-cars' to see available cars.")
            raise typer.Exit(code=1)

        # Get maintenance history
        maintenance_history = repo.get_maintenance_for_car(car_id)

        # Generate checklist
        console.print(f"[dim]Generating track prep checklist for {car.display_name()}...[/dim]")
        checklist = generate_track_prep_checklist(car, maintenance_history)

        # Display results
        console.print(f"\n[bold cyan]🏁 Track Prep Checklist: {checklist.car_label}[/bold cyan]\n")

        if checklist.critical_items:
            console.print("[bold red]CRITICAL - Must Check:[/bold red]")
            for item in checklist.critical_items:
                console.print(f"  ❗ {item}")
            console.print()

        if checklist.recommended_items:
            console.print("[bold yellow]Recommended:[/bold yellow]")
            for item in checklist.recommended_items:
                console.print(f"  • {item}")
            console.print()

        if checklist.notes:
            console.print("[bold]Notes:[/bold]")
            console.print(f"{checklist.notes}\n")

    except LLMUnavailableError as e:
        console.print(f"[red]LLM service unavailable:[/red] {e}")
        console.print("[yellow]Make sure Foundry Local is running: foundry serve phi-3.5-mini[/yellow]")
        raise typer.Exit(code=1)
    except LLMError as e:
        console.print(f"[red]LLM error:[/red] {e}", soft_wrap=True)
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error generating checklist:[/red] {e}", soft_wrap=True)
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(code=1)
    finally:
        repo.close()


if __name__ == "__main__":
    app()
