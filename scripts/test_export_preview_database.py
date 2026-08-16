from __future__ import annotations

import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.export_preview_database import (
    CORE_TABLES,
    create_backup,
    postgres_child_env,
    redact,
    validate_archive_listing,
    validate_database_url,
)


ARCHIVE_LISTING = "\n".join(
    f"1; 1259 1 TABLE public {table} app" for table in sorted(CORE_TABLES | {"users"})
)


class PreviewDatabaseBackupTests(unittest.TestCase):
    def test_live_target_contract_rejects_sqlite_and_local_postgres(self):
        with self.assertRaisesRegex(ValueError, "PostgreSQL"):
            validate_database_url("sqlite:///preview.db")
        with self.assertRaisesRegex(ValueError, "local database"):
            validate_database_url("postgresql://user:secret@127.0.0.1:5432/app")
        validate_database_url("postgresql://user:secret@dpg-preview.internal:5432/app")
        validate_database_url(
            "postgresql://user:secret@127.0.0.1:5432/app",
            allow_local=True,
        )

    def test_archive_contract_requires_every_core_table(self):
        self.assertEqual(
            validate_archive_listing(ARCHIVE_LISTING),
            CORE_TABLES | {"users"},
        )
        with self.assertRaisesRegex(RuntimeError, "candidates"):
            validate_archive_listing(
                ARCHIVE_LISTING.replace("1; 1259 1 TABLE public candidates app\n", "")
            )

    def test_database_url_becomes_libpq_environment_not_an_argument(self):
        database_url = (
            "postgresql://preview%40user:private%2Fvalue@db.example.com:5433/preview%20db"
            "?sslmode=require"
        )
        env = postgres_child_env(database_url)
        self.assertEqual(env["PGHOST"], "db.example.com")
        self.assertEqual(env["PGPORT"], "5433")
        self.assertEqual(env["PGUSER"], "preview@user")
        self.assertEqual(env["PGPASSWORD"], "private/value")
        self.assertEqual(env["PGDATABASE"], "preview db")
        self.assertEqual(env["PGSSLMODE"], "require")
        self.assertNotIn(database_url, env.values())

    def test_backup_is_atomic_private_verified_and_checksummed(self):
        database_url = "postgresql://user:private-value@dpg-preview.internal:5432/app"

        def fake_run(command, **kwargs):
            if command[0] == "pg_dump":
                dump_path = Path(next(item.split("=", 1)[1] for item in command if item.startswith("--file=")))
                dump_path.write_bytes(b"verified custom archive")
                stdout = ""
            else:
                stdout = ARCHIVE_LISTING
            self.assertNotIn(database_url, command)
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "scripts.export_preview_database.subprocess.run",
            side_effect=fake_run,
        ):
            report = create_backup(
                database_url=database_url,
                output_dir=Path(temp_dir),
                pg_dump="pg_dump",
                pg_restore="pg_restore",
            )
            archive = Path(report["archive"])
            checksum = Path(report["checksum_file"])
            self.assertTrue(archive.is_file())
            self.assertTrue(checksum.is_file())
            self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(checksum.stat().st_mode), 0o600)
            self.assertIn(report["sha256"], checksum.read_text(encoding="ascii"))
            self.assertFalse(list(Path(temp_dir).glob("*.partial")))

    def test_failed_archive_verification_leaves_no_backup(self):
        database_url = "postgresql://user:secret@dpg-preview.internal:5432/app"

        def fake_run(command, **kwargs):
            if command[0] == "pg_dump":
                dump_path = Path(next(item.split("=", 1)[1] for item in command if item.startswith("--file=")))
                dump_path.write_bytes(b"incomplete archive")
                stdout = ""
            else:
                stdout = ARCHIVE_LISTING.replace(
                    "1; 1259 1 TABLE public candidates app\n",
                    "",
                )
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "scripts.export_preview_database.subprocess.run",
            side_effect=fake_run,
        ):
            with self.assertRaisesRegex(RuntimeError, "candidates"):
                create_backup(
                    database_url=database_url,
                    output_dir=Path(temp_dir),
                    pg_dump="pg_dump",
                    pg_restore="pg_restore",
                )
            self.assertEqual(list(Path(temp_dir).iterdir()), [])

    def test_error_redaction_removes_url_and_password(self):
        database_url = "postgresql://user:private%2Fvalue@example.com:5432/app"
        message = redact(
            f"failed for {database_url}; encoded=private%2Fvalue; decoded=private/value",
            database_url,
        )
        self.assertNotIn("private-value", message)
        self.assertNotIn("private%2Fvalue", message)
        self.assertNotIn("private/value", message)
        self.assertNotIn(database_url, message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
