from exotica import hikka_runtime


def test_run_hikka_passes_private_data_root_and_credentials(monkeypatch, tmp_path):
    home = tmp_path / "private-data"
    captured = {}

    def fake_run(command, *, cwd, env, check, start_new_session):
        captured.update(command=command, cwd=cwd, env=env, check=check, start_new_session=start_new_session)
        return type("Result", (), {"returncode": 17})()

    monkeypatch.setattr(hikka_runtime, "data_dir", lambda: home)
    monkeypatch.setattr(hikka_runtime.subprocess, "run", fake_run)
    monkeypatch.setenv("EXOTICA_API_ID", "12345")
    monkeypatch.setenv("EXOTICA_API_HASH", "a" * 32)

    assert hikka_runtime.run_hikka(["--no-web"]) == 17
    assert captured["command"] == [
        hikka_runtime.sys.executable,
        "-m",
        "hikka",
        "--no-web",
        "--data-root",
        str(home),
    ]
    assert captured["cwd"] == hikka_runtime.HIKKA_ROOT
    assert captured["env"]["PYTHONPATH"].split(hikka_runtime.os.pathsep)[0] == str(hikka_runtime.HIKKA_ROOT)
    assert captured["env"]["EXOTICA_HOME"] == str(home)
    assert captured["env"]["api_id"] == "12345"
    assert captured["env"]["api_hash"] == "a" * 32
    assert captured["check"] is False
    assert captured["start_new_session"] is True
    assert home.stat().st_mode & 0o777 == 0o700


def test_run_hikka_fails_when_upstream_checkout_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(hikka_runtime, "HIKKA_ROOT", tmp_path)

    try:
        hikka_runtime.run_hikka()
    except RuntimeError as error:
        assert "Vendored Hikka runtime is missing" in str(error)
    else:
        raise AssertionError("missing runtime should fail clearly")
