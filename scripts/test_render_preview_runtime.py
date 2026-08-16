#!/usr/bin/env python3
"""Side-effect-free contract tests for the Render preview bootstrap."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Prevent module import from touching an operator-configured database.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/15"
os.environ["FLASK_SECRET_KEY"] = "render-preview-test-only-secret-value"
os.environ["ADMIN_PASSWORD"] = "render-preview-test-only"

from scripts import start_render_preview as runtime  # noqa: E402


class RenderPreviewRuntimeTests(unittest.TestCase):
    def preview_env(self) -> dict[str, str]:
        return {
            "FLASK_SECRET_KEY": "s" * 40,
            "ADMIN_PASSWORD": "p" * 20,
            "BILLING_ENABLED": "0",
            "PREVIEW_SEED": "0",
            "PORT": "10000",
            "WEB_CONCURRENCY": "1",
        }

    def test_environment_contract_accepts_generated_secrets_and_linked_datastores(self) -> None:
        with (
            patch.dict(os.environ, self.preview_env(), clear=False),
            patch.object(runtime.Config, "DATABASE_URL", "postgresql://user:pass@db.internal/app"),
            patch.object(runtime.Config, "REDIS_URL", "rediss://cache.internal:6379"),
        ):
            runtime.validate_preview_environment()

    def test_environment_contract_fails_closed(self) -> None:
        unsafe = self.preview_env() | {
            "FLASK_SECRET_KEY": "dev-secret",
            "ADMIN_PASSWORD": "admin123",
            "BILLING_ENABLED": "1",
        }
        with (
            patch.dict(os.environ, unsafe, clear=False),
            patch.object(runtime.Config, "DATABASE_URL", "postgresql://postgres@127.0.0.1/preview"),
            patch.object(runtime.Config, "REDIS_URL", "redis://localhost:6379"),
            self.assertRaisesRegex(
                RuntimeError,
                r"(?s)DATABASE_URL must be a Render Postgres URL.*"
                r"REDIS_URL must be a Render Key Value URL.*"
                r"FLASK_SECRET_KEY must be a generated.*"
                r"ADMIN_PASSWORD must be a generated.*"
                r"BILLING_ENABLED must remain off",
            ),
        ):
            runtime.validate_preview_environment()

    def test_datastore_wait_retries_then_succeeds(self) -> None:
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.__exit__.return_value = False
        fake_engine = MagicMock()
        fake_engine.connect.side_effect = [RuntimeError("starting"), connection]
        redis_client = MagicMock()

        with (
            patch.object(runtime, "engine", fake_engine),
            patch.object(runtime.Redis, "from_url", return_value=redis_client),
            patch.object(runtime.time, "sleep") as sleep,
            patch.object(runtime.time, "monotonic", side_effect=[0, 0, 1]),
        ):
            runtime.wait_for_datastores(timeout_seconds=10)

        sleep.assert_called_once_with(2)
        connection.execute.assert_called_once()
        redis_client.ping.assert_called_once()

    def test_gunicorn_command_is_web_only_and_uses_render_port(self) -> None:
        with patch.dict(os.environ, {"PORT": "12345", "WEB_CONCURRENCY": "2"}, clear=False):
            command = runtime.gunicorn_command()

        self.assertIn("0.0.0.0:12345", command)
        self.assertIn("app.factory:create_app()", command)
        self.assertNotIn("worker.run_worker", command)
        self.assertNotIn("bot.run_bot", command)


if __name__ == "__main__":
    unittest.main(verbosity=2)
