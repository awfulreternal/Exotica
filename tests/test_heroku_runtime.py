from exotica import heroku_runtime


def test_run_heroku_uses_private_data_root_and_credentials(monkeypatch, tmp_path):
    home = tmp_path / "private-data"
    captured = {}

    def fake_run(command, *, cwd, env, check, start_new_session):
        captured.update(command=command, cwd=cwd, env=env, check=check, start_new_session=start_new_session)
        return type("Result", (), {"returncode": 17})()

    monkeypatch.setattr(heroku_runtime, "data_dir", lambda: home)
    monkeypatch.setattr(heroku_runtime.subprocess, "run", fake_run)
    monkeypatch.setenv("EXOTICA_API_ID", "12345")
    monkeypatch.setenv("EXOTICA_API_HASH", "a" * 32)

    assert heroku_runtime.run_heroku(["--no-web"]) == 17
    assert captured["command"] == [
        heroku_runtime.sys.executable,
        "-m",
        "heroku",
        "--no-git",
        "--no-web",
        "--data-root",
        str(home),
    ]
    assert captured["cwd"] == home.resolve()
    assert captured["env"]["PYTHONPATH"].split(heroku_runtime.os.pathsep)[0] == str(
        heroku_runtime.HEROKU_ROOT
    )
    assert captured["env"]["EXOTICA_HOME"] == str(home)
    assert captured["env"]["EXOTICA_RUNTIME_ROOT"] == str(heroku_runtime.HEROKU_ROOT)
    assert captured["env"]["api_id"] == "12345"
    assert captured["env"]["api_hash"] == "a" * 32
    assert captured["env"]["HEROKU_NO_GIT"] == "1"
    assert captured["check"] is False
    assert captured["start_new_session"] is True
    assert home.stat().st_mode & 0o777 == 0o700


def test_run_heroku_fails_when_upstream_checkout_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(heroku_runtime, "HEROKU_ROOT", tmp_path)

    try:
        heroku_runtime.run_heroku()
    except RuntimeError as error:
        assert "Vendored Heroku runtime is missing" in str(error)
    else:
        raise AssertionError("missing runtime should fail clearly")
