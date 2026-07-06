from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEFAULT_DB = ROOT / "data" / "local_dev.sqlite"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.db.base import Base  # noqa: E402
from app import models  # noqa: F401, E402


REQUIRED_TABLES = (
    "business_objects",
    "business_object_aliases",
    "object_knowledge_cards",
    "knowledge_import_batches",
    "reply_decisions",
    "channel_accounts",
)


def current_head() -> str:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "app" / "migrations"))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"Expected one Alembic head, got {heads!r}")
    return heads[0]


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path}"


def stamp_head(engine, revision: str) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES (:revision)"), {"revision": revision})


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repair the local SQLite schema used by the desktop preview without deleting business data."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--stamp-head",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Stamp alembic_version to the current single head after create_all.",
    )
    args = parser.parse_args()

    db_path = args.db.expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(sqlite_url(db_path), connect_args={"check_same_thread": False})

    before = set(inspect(engine).get_table_names())
    missing_before = [table for table in REQUIRED_TABLES if table not in before]
    Base.metadata.create_all(bind=engine)
    if args.stamp_head:
        stamp_head(engine, current_head())

    after = set(inspect(engine).get_table_names())
    missing_after = [table for table in REQUIRED_TABLES if table not in after]
    if missing_after:
        raise SystemExit(f"local schema repair incomplete, still missing: {', '.join(missing_after)}")

    print(f"database: {db_path}")
    print(f"missing_before: {', '.join(missing_before) if missing_before else 'none'}")
    print("required_tables: ok")
    if args.stamp_head:
        print(f"alembic_version: {current_head()}")


if __name__ == "__main__":
    main()
