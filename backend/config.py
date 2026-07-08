import os
from dataclasses import dataclass


@dataclass
class Settings:
    db_path: str = os.getenv("SNAPLINK_DB_PATH", "snaplink.db")
    base_url: str = os.getenv("SNAPLINK_BASE_URL", "http://localhost:8000")
