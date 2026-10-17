import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"

# minimal .env loader (real environment variables win)
_env = ROOT_DIR / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.split("#", 1)[0].strip()
        if "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", BACKEND_DIR / "artifacts"))
if not ARTIFACT_DIR.is_absolute():
    ARTIFACT_DIR = ROOT_DIR / ARTIFACT_DIR

_default_db = f"sqlite:///{(DATA_DIR / 'complaintiq.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", _default_db)
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////") \
        and not Path(DATABASE_URL[len("sqlite:///"):]).is_absolute():
    # relative sqlite path is resolved from the repo root
    DATABASE_URL = f"sqlite:///{(ROOT_DIR / DATABASE_URL[len('sqlite:///'):]).as_posix()}"

AUTO_BOOTSTRAP = os.getenv("AUTO_BOOTSTRAP", "true").lower() in ("1", "true", "yes")
SYNTHETIC_ROWS = int(os.getenv("SYNTHETIC_ROWS", "7000"))
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]

CATEGORIES = ["Billing", "Delivery", "Product Quality", "Technical Support", "Refunds",
              "Account Issues", "Customer Service", "Other"]
SENTIMENTS = ["negative", "neutral", "positive"]
