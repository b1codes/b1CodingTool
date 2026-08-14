from typer.testing import CliRunner
from b1.cli import app
import b1.commands.update_project as update_project_mod

runner = CliRunner()


class _FakeCompletedProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode


def test_update_project_invokes_bundled_script(monkeypatch):
    captured = {}

    def fake_run(args, cwd=None):
        captured["args"] = args
        captured["cwd"] = cwd
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(update_project_mod.subprocess, "run", fake_run)

    result = runner.invoke(app, ["update-project", "--claude", "--skip-skills"])

    assert result.exit_code == 0
    assert captured["args"][0].endswith("scripts/update-project.sh")
    assert "--claude" in captured["args"]
    assert "--skip-skills" in captured["args"]
    assert "--agy" not in captured["args"]


def test_update_project_propagates_nonzero_exit(monkeypatch):
    monkeypatch.setattr(
        update_project_mod.subprocess, "run", lambda args, cwd=None: _FakeCompletedProcess(3)
    )

    result = runner.invoke(app, ["update-project", "--all"])

    assert result.exit_code == 3
