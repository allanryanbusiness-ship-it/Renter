import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_RUNTIME = Path("/tmp/renter-dashboard-tests")
TEST_RUNTIME.mkdir(parents=True, exist_ok=True)
for path in TEST_RUNTIME.glob("*"):
    if path.is_file():
        path.unlink()

os.environ["RENTAL_DASHBOARD_DB_PATH"] = str(TEST_RUNTIME / "renter-test.db")
os.environ["RENTAL_DASHBOARD_BACKUP_DIR"] = str(TEST_RUNTIME / "backups")
os.environ["RENTAL_DASHBOARD_LOG_DIR"] = str(TEST_RUNTIME / "logs")
os.environ["RENTAL_DASHBOARD_EXPORT_DIR"] = str(TEST_RUNTIME / "exports")
