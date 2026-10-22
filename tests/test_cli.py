from exotica.cli import main

def test_help_screen(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "EXOTICA" in out and "COMMANDS" in out

def test_paths_command(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("EXOTICA_HOME", str(tmp_path / "exotica-data"))
    assert main(["paths"]) == 0
    assert str(tmp_path / "exotica-data") in capsys.readouterr().out


def test_run_forwards_runtime_arguments(monkeypatch):
    from exotica import heroku_runtime

    captured = {}

    def fake_run(arguments):
        captured["arguments"] = arguments
        return 0

    monkeypatch.setattr(heroku_runtime, "run_heroku", fake_run)

    assert main(["run", "--no-web", "--qr-login"]) == 0
    assert captured["arguments"] == ["--no-web", "--qr-login"]


def test_modules_lists_heroku_sources_without_executing_them(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("EXOTICA_HOME", str(tmp_path / "exotica-data"))
    directory = tmp_path / "exotica-data" / "loaded_modules"
    directory.mkdir(parents=True)
    (directory / "reviewed.py").write_text("raise RuntimeError('must not run')", encoding="utf-8")

    assert main(["modules"]) == 0
    output = capsys.readouterr().out
    assert "reviewed.py" in output
    assert "never executed" in output
