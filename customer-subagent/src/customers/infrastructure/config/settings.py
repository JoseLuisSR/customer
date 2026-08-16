from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    flask_env: str = "production"

    @classmethod
    def from_env(cls) -> Settings:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is required")
        return cls(
            database_url=database_url,
            flask_env=os.getenv("FLASK_ENV", "production"),
        )
