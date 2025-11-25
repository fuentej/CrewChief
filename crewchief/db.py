"""Database repository layer for CrewChief using SQLite."""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from crewchief.models import Car, CarPart, MaintenanceEvent, MaintenanceInterval, PartCategory, ServiceType, UsageType

# Register datetime adapters to suppress Python 3.13 deprecation warnings
sqlite3.register_adapter(datetime, lambda val: val.isoformat() if val else None)
sqlite3.register_adapter(date, lambda val: val.isoformat() if val else None)


class GarageRepository:
    """Repository for managing garage data in SQLite."""

    def __init__(self, db_path: str | Path):
        """Initialize repository with database path."""
        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return self.conn

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_db(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create cars table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT,
                year INTEGER NOT NULL,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                trim TEXT,
                vin TEXT,
                usage_type TEXT NOT NULL,
                current_odometer INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create maintenance_events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                service_date DATE NOT NULL,
                odometer INTEGER,
                service_type TEXT NOT NULL,
                description TEXT,
                parts TEXT,
                cost REAL,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            )
        """
        )

        # Create car_parts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS car_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                part_category TEXT NOT NULL,
                brand TEXT,
                part_number TEXT,
                size_spec TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars(id)
            )
        """
        )

        # Create maintenance_intervals table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_intervals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                interval_miles INTEGER,
                interval_months INTEGER,
                last_service_date DATE,
                last_service_odometer INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars(id),
                UNIQUE(car_id, service_type)
            )
        """
        )

        conn.commit()

    def add_car(self, car: Car) -> Car:
        """Add a new car to the garage and return it with ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO cars (
                nickname, year, make, model, trim, vin, usage_type,
                current_odometer, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                car.nickname,
                car.year,
                car.make,
                car.model,
                car.trim,
                car.vin,
                car.usage_type.value,
                car.current_odometer,
                car.notes,
                car.created_at,
                car.updated_at,
            ),
        )

        conn.commit()
        car.id = cursor.lastrowid
        return car

    def get_cars(self) -> list[Car]:
        """Get all cars from the garage."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cars ORDER BY id")
        rows = cursor.fetchall()

        cars = []
        for row in rows:
            car = self._row_to_car(row)
            cars.append(car)

        return cars

    def get_car(self, car_id: int) -> Car | None:
        """Get a specific car by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cars WHERE id = ?", (car_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_car(row)

    def update_car(self, car: Car) -> Car:
        """Update an existing car."""
        conn = self._get_connection()
        cursor = conn.cursor()

        car.updated_at = datetime.now()

        cursor.execute(
            """
            UPDATE cars
            SET nickname = ?, year = ?, make = ?, model = ?, trim = ?,
                vin = ?, usage_type = ?, current_odometer = ?, notes = ?,
                updated_at = ?
            WHERE id = ?
        """,
            (
                car.nickname,
                car.year,
                car.make,
                car.model,
                car.trim,
                car.vin,
                car.usage_type.value,
                car.current_odometer,
                car.notes,
                car.updated_at,
                car.id,
            ),
        )

        conn.commit()
        return car

    def delete_car(self, car_id: int) -> bool:
        """Delete a car and all its maintenance events.

        Returns:
            True if car was deleted, False if car not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if car exists
        cursor.execute("SELECT id FROM cars WHERE id = ?", (car_id,))
        if cursor.fetchone() is None:
            return False

        # Delete maintenance events first (foreign key constraint)
        cursor.execute("DELETE FROM maintenance_events WHERE car_id = ?", (car_id,))

        # Delete the car
        cursor.execute("DELETE FROM cars WHERE id = ?", (car_id,))

        conn.commit()
        return True

    def add_maintenance_event(self, event: MaintenanceEvent) -> MaintenanceEvent:
        """Add a maintenance event and return it with ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO maintenance_events (
                car_id, service_date, odometer, service_type, description,
                parts, cost, location, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event.car_id,
                event.service_date.isoformat(),
                event.odometer,
                event.service_type.value,
                event.description,
                event.parts,
                event.cost,
                event.location,
                event.created_at,
            ),
        )

        conn.commit()
        event.id = cursor.lastrowid
        return event

    def get_maintenance_for_car(
        self, car_id: int, limit: int | None = None
    ) -> list[MaintenanceEvent]:
        """Get maintenance events for a specific car, optionally limited."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM maintenance_events WHERE car_id = ? ORDER BY service_date DESC"
        if limit is not None:
            query += f" LIMIT {limit}"

        cursor.execute(query, (car_id,))
        rows = cursor.fetchall()

        events = []
        for row in rows:
            event = self._row_to_maintenance_event(row)
            events.append(event)

        return events

    def get_all_maintenance(self, limit: int | None = None) -> list[MaintenanceEvent]:
        """Get all maintenance events, optionally limited."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM maintenance_events ORDER BY service_date DESC"
        if limit is not None:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()

        events = []
        for row in rows:
            event = self._row_to_maintenance_event(row)
            events.append(event)

        return events

    def get_maintenance_event(self, event_id: int) -> MaintenanceEvent | None:
        """Get a specific maintenance event by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM maintenance_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_maintenance_event(row)

    def update_maintenance_event(
        self,
        event_id: int,
        service_date: date | None = None,
        service_type: ServiceType | None = None,
        odometer: int | None = None,
        description: str | None = None,
        parts: str | None = None,
        cost: float | None = None,
        location: str | None = None,
    ) -> MaintenanceEvent | None:
        """Update specific fields of a maintenance event.

        Only the provided fields are updated. Returns the updated event or None if not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if event exists
        cursor.execute("SELECT * FROM maintenance_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        if row is None:
            return None

        # Get current values
        current_event = self._row_to_maintenance_event(row)

        # Update only provided fields
        if service_date is not None:
            current_event.service_date = service_date
        if service_type is not None:
            current_event.service_type = service_type
        if odometer is not None:
            current_event.odometer = odometer
        if description is not None:
            current_event.description = description
        if parts is not None:
            current_event.parts = parts
        if cost is not None:
            current_event.cost = cost
        if location is not None:
            current_event.location = location

        # Execute update
        cursor.execute(
            """
            UPDATE maintenance_events
            SET service_date = ?, service_type = ?, odometer = ?, description = ?, parts = ?, cost = ?, location = ?
            WHERE id = ?
        """,
            (
                current_event.service_date,
                current_event.service_type.value,
                current_event.odometer,
                current_event.description,
                current_event.parts,
                current_event.cost,
                current_event.location,
                event_id,
            ),
        )

        conn.commit()
        return current_event

    def delete_maintenance_event(self, event_id: int) -> bool:
        """Delete a maintenance event by ID.

        Returns:
            True if event was deleted, False if event not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if event exists
        cursor.execute("SELECT id FROM maintenance_events WHERE id = ?", (event_id,))
        if cursor.fetchone() is None:
            return False

        # Delete the event
        cursor.execute("DELETE FROM maintenance_events WHERE id = ?", (event_id,))

        conn.commit()
        return True

    def add_car_part(self, part: CarPart) -> CarPart:
        """Add a car part to the database and return it with ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO car_parts (
                car_id, part_category, brand, part_number, size_spec, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                part.car_id,
                part.part_category.value,
                part.brand,
                part.part_number,
                part.size_spec,
                part.notes,
                part.created_at,
                part.updated_at,
            ),
        )

        conn.commit()
        part.id = cursor.lastrowid
        return part

    def get_car_parts(self, car_id: int) -> list[CarPart]:
        """Get all parts for a specific car."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM car_parts WHERE car_id = ? ORDER BY part_category",
            (car_id,),
        )
        rows = cursor.fetchall()

        parts = []
        for row in rows:
            part = self._row_to_car_part(row)
            parts.append(part)

        return parts

    def get_car_part(self, part_id: int) -> CarPart | None:
        """Get a specific car part by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM car_parts WHERE id = ?", (part_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_car_part(row)

    def update_car_part(
        self,
        part_id: int,
        brand: str | None = None,
        part_number: str | None = None,
        size_spec: str | None = None,
        notes: str | None = None,
    ) -> CarPart | None:
        """Update specific fields of a car part.

        Only the provided fields are updated. Returns the updated part or None if not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if part exists
        cursor.execute("SELECT * FROM car_parts WHERE id = ?", (part_id,))
        row = cursor.fetchone()
        if row is None:
            return None

        # Get current values
        current_part = self._row_to_car_part(row)

        # Update only provided fields
        if brand is not None:
            current_part.brand = brand
        if part_number is not None:
            current_part.part_number = part_number
        if size_spec is not None:
            current_part.size_spec = size_spec
        if notes is not None:
            current_part.notes = notes

        current_part.updated_at = datetime.now()

        # Execute update
        cursor.execute(
            """
            UPDATE car_parts
            SET brand = ?, part_number = ?, size_spec = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """,
            (
                current_part.brand,
                current_part.part_number,
                current_part.size_spec,
                current_part.notes,
                current_part.updated_at,
                part_id,
            ),
        )

        conn.commit()
        return current_part

    def delete_car_part(self, part_id: int) -> bool:
        """Delete a car part by ID.

        Returns:
            True if part was deleted, False if part not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if part exists
        cursor.execute("SELECT id FROM car_parts WHERE id = ?", (part_id,))
        if cursor.fetchone() is None:
            return False

        # Delete the part
        cursor.execute("DELETE FROM car_parts WHERE id = ?", (part_id,))

        conn.commit()
        return True

    def get_maintenance_costs(self, car_id: int | None = None) -> dict:
        """Get maintenance cost analysis.

        Args:
            car_id: If provided, analyze costs for specific car. Otherwise, analyze all cars.

        Returns:
            Dictionary with cost breakdown by car and service type.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if car_id is not None:
            # Single car costs
            cursor.execute(
                """
                SELECT
                    car_id,
                    service_type,
                    COUNT(*) as service_count,
                    SUM(cost) as total_cost,
                    AVG(cost) as avg_cost,
                    MAX(cost) as max_cost,
                    MIN(cost) as min_cost
                FROM maintenance_events
                WHERE car_id = ? AND cost IS NOT NULL
                GROUP BY car_id, service_type
                ORDER BY service_type
                """,
                (car_id,),
            )
        else:
            # All cars costs
            cursor.execute(
                """
                SELECT
                    car_id,
                    service_type,
                    COUNT(*) as service_count,
                    SUM(cost) as total_cost,
                    AVG(cost) as avg_cost,
                    MAX(cost) as max_cost,
                    MIN(cost) as min_cost
                FROM maintenance_events
                WHERE cost IS NOT NULL
                GROUP BY car_id, service_type
                ORDER BY car_id, service_type
                """
            )

        rows = cursor.fetchall()

        # Organize results by car
        costs_by_car = {}
        for row in rows:
            car_id_val = row["car_id"]
            if car_id_val not in costs_by_car:
                costs_by_car[car_id_val] = {
                    "total": 0,
                    "count": 0,
                    "by_type": {},
                }

            service_type = row["service_type"]
            total = row["total_cost"] or 0
            count = row["service_count"] or 0

            costs_by_car[car_id_val]["by_type"][service_type] = {
                "count": count,
                "total": total,
                "average": row["avg_cost"],
                "max": row["max_cost"],
                "min": row["min_cost"],
            }
            costs_by_car[car_id_val]["total"] += total
            costs_by_car[car_id_val]["count"] += count

        return costs_by_car

    def get_cost_per_mile(self, car_id: int) -> dict:
        """Calculate cost per mile for a specific car.

        Returns:
            Dictionary with total cost, total miles, and cost per mile.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get car's current odometer
        cursor.execute(
            "SELECT current_odometer FROM cars WHERE id = ?",
            (car_id,),
        )
        car_row = cursor.fetchone()
        if car_row is None or car_row["current_odometer"] is None:
            return {"total_cost": 0, "total_miles": 0, "cost_per_mile": 0}

        current_odometer = car_row["current_odometer"]

        # Get total maintenance costs
        cursor.execute(
            "SELECT SUM(cost) as total FROM maintenance_events WHERE car_id = ? AND cost IS NOT NULL",
            (car_id,),
        )
        cost_row = cursor.fetchone()
        total_cost = cost_row["total"] or 0

        # Estimate starting odometer (use first service or assume 0)
        cursor.execute(
            """
            SELECT MIN(odometer) as min_odometer FROM maintenance_events
            WHERE car_id = ? AND odometer IS NOT NULL
            """,
            (car_id,),
        )
        odometer_row = cursor.fetchone()
        min_odometer = odometer_row["min_odometer"] if odometer_row and odometer_row["min_odometer"] else 0

        total_miles = current_odometer - min_odometer

        return {
            "total_cost": total_cost,
            "total_miles": total_miles,
            "cost_per_mile": total_cost / total_miles if total_miles > 0 else 0,
        }

    def set_maintenance_interval(self, interval: MaintenanceInterval) -> MaintenanceInterval:
        """Set or update a maintenance interval for a car.

        Uses REPLACE to handle updates to existing intervals.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            REPLACE INTO maintenance_intervals (
                car_id, service_type, interval_miles, interval_months,
                last_service_date, last_service_odometer, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                interval.car_id,
                interval.service_type.value,
                interval.interval_miles,
                interval.interval_months,
                interval.last_service_date.isoformat() if interval.last_service_date else None,
                interval.last_service_odometer,
                interval.notes,
                interval.created_at,
                interval.updated_at,
            ),
        )

        conn.commit()
        interval.id = cursor.lastrowid
        return interval

    def get_maintenance_intervals(self, car_id: int) -> list[MaintenanceInterval]:
        """Get all maintenance intervals for a specific car."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM maintenance_intervals WHERE car_id = ? ORDER BY service_type",
            (car_id,),
        )
        rows = cursor.fetchall()

        intervals = []
        for row in rows:
            interval = self._row_to_maintenance_interval(row)
            intervals.append(interval)

        return intervals

    def get_due_services(self, car_id: int) -> list[dict]:
        """Calculate which services are due or overdue for a car.

        Returns:
            List of dicts with service info and due status.
        """
        from datetime import timedelta

        conn = self._get_connection()
        cursor = conn.cursor()

        # Get car info
        car = self.get_car(car_id)
        if not car:
            return []

        # Get all intervals
        intervals = self.get_maintenance_intervals(car_id)

        today = date.today()
        due_services = []

        for interval in intervals:
            due_info = {
                "service_type": interval.service_type,
                "interval_miles": interval.interval_miles,
                "interval_months": interval.interval_months,
                "last_service_date": interval.last_service_date,
                "last_service_odometer": interval.last_service_odometer,
                "is_due": False,
                "miles_until_due": None,
                "months_until_due": None,
                "reason": None,
            }

            # Check mileage-based intervals
            if interval.interval_miles and car.current_odometer and interval.last_service_odometer is not None:
                miles_since = car.current_odometer - interval.last_service_odometer
                miles_until = interval.interval_miles - miles_since

                due_info["miles_until_due"] = miles_until

                if miles_since >= interval.interval_miles:
                    due_info["is_due"] = True
                    due_info["reason"] = f"Overdue by {miles_since - interval.interval_miles:,} miles"
                elif miles_until <= 500:  # Warning threshold
                    due_info["is_due"] = True
                    due_info["reason"] = f"Due soon ({miles_until:,} miles remaining)"

            # Check time-based intervals
            if interval.interval_months and interval.last_service_date:
                months_since = (today.year - interval.last_service_date.year) * 12 + (
                    today.month - interval.last_service_date.month
                )
                months_until = interval.interval_months - months_since

                due_info["months_until_due"] = months_until

                if months_since >= interval.interval_months:
                    due_info["is_due"] = True
                    if due_info["reason"]:
                        due_info["reason"] += f" and {months_since - interval.interval_months} months"
                    else:
                        due_info["reason"] = f"Overdue by {months_since - interval.interval_months} months"
                elif months_until <= 1:  # Warning threshold
                    if not due_info["is_due"]:
                        due_info["is_due"] = True
                        due_info["reason"] = f"Due soon ({months_until} month(s) remaining)"

            due_services.append(due_info)

        return due_services

    def update_interval_after_service(
        self, car_id: int, service_type: ServiceType, service_date: date, odometer: int | None
    ) -> None:
        """Update the last service tracking for an interval after logging service."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE maintenance_intervals
            SET last_service_date = ?, last_service_odometer = ?, updated_at = ?
            WHERE car_id = ? AND service_type = ?
            """,
            (service_date.isoformat(), odometer, datetime.now(), car_id, service_type.value),
        )

        conn.commit()

    def _row_to_car(self, row: sqlite3.Row) -> Car:
        """Convert a database row to a Car model."""
        return Car(
            id=row["id"],
            nickname=row["nickname"],
            year=row["year"],
            make=row["make"],
            model=row["model"],
            trim=row["trim"],
            vin=row["vin"],
            usage_type=UsageType(row["usage_type"]),
            current_odometer=row["current_odometer"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_maintenance_event(self, row: sqlite3.Row) -> MaintenanceEvent:
        """Convert a database row to a MaintenanceEvent model."""
        return MaintenanceEvent(
            id=row["id"],
            car_id=row["car_id"],
            service_date=date.fromisoformat(row["service_date"]),
            odometer=row["odometer"],
            service_type=ServiceType(row["service_type"]),
            description=row["description"],
            parts=row["parts"],
            cost=row["cost"],
            location=row["location"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _row_to_car_part(self, row: sqlite3.Row) -> CarPart:
        """Convert a database row to a CarPart model."""
        return CarPart(
            id=row["id"],
            car_id=row["car_id"],
            part_category=PartCategory(row["part_category"]),
            brand=row["brand"],
            part_number=row["part_number"],
            size_spec=row["size_spec"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_maintenance_interval(self, row: sqlite3.Row) -> MaintenanceInterval:
        """Convert a database row to a MaintenanceInterval model."""
        return MaintenanceInterval(
            id=row["id"],
            car_id=row["car_id"],
            service_type=ServiceType(row["service_type"]),
            interval_miles=row["interval_miles"],
            interval_months=row["interval_months"],
            last_service_date=date.fromisoformat(row["last_service_date"]) if row["last_service_date"] else None,
            last_service_odometer=row["last_service_odometer"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
