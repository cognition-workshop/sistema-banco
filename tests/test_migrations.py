import pytest
from django.core.management import call_command
from django.test import TestCase


class MigrationTestCase(TestCase):
    """Test that migrations can be applied and reversed."""

    @pytest.mark.skip(
        reason="SQLite does not support migration reversibility with FK constraints"
    )
    def test_migrations_accounts_reversible(self):
        """Test that accounts migrations are reversible."""
        call_command("migrate", "accounts", verbosity=0)

        call_command("migrate", "accounts", "zero", verbosity=0)

        call_command("migrate", "accounts", verbosity=0)

    @pytest.mark.skip(
        reason="SQLite does not support migration reversibility with FK constraints"
    )
    def test_migrations_transactions_reversible(self):
        """Test that transactions migrations are reversible."""
        call_command("migrate", "transactions", verbosity=0)

        call_command("migrate", "transactions", "zero", verbosity=0)

        call_command("migrate", "transactions", verbosity=0)

    def test_no_pending_migrations(self):
        """Verify there are no unapplied migrations."""
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)
