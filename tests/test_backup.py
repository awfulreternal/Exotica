import tarfile
import pytest
from exotica.backup import BackupError, create_backup, restore_backup

def test_backup_restore_and_session_exclusion(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "settings.json").write_text('{"theme":"mono"}', encoding="utf-8")
    (source / "secret.session").write_text("sensitive", encoding="utf-8")
    backup = create_backup(source, tmp_path / "backups")
    target = tmp_path / "target"
    restore_backup(backup, target)
    assert (target / "settings.json").exists()
    assert not (target / "secret.session").exists()

def test_restore_rejects_path_traversal(tmp_path):
    archive = tmp_path / "unsafe.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("../escape.txt")
        info.size = 3
        import io
        tar.addfile(info, io.BytesIO(b"bad"))
    with pytest.raises(BackupError):
        restore_backup(archive, tmp_path / "restore")

def test_backup_excludes_nested_sessions(tmp_path):
    source = tmp_path / "source"
    (source / "sessions").mkdir(parents=True)
    (source / "sessions" / "main.session").write_text("secret", encoding="utf-8")
    (source / "sessions" / "main.session-journal").write_text("secret", encoding="utf-8")
    (source / "sessions" / "readme.txt").write_text("safe", encoding="utf-8")
    backup = create_backup(source, tmp_path / "backups")
    with tarfile.open(backup, "r:gz") as archive:
        names = archive.getnames()
    assert "sessions/main.session" not in names
    assert "sessions/main.session-journal" not in names
    assert "sessions/readme.txt" in names
