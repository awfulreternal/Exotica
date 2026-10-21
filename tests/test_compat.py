from exotica.adapters.hikka_compat import compatibility_report, loader
from exotica.modules.api import Module, command, tds

def test_compatibility_report_is_explicit_about_gaps():
    report = compatibility_report()
    assert "basic facade available" in report["loader.Module"]
    assert "not implemented" in report["database_api"]

def test_module_decorators_attach_metadata():
    @tds(name="Demo")
    class Demo(Module):
        @command(name="hello", description="hello world")
        async def hello_cmd(self, event):
            pass
    assert Demo.__exotica_metadata__["name"] == "Demo"
    assert Demo.hello_cmd.__exotica_command__.name == "hello"
    assert loader.Module is Module
