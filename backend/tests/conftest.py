from __future__ import annotations

import os
from pathlib import Path
import tempfile


os.environ.setdefault("SQLITE_PATH", str(Path(tempfile.gettempdir()) / "scraping-hotels-pytest.sqlite"))
os.environ["DATABASE_PROVIDER"] = "sqlite"
os.environ.pop("DATABASE_URL", None)
