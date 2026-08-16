import pytest

from customers.infrastructure.config.settings import Settings


def test_from_env_reads_database_url_and_flask_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host:5432/db")
    monkeypatch.setenv("FLASK_ENV", "development")

    settings = Settings.from_env()

    assert settings.database_url == "postgresql+psycopg://u:p@host:5432/db"
    assert settings.flask_env == "development"


def test_from_env_defaults_flask_env_to_production(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host:5432/db")
    monkeypatch.delenv("FLASK_ENV", raising=False)

    settings = Settings.from_env()

    assert settings.flask_env == "production"


def test_from_env_raises_when_database_url_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError):
        Settings.from_env()
