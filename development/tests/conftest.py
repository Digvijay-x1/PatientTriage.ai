# Make the backend packages (ml, services, models, routes) importable
# when pytest runs from development/.
import sys
from pathlib import Path

DEVELOPMENT_DIR = Path(__file__).resolve().parent.parent

if str(DEVELOPMENT_DIR) not in sys.path:
    sys.path.insert(0, str(DEVELOPMENT_DIR))
