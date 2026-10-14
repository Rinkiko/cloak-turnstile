import json
import sys
from types import SimpleNamespace

from cloak_turnstile import cli


def test_cli_help_uses_product_identity():
    help_text = cli.parser().format_help()
    assert "usage: cloak-turnstile" in help_text
    assert "Cloak Turnstile" in help_text
    assert "browser-based challenge handling" in help_text
    assert cli.parser().parse_args(["doctor"]).command == "doctor"


def test_cli_json_success_and_stdout_isolation(monkeypatch, capsys):
    def solve(options):
        print("dependency diagnostic")
        assert options.url == "https://example.com"
        return {"ok": True, "token": "x" * 21}

    monkeypatch.setattr(cli, "solve", solve)
    assert cli.main(["solve", "--url", "https://example.com"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["ok"] is True
    assert "dependency diagnostic" in captured.err
    assert len(captured.out.splitlines()) == 1


def test_cli_failure_exit_code(monkeypatch, capsys):
    def fail(_):
        raise RuntimeError("browser failed")

    monkeypatch.setattr(cli, "solve", fail)
    assert cli.main(["solve", "--url", "https://example.com"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result == {"ok": False, "error": "RuntimeError: browser failed"}


def test_fetch_uses_official_downloader(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "cloakbrowser", SimpleNamespace(ensure_binary=lambda: "browser-path"))
    assert cli.main(["fetch"]) == 0
    assert json.loads(capsys.readouterr().out)["binary_path"] == "browser-path"


def test_doctor_no_browser_download(monkeypatch, capsys):
    monkeypatch.setattr(cli, "doctor", lambda: {"ok": False, "node_ok": False})
    assert cli.main(["doctor"]) == 1
    assert json.loads(capsys.readouterr().out)["node_ok"] is False
