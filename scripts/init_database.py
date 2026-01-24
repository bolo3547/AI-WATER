"""Initialize the TimescaleDB schema for AquaWatch NRW."""

import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.database import initialize_database


def main() -> int:
    ok = initialize_database()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
