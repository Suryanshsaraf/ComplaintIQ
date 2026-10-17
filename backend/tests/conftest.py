import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="ciq_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp, 'test.db').as_posix()}"
os.environ["ARTIFACT_DIR"] = str(Path(_tmp, "artifacts"))
os.environ["AUTO_BOOTSTRAP"] = "false"
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.db import SessionLocal, init_db
    from app.main import app, bootstrap
    init_db()
    with SessionLocal() as db:
        out = bootstrap(db, rows=4000)
    assert out["tasks"]["category"]["status"] == "ok"
    with TestClient(app) as c:
        yield c
