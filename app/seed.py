from sqlalchemy.orm import Session

from app.services.listings import seed_demo_data


def bootstrap_demo_state(db: Session) -> None:
    seed_demo_data(db)

