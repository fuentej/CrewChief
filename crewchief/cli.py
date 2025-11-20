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
    GarageSnapshot,
    MaintenanceEvent,
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
                    llm_url = f"http://localhost:{port}/openai/v1"

                    # Create .env file
                    env_content = f"""# CrewChief Configuration
CREWCHIEF_LLM_BASE_URL={llm_url}
CREWCHIEF_LLM_MODEL=phi-3.5-mini
CREWCHIEF_LLM_ENABLED=true
CREWCHIEF_LLM_TIMEOUT=30
"""
                    env_path.write_text(env_content)
                    console.print(f"[green]✓[/green] Created .env file with Foundry Local endpoint: {llm_url}")
                else:
                    console.print("[yellow]⚠[/yellow] Foundry Local detected but couldn't find endpoint URL")
                    console.print("[dim]You may need to create .env manually - see PREREQUISITES.md[/dim]")
            else:
                console.print("[yellow]⚠[/yellow] Foundry Local not running")
                console.print("[dim]AI features require Foundry Local - see PREREQUISITES.md[/dim]")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            console.print("[yellow]⚠[/yellow] Foundry Local not installed")
            console.print("[dim]AI features require Foundry Local - see PREREQUISITES.md[/dim]")
        except Exception as e:
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

    # Parse or prompt for date
    if service_date is None:
        service_date_obj = date.today()
        console.print(f"Service date: {service_date_obj} [dim](today)[/dim]")
    else:
        try:
            service_date_obj = date.fromisoformat(service_date)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid date format. Use YYYY-MM-DD")
            repo.close()
            raise typer.Exit(code=1)

    # Optional prompts
    if odometer is None and typer.confirm("Record odometer reading?", default=False):
        odometer = typer.prompt("Odometer", type=int)

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


# Phase 4: LLM-powered features
@app.command()
def summary() -> None:
    """Get an AI-generated summary of your garage."""
    repo = get_repository()

    # Get all cars and maintenance events
    try:
        cars = repo.get_cars()
        if not cars:
            console.print("[yellow]No cars in garage yet. Use 'crewchief add-car' to get started.[/yellow]")
            return

        all_maintenance = repo.get_all_maintenance()

        # Build snapshot for LLM
        snapshot = GarageSnapshot(cars=cars, maintenance_events=all_maintenance)

        # Generate summary
        console.print("[dim]Generating garage summary...[/dim]")
        summary_text = generate_garage_summary(snapshot)

        # Display result
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


@app.command()
def suggest_maint() -> None:
    """Get AI-powered maintenance suggestions for all vehicles."""
    repo = get_repository()

    try:
        cars = repo.get_cars()
        if not cars:
            console.print("[yellow]No cars in garage yet. Use 'crewchief add-car' to get started.[/yellow]")
            return

        all_maintenance = repo.get_all_maintenance()

        # Build snapshot for LLM
        snapshot = GarageSnapshot(cars=cars, maintenance_events=all_maintenance)

        # Generate suggestions
        console.print("[dim]Analyzing maintenance needs...[/dim]")
        suggestions = generate_maintenance_suggestions(snapshot)

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


@app.command()
def track_prep(car_id: int) -> None:
    """Generate a track day preparation checklist for a specific car.

    Args:
        car_id: The ID of the car to prepare for track day
    """
    repo = get_repository()

    # Get the car
    car = repo.get_car(car_id)
    if not car:
        console.print(f"[red]Car with ID {car_id} not found.[/red]")
        console.print("Use 'crewchief list-cars' to see available cars.")
        repo.close()
        raise typer.Exit(code=1)

    try:
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
        repo.close()
        raise typer.Exit(code=1)
    except LLMError as e:
        console.print(f"[red]LLM error:[/red] {e}")
        repo.close()
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error generating checklist:[/red] {e}")
        repo.close()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
