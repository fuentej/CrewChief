"""Database repository layer for CrewChief using SQLite."""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from crewchief.models import Car, MaintenanceEvent, ServiceType, UsageType


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
