# Contributing to CrewChief

Thank you for your interest in contributing to CrewChief! This guide will help you get started.

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- pip (Python package installer)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AgentFactoryJosh/crewchief.git
   cd crewchief
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify the installation**
   ```bash
   crewchief --help
   ```

## Development Workflow

### Running Tests
```bash
pytest
pytest -v  # Verbose output
pytest tests/test_cli.py  # Run specific test file
```

### Code Formatting and Linting
```bash
# Format code
black crewchief/ tests/

# Check linting
ruff check crewchief/ tests/

# Fix linting issues automatically
ruff check --fix crewchief/ tests/
```

### Running the CLI Locally
```bash
crewchief init-garage        # Initialize database
crewchief add-car            # Add a test car
crewchief list-cars          # List cars
crewchief log-service 1      # Log maintenance
```

## Code Style

- Use Black for formatting (100 character line length)
- Use Ruff for linting
- Follow PEP 8 conventions
- Add type hints to all functions
- Write docstrings for classes and public methods

### Example Function
```python
def calculate_age(birth_year: int) -> int:
    """Calculate age from birth year.

    Args:
        birth_year: The year the vehicle was manufactured.

    Returns:
        The age of the vehicle in years.
    """
    from datetime import datetime
    return datetime.now().year - birth_year
```

## Architecture Overview

See [ARCHITECTURE.md](ARCHITECTURE.md) for details on the layered architecture. Key points:

- **Models** (`models.py`): Pydantic v2 models for data validation
- **Database** (`db.py`): Repository pattern with SQLite
- **LLM** (`llm.py`): Foundry Local integration
- **CLI** (`cli.py`): Typer commands and user interaction
- **Settings** (`settings.py`): Configuration management

## Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**
   - Keep changes focused and small
   - Add tests for new functionality
   - Update docstrings as needed

3. **Run tests and checks**
   ```bash
   pytest
   black crewchief/ tests/
   ruff check crewchief/ tests/
   ```

4. **Commit with a clear message**
   ```bash
   git commit -m "Add brief description of changes"
   ```

5. **Push and open a pull request**
   ```bash
   git push origin feature/my-feature
   ```

## Testing Guidelines

- Write unit tests for new functions and models
- Use mocks for LLM calls (see `test_llm.py`)
- Test both happy paths and error cases
- Aim for good coverage of business logic

### Example Test
```python
def test_add_car():
    repo = GarageRepository(":memory:")
    repo.init_db()

    car = Car(year=2024, make="Toyota", model="Camry", usage_type=UsageType.DAILY)
    saved_car = repo.add_car(car)

    assert saved_car.id is not None
    assert saved_car.year == 2024
```

## Submitting Changes

### Before Submitting a PR
- Ensure all tests pass: `pytest`
- Code is formatted: `black crewchief/ tests/`
- No linting errors: `ruff check crewchief/ tests/`
- Changes follow architecture patterns
- Docstrings are updated

### PR Guidelines
- Write a clear title and description
- Reference any related issues
- Keep PRs focused on a single feature or fix
- Be open to feedback and suggestions

## Reporting Issues

Found a bug? Please create a GitHub issue with:
- A clear title
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## Questions?

- Check existing documentation in the repo
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for design patterns
- Open a discussion issue for questions

Thank you for contributing!
