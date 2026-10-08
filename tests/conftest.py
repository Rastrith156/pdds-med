"""Test configuration.

Makes the ``backend`` package importable so tests can live in the
repository-level ``tests/`` folder.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
