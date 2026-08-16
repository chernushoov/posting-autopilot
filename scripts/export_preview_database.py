#!/usr/bin/env python3
"""Create and verify a private PostgreSQL backup for the expiring preview DB."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


CORE_TABLES = {"companies", "vacancies", "sources", "campaigns", "candidates"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
POSTGRES_SCHEMES = {"postgres", "postgresql"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Private directory that will receive the .dump and .sha256 files.",
    )
    parser.add_argument(
        "--allow-local",
        action="store_true",
        help="Allow localhost PostgreSQL (intended only for restore verification).",
    )
    return parser.parse_args()


def validate_database_url(database_url: str, *, allow_local: bool = False) -> None:
    parsed = urlparse(database_url)
    if parsed.scheme not in POSTGRES_SCHEMES:
        raise ValueError("DATABASE_URL must be a PostgreSQL connection URL.")
    if not parsed.hostname or not parsed.path.strip("/"):
        raise ValueError("DATABASE_URL must include a host and database name.")
    if parsed.hostname.lower() in LOCAL_HOSTS and not allow_local:
        raise ValueError("Refusing a local database; use --allow-local only for restore verification.")


def redact(text: str, database_url: str) -> str:
    redacted = text.replace(database_url, "[DATABASE_URL]")
    password = urlparse(database_url).password
    if password:
        for candidate in {password, unquote(password)}:
            redacted = redacted.replace(candidate, "[PASSWORD]")
    return redacted


def find_postgres_tool(name: str) -> str:
    direct = shutil.which(name)
    if direct:
        return direct

    candidates: list[Path] = []
    for pattern in (
        f"/opt/homebrew/opt/postgresql*/bin/{name}",
        f"/opt/homebrew/Cellar/postgresql*/*/bin/{name}",
        f"/usr/local/opt/postgresql*/bin/{name}",
        f"/usr/local/Cellar/postgresql*/*/bin/{name}",
    ):
        candidates.extend(Path("/").glob(pattern.lstrip("/")))
    executable = [candidate for candidate in candidates if candidate.is_file()]
    if executable:
        return str(sorted(executable)[-1])
    raise FileNotFoundError(f"{name} is required. Install PostgreSQL client tools first.")


def postgres_child_env(database_url: str | None = None) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key in {"HOME", "LANG", "LC_ALL", "PATH", "TMPDIR"}
    }
    if database_url:
        # Keep credentials out of command arguments and process output.
        parsed = urlparse(database_url)
        env.update(
            {
                "PGHOST": parsed.hostname or "",
                "PGPORT": str(parsed.port or 5432),
                "PGDATABASE": unquote(parsed.path.lstrip("/")),
            }
        )
        if parsed.username:
            env["PGUSER"] = unquote(parsed.username)
        if parsed.password:
            env["PGPASSWORD"] = unquote(parsed.password)
        sslmode = parse_qs(parsed.query).get("sslmode", [""])[0]
        if sslmode:
            env["PGSSLMODE"] = sslmode
    return env


def run_checked(command: list[str], *, env: dict[str, str], database_url: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = redact((result.stderr or result.stdout or "unknown PostgreSQL error").strip(), database_url)
        raise RuntimeError(f"{Path(command[0]).name} failed: {detail}")
    return result


def archive_tables(listing: str) -> set[str]:
    tables: set[str] = set()
    for line in listing.splitlines():
        parts = line.split()
        if "TABLE" not in parts:
            continue
        index = parts.index("TABLE")
        if index + 2 >= len(parts) or parts[index + 1] == "DATA":
            continue
        tables.add(parts[index + 2].strip('"'))
    return tables


def validate_archive_listing(listing: str) -> set[str]:
    tables = archive_tables(listing)
    missing = sorted(CORE_TABLES - tables)
    if missing:
        raise RuntimeError(f"Backup archive is missing core tables: {', '.join(missing)}")
    return tables


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(
    *,
    database_url: str,
    output_dir: Path,
    allow_local: bool = False,
    pg_dump: str | None = None,
    pg_restore: str | None = None,
) -> dict[str, object]:
    validate_database_url(database_url, allow_local=allow_local)
    dump_tool = pg_dump or find_postgres_tool("pg_dump")
    restore_tool = pg_restore or find_postgres_tool("pg_restore")

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    filename = f"posting-autopilot-{timestamp}-{suffix}.dump"
    final_path = output_dir / filename
    checksum_path = final_path.with_suffix(final_path.suffix + ".sha256")

    temporary = tempfile.NamedTemporaryFile(
        prefix=f".{filename}.",
        suffix=".partial",
        dir=output_dir,
        delete=False,
    )
    temporary_path = Path(temporary.name)
    temporary.close()
    temporary_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    try:
        run_checked(
            [
                dump_tool,
                "--format=custom",
                "--compress=6",
                "--no-owner",
                "--no-privileges",
                f"--file={temporary_path}",
            ],
            env=postgres_child_env(database_url),
            database_url=database_url,
        )
        if temporary_path.stat().st_size == 0:
            raise RuntimeError("pg_dump produced an empty archive.")
        listing = run_checked(
            [restore_tool, "--list", str(temporary_path)],
            env=postgres_child_env(),
            database_url=database_url,
        ).stdout
        tables = validate_archive_listing(listing)
        temporary_path.replace(final_path)
        final_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

        checksum = file_sha256(final_path)
        checksum_path.write_text(f"{checksum}  {final_path.name}\n", encoding="ascii")
        checksum_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return {
            "ok": True,
            "archive": str(final_path),
            "checksum_file": str(checksum_path),
            "sha256": checksum,
            "bytes": final_path.stat().st_size,
            "verified_core_tables": sorted(CORE_TABLES),
            "archive_table_count": len(tables),
            "contains_sensitive_customer_data": True,
        }
    except Exception:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        checksum_path.unlink(missing_ok=True)
        raise


def main() -> int:
    args = parse_args()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("ERROR: DATABASE_URL is required.", file=sys.stderr)
        return 2
    try:
        report = create_backup(
            database_url=database_url,
            output_dir=args.output_dir,
            allow_local=args.allow_local,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {redact(str(error), database_url)}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
