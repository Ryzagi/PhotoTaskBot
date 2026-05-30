"""Minimal SQL migration runner.

Usage:
    python -m bot.migrate up
    python -m bot.migrate up 0002
    python -m bot.migrate status

Connects via DATABASE_URL (preferred) or, if absent, builds a Postgres URL from
SUPABASE_URL by replacing the host scheme — Supabase exposes the DB at
`db.<project>.supabase.co:5432`. For mass schema changes you should normally use
the Supabase SQL editor; this runner is for CI and dev.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg  # type: ignore[import-not-found]
from dotenv import load_dotenv

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _conn() -> psycopg.Connection:
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL must be set (or supply a direct psycopg URL).")
    return psycopg.connect(url, autocommit=False)


def _ensure_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def _applied(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def _files() -> list[Path]:
    return sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))


def cmd_status() -> None:
    with _conn() as conn:
        _ensure_table(conn)
        applied = _applied(conn)
    for f in _files():
        marker = "✓" if f.stem in applied else " "
        print(f"  [{marker}] {f.stem}")


def cmd_up(target: str | None = None) -> None:
    with _conn() as conn:
        _ensure_table(conn)
        applied = _applied(conn)
        for f in _files():
            if f.stem in applied:
                continue
            print(f"applying {f.stem}…", flush=True)
            sql = f.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)", (f.stem,)
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            print(f"  ✓ {f.stem}")
            if target and f.stem == target:
                break


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "up":
        cmd_up(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print(f"unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
