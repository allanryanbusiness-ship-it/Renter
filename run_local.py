from __future__ import annotations

import argparse

import uvicorn

from app.config import APP_HOST, APP_PORT, BACKUP_DIR, DATABASE_PATH, LOG_DIR
from app.logging_config import configure_logging


def print_runtime_info() -> None:
    print("Rental Dashboard starting...")
    print(f"Dashboard: http://{APP_HOST}:{APP_PORT}")
    print(f"Database: {DATABASE_PATH}")
    print(f"Backups: {BACKUP_DIR}")
    print(f"Logs: {LOG_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Renter dashboard locally.")
    parser.add_argument("--check", action="store_true", help="Print resolved runtime paths and exit.")
    parser.add_argument("--reload", action="store_true", help="Run uvicorn with reload enabled.")
    args = parser.parse_args()

    configure_logging()
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print_runtime_info()
    if args.check:
        return
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=args.reload)


if __name__ == "__main__":
    main()
