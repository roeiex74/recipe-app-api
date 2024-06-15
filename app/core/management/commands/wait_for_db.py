"""
Django command that waits for db to be available.
"""

from typing import Any
from django.core.management.base import BaseCommand
import time
from psycopg2 import OperationalError as Psycopg2Error
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for db."""

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Entry point for command."""
        self.stdout.write("Waiting for database...")
        db_is_up = False
        while not db_is_up:
            try:
                self.check(databases=["default"])
                db_is_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write("Database unavailabale, waiting 1 second...")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS("Database availabale!"))
