from pathlib import Path
import pytest
from exotica.config import ensure_private_dir, validate_log_level

def test_valid_log_levels():
    assert validate_log_level("debug") == "DEBUG"
    assert validate_log_level(None) == "INFO"

def test_invalid_log_level():
    with pytest.raises(ValueError):
        validate_log_level("LOUD")

def test_private_directory_is_created(tmp_path: Path):
    path = ensure_private_dir(tmp_path / "private")
    assert path.is_dir()
    assert path.stat().st_mode & 0o777 == 0o700
