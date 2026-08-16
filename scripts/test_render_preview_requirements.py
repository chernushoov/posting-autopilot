#!/usr/bin/env python3
"""Regression checks for the web-only Render preview dependency contract."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
PREVIEW_REQUIREMENTS = ROOT / "requirements-preview.txt"
BLUEPRINT = ROOT / "render.yaml"

EXPECTED_PACKAGES = {
    "flask",
    "flask-wtf",
    "gunicorn",
    "psycopg2-binary",
    "python-dotenv",
    "redis",
    "requests",
    "rq",
    "sqlalchemy",
}
EXCLUDED_RUNTIME_PACKAGES = {
    "aiogram",
    "apscheduler",
    "openai",
    "playwright",
    "stripe",
    "telethon",
}


def requirement_names(path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~;\s\[]", line, maxsplit=1)[0]
        names.add(name.lower())
    return names


class RenderPreviewRequirementsTests(unittest.TestCase):
    def test_preview_dependency_set_is_explicit_and_web_only(self) -> None:
        packages = requirement_names(PREVIEW_REQUIREMENTS)

        self.assertEqual(packages, EXPECTED_PACKAGES)
        self.assertTrue(packages.isdisjoint(EXCLUDED_RUNTIME_PACKAGES))

    def test_blueprint_uses_preview_dependencies_and_pinned_python(self) -> None:
        blueprint = BLUEPRINT.read_text(encoding="utf-8")

        self.assertIn("pip install --no-cache-dir -r requirements-preview.txt", blueprint)
        self.assertRegex(blueprint, r"(?s)- key: PYTHON_VERSION\s+value: 3\.11\.15")


if __name__ == "__main__":
    unittest.main(verbosity=2)
