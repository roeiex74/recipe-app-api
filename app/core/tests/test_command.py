"""
Test custom created django management command
"""

from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2Error
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


# path of command to mock
# check method that will allow to check the status of the db
@patch("core.management.commands.wait_for_db.Command.check")
class CommandTests(SimpleTestCase):
    """Test custom command."""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database if ready."""
        patched_check.return_value = True

        call_command("wait_for_db")
        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test wait for database when getting OperationalError."""
        expected_list = [Psycopg2Error] * 2 + [OperationalError] * 3 + [True]
        patched_check.side_effect = expected_list

        call_command("wait_for_db")
        self.assertEqual(patched_check.call_count, 6)  # 6 calls
        patched_check.assert_called_with(databases=["default"])


# When mokcing an object - we want in some cases to raise an exception
# the side_effect allows to pass different values that can be handled
# differently based on their type,
# Here we pass the exception so the library will pass these exceptions
# in the same order it has received them.

# in the first stage - postgres havent started yet,
# not ready to accept connections
# After , the db is ready to accept connections but is not set up
# and ready. In total - the first 2 calls -
# we expect the Psycopg2 error
# In the last 3 times the OpertationalError indicated the db
# is not ready yet
# We expect in the sixth time to recieve a true value indication
# it is ready
