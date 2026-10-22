from exotica.ui import format_uptime, render_panel


def render(page, **overrides):
    values = {
        "account": "@exotica",
        "user_id": 42,
        "uptime": 3661,
        "connected": True,
        "version": "0.3.0",
        "modules_enabled": False,
        "modules": [],
    }
    values.update(overrides)
    return render_panel(page, **values)


def test_format_uptime_compacts_days_and_hours():
    assert format_uptime(3661) == "01:01:01"
    assert format_uptime(90061) == "1d 01:01:01"


def test_home_panel_shows_live_account_and_runtime():
    text = render("home")
    assert "CONNECTED" in text
    assert "@exotica · 42" in text
    assert "01:01:01" in text
    assert "disabled · opt-in" in text


def test_modules_panel_explains_opt_in_execution():
    text = render("modules")
    assert "Local Python modules are disabled." in text
    assert "code you have reviewed" in text


def test_commands_panel_lists_loaded_module_commands():
    text = render("commands", modules_enabled=True, module_commands=[("weather", "Show local forecast")])
    assert ".weather  Show local forecast" in text


def test_backup_panel_discloses_excluded_secrets():
    text = render("backup")
    assert "Telegram sessions and .env files are excluded." in text


def test_system_panel_only_reports_lavhost_marker(monkeypatch):
    monkeypatch.setenv("LAVHOST", "internal-host-id")
    text = render("system")
    assert "lavHost-compatible" in text
    assert "internal-host-id" not in text
