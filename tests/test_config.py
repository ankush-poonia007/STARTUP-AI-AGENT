
import pytest
from pydantic import SecretStr, ValidationError

from src.core.config import Settings


@pytest.fixture
def valid_settings_data():
    return {
        "database_url": "postgresql+asyncpg://test:test@localhost/test_db",
        "chroma_persist_directory": "./test_chroma",
        "file_storage_path": "./test_uploads",
        "jwt_secret_key": "test-secret-that-must-not-leak",
    }


def test_settings_load_with_valid_configuration(valid_settings_data):
    settings = Settings(**valid_settings_data)

    assert settings.database_url == valid_settings_data["database_url"]
    assert settings.environment == "development"
    assert settings.rag_embedding_batch_size == 15



def test_missing_database_url_raises_validation_error(valid_settings_data, monkeypatch):
    valid_settings_data.pop("database_url")

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("database_url", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None, **valid_settings_data)

    assert "database_url" in str(exc_info.value)



def test_unknown_settings_are_ignored(valid_settings_data):
    valid_settings_data["UNKNOWN_PHASE6_SETTING"] = "ignored"

    settings = Settings(**valid_settings_data)

    assert not hasattr(settings, "UNKNOWN_PHASE6_SETTING")


def test_settings_are_frozen(valid_settings_data):
    settings = Settings(**valid_settings_data)

    with pytest.raises(ValidationError):
        settings.environment = "production"


def test_jwt_secret_is_masked(valid_settings_data):
    settings = Settings(**valid_settings_data)
    secret = valid_settings_data["jwt_secret_key"]

    assert isinstance(settings.jwt_secret_key, SecretStr)
    assert secret not in repr(settings.jwt_secret_key)
    assert secret not in repr(settings)
    assert str(settings.jwt_secret_key) == "**********"
