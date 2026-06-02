"""Create the application database on RDS if it does not exist."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.admin_database_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": settings.database},
        ).scalar()

        if exists:
            print(f"Database '{settings.database}' already exists.")
            return

        connection.execute(text(f'CREATE DATABASE "{settings.database}"'))
        print(f"Created database '{settings.database}'.")


if __name__ == "__main__":
    main()
