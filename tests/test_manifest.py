import json
from pathlib import Path
import pytest
from exotica.modules.manifest import parse_manifest

def write_manifest(path: Path, **updates):
    data = {"name":"example","version":"1.0.0","description":"Example metadata",
            "entrypoint":"example.py","permissions":["messages.read"]}
    data.update(updates)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path

def test_valid_manifest(tmp_path):
    result = parse_manifest(write_manifest(tmp_path / "example.json"))
    assert result.name == "example"
    assert result.permissions == ("messages.read",)

def test_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        parse_manifest(write_manifest(tmp_path / "bad.json", entrypoint="../../evil.py"))

def test_rejects_unknown_permission(tmp_path):
    with pytest.raises(ValueError):
        parse_manifest(write_manifest(tmp_path / "bad.json", permissions=["shell.execute"]))
