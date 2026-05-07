from collections.abc import Generator
import logging

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_PATH, DATABASE_URL, DATA_DIR


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from app import models  # noqa: F401

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Initializing SQLite database", extra={"database_path": str(DATABASE_PATH)})
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_columns()


def _migrate_sqlite_columns() -> None:
    """Add nullable/defaulted MVP columns for local SQLite databases."""
    inspector = inspect(engine)
    if "listings" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("listings")}
    listing_columns = {
        "latitude": "FLOAT",
        "longitude": "FLOAT",
        "backyard_status": "VARCHAR(20) NOT NULL DEFAULT 'unknown'",
        "backyard_evidence": "TEXT",
        "garage_status": "VARCHAR(20) NOT NULL DEFAULT 'unknown'",
        "garage_evidence": "TEXT",
        "parking_details": "TEXT",
        "pet_policy": "TEXT",
        "laundry": "VARCHAR(120)",
        "air_conditioning": "VARCHAR(120)",
        "source_url": "VARCHAR(500)",
        "source_domain": "VARCHAR(240)",
        "source_type": "VARCHAR(80) NOT NULL DEFAULT 'manual'",
        "source_listing_id": "VARCHAR(120)",
        "discovery_run_id": "INTEGER",
        "source_confidence": "FLOAT NOT NULL DEFAULT 0.75",
        "first_seen_at": "DATETIME",
        "imported_at": "DATETIME",
        "listing_status": "VARCHAR(40) NOT NULL DEFAULT 'active'",
        "decision_status": "VARCHAR(40) NOT NULL DEFAULT 'new'",
        "decision_reason": "TEXT",
        "priority": "VARCHAR(40) NOT NULL DEFAULT 'medium'",
        "next_action": "TEXT",
        "next_action_due_date": "DATETIME",
        "contact_name": "VARCHAR(160)",
        "contact_phone": "VARCHAR(80)",
        "contact_email": "VARCHAR(160)",
        "tour_date": "DATETIME",
        "user_rating": "INTEGER",
        "private_notes": "TEXT",
        "raw_text": "TEXT",
        "match_score": "FLOAT NOT NULL DEFAULT 0",
        "deal_score": "FLOAT NOT NULL DEFAULT 0",
        "confidence_score": "FLOAT NOT NULL DEFAULT 0",
    }

    score_existing = set()
    if "listing_scores" in inspector.get_table_names():
        score_existing = {column["name"] for column in inspector.get_columns("listing_scores")}
    score_columns = {
        "hard_criteria_score": "FLOAT NOT NULL DEFAULT 0",
        "deal_score": "FLOAT NOT NULL DEFAULT 0",
        "data_completeness_score": "FLOAT NOT NULL DEFAULT 0",
        "source_reliability_score": "FLOAT NOT NULL DEFAULT 0",
    }

    criteria_columns = {
        "preferred_cities": "JSON NOT NULL DEFAULT '[]'",
        "zip_codes": "JSON NOT NULL DEFAULT '[]'",
        "allow_unknown_backyard": "BOOLEAN NOT NULL DEFAULT 1",
        "allow_unknown_garage": "BOOLEAN NOT NULL DEFAULT 1",
        "property_types": "JSON NOT NULL DEFAULT '[]'",
        "provider_names": "JSON NOT NULL DEFAULT '[]'",
    }

    with engine.begin() as connection:
        for name, ddl in listing_columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE listings ADD COLUMN {name} {ddl}"))
        for name, ddl in score_columns.items():
            if "listing_scores" in inspector.get_table_names() and name not in score_existing:
                connection.execute(text(f"ALTER TABLE listing_scores ADD COLUMN {name} {ddl}"))
        if "search_criteria" in inspector.get_table_names():
            criteria_existing = {column["name"] for column in inspector.get_columns("search_criteria")}
            for name, ddl in criteria_columns.items():
                if name not in criteria_existing:
                    connection.execute(text(f"ALTER TABLE search_criteria ADD COLUMN {name} {ddl}"))
