from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "renter.db"
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
    "name": "Orange County Family Rental Search",
    "county": "Orange County",
    "state": "CA",
    "city": "",
    "min_bedrooms": 3,
    "min_bathrooms": 2.0,
    "max_price": 6500,
    "min_sqft": 1400,
    "require_backyard": True,
    "require_garage": True,
    "pets_required": False,
    "notes": "Focus on Orange County rentals with at least 3 bedrooms, a backyard, and a garage.",
    "weights": DEFAULT_SCORE_WEIGHTS,
}

APP_TITLE = "Renter Dashboard"

