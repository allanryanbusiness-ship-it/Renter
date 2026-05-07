import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
APP_DATA_DIR = BASE_DIR / "app" / "data"
BACKUP_DIR = Path(os.getenv("RENTAL_DASHBOARD_BACKUP_DIR", str(BASE_DIR / "backups"))).expanduser().resolve()
LOG_DIR = Path(os.getenv("RENTAL_DASHBOARD_LOG_DIR", str(BASE_DIR / "logs"))).expanduser().resolve()
EXPORT_DIR = Path(os.getenv("RENTAL_DASHBOARD_EXPORT_DIR", str(BASE_DIR / "exports"))).expanduser().resolve()
APP_HOST = os.getenv("RENTAL_DASHBOARD_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("RENTAL_DASHBOARD_PORT", "8000"))
APP_VERSION = os.getenv("RENTAL_DASHBOARD_VERSION", "0.1.0")
ORANGE_COUNTY_DISCOVERY_CITIES = [
    "Irvine",
    "Costa Mesa",
    "Huntington Beach",
    "Newport Beach",
    "Orange",
    "Anaheim",
    "Tustin",
    "Fullerton",
    "Mission Viejo",
    "Lake Forest",
    "Garden Grove",
    "Santa Ana",
    "Aliso Viejo",
    "Laguna Niguel",
    "Yorba Linda",
]
APPROVED_PROVIDER_FEED_PATH = Path(
    os.getenv("RENTAL_DASHBOARD_APPROVED_FEED_PATH", str(APP_DATA_DIR / "approved_provider_feed.json"))
).expanduser().resolve()
APPROVED_PROVIDER_API_URL = os.getenv("RENTAL_DASHBOARD_PROVIDER_API_URL", "").strip()
APPROVED_PROVIDER_API_KEY = os.getenv("RENTAL_DASHBOARD_PROVIDER_API_KEY", "").strip()
APPROVED_PROVIDER_API_NAME = os.getenv("RENTAL_DASHBOARD_PROVIDER_API_NAME", "Approved JSON Provider API").strip()
APPROVED_PROVIDER_API_TIMEOUT_SECONDS = float(os.getenv("RENTAL_DASHBOARD_PROVIDER_API_TIMEOUT_SECONDS", "12"))
DISCOVERY_DEFAULT_CITIES = [
    city.strip()
    for city in os.getenv(
        "RENTAL_DASHBOARD_DISCOVERY_DEFAULT_CITIES",
        ",".join(ORANGE_COUNTY_DISCOVERY_CITIES),
    ).split(",")
    if city.strip()
]


def resolve_database_path() -> Path:
    configured = os.getenv("RENTAL_DASHBOARD_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return (DATA_DIR / "renter.db").resolve()


DATABASE_PATH = resolve_database_path()
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

DEFAULT_SCORE_WEIGHTS = {
    "price": 0.28,
    "space": 0.18,
    "location": 0.18,
    "features": 0.20,
    "freshness": 0.08,
    "confidence": 0.08,
}

DEFAULT_SEARCH_CRITERIA = {
    "name": "Orange County 3BR Yard + Garage",
    "county": "Orange County",
    "state": "CA",
    "city": "",
    "preferred_cities": ORANGE_COUNTY_DISCOVERY_CITIES,
    "zip_codes": [],
    "min_bedrooms": 3,
    "min_bathrooms": 2.0,
    "max_price": 6500,
    "min_sqft": 1400,
    "require_backyard": True,
    "require_garage": True,
    "allow_unknown_backyard": True,
    "allow_unknown_garage": True,
    "pets_required": False,
    "property_types": ["single_family", "townhome"],
    "provider_names": ["mock"],
    "notes": "Focus on Orange County rentals with at least 3 bedrooms, a backyard, and a garage.",
    "weights": DEFAULT_SCORE_WEIGHTS,
}

APP_TITLE = "Renter Dashboard"
