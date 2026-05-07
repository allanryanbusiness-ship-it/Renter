from sqlalchemy.orm import Session

from app.services.saved_searches import ensure_default_saved_search
from app.services.listings import seed_demo_data


def bootstrap_demo_state(db: Session) -> None:
    seed_demo_data(db)
    ensure_default_saved_search(db)
