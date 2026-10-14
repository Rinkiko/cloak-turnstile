import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from cloak_turnstile import runner
from cloak_turnstile.runner import SolveOptions, launch_options, validate_result


@pytest.mark.parametrize("url", ["TARGET", "file:///tmp/page", "https:///no-host", "ftp://example.com"])
def test_invalid_url(url):
    with pytest.raises(ValueError):
        SolveOptions(url=url).validate()


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout(timeout):
    with pytest.raises(ValueError):
        SolveOptions(url="https://example.com", timeout=timeout).validate()


def test_invalid_seed_and_geoip():
    with pytest.raises(ValueError):
        SolveOptions(url="https://example.com", seed=0).validate()
    with pytest.raises(ValueError):
        SolveOptions(url="https://example.com", geoip=True).validate()


def test_normal_page_is_not_a_solve():
    with pytest.raises(RuntimeError, match="no verified token"):
        validate_result({"kind": "cf_passed", "token": ""})


@pytest.mark.parametrize("length", [0, 20])
def test_short_token_rejected(length):
    with pytest.raises(RuntimeError):
        validate_result({"token": "x" * length})


def test_result_kinds():
    assert validate_result({"token": "x" * 21})["kind"] == "turnstile_token"
    clearance = {"len": 100, "domain": "example.com"}
    assert validate_result({"clearance": clearance})["kind"] == "cf_clearance"
    result = validate_result({"token": "x" * 21, "clearance": clearance})
    assert result["kind"] == "both"
    assert result["clearanceDomain"] == "example.com"


def test_launch_arguments():
    opts = SolveOptions(url="https://example.com", proxy="http://proxy:8080", seed=123, locale="en-US")
    kwargs = launch_options(opts, 9234)
    assert kwargs["headless"] is False
    assert kwargs["proxy"] == opts.proxy
    assert kwargs["locale"] == "en-US"
    assert "--fingerprint=123" in kwargs["args"]
    assert "--remote-debugging-address=127.0.0.1" in kwargs["args"]
    assert Path(kwargs["extension_paths"][0], "script.js").is_file()
    assert launch_options(SolveOptions(url=opts.url, patch=False), 9234)["extension_paths"] is None


def browser_double(monkeypatch, solve_result=None):
    page = Mock()
    page.url = "https://example.com/"
    session = Mock()
    session.send.return_value = {"targetInfo": {"targetId": "EXACT-TARGET"}}
    context = Mock()
    context.pages = [page]
    context.new_cdp_session.return_value = session
    launch = Mock(return_value=context)
    monkeypatch.setitem(sys.modules, "cloakbrowser", SimpleNamespace(launch_persistent_context=launch))
    monkeypatch.setattr(runner.shutil, "which", lambda _: "node")
    upstream_solve = Mock(return_value=solve_result or {"token": "x" * 21})
    monkeypatch.setattr(runner.upstream, "solve", upstream_solve)
    return launch, context, page, session, upstream_solve


def test_same_browser_exact_target_and_temporary_cleanup(monkeypatch):
    launch, context, page, session, upstream_solve = browser_double(monkeypatch)
    result = runner.solve(SolveOptions(url="https://example.com"))
    assert result["ok"]
    profile = Path(launch.call_args.args[0])
    assert not profile.exists()
    assert upstream_solve.call_args.args[1] == "EXACT-TARGET"
    assert upstream_solve.call_args.kwargs["url"] == "https://example.com"
    page.goto.assert_called_once()
    session.detach.assert_called_once()
    context.close.assert_called_once()


def test_profile_preserved_on_solver_error(monkeypatch, tmp_path):
    launch, context, page, session, upstream_solve = browser_double(monkeypatch)
    upstream_solve.side_effect = RuntimeError("solver failed")
    profile = tmp_path / "profile"
    with pytest.raises(RuntimeError, match="solver failed"):
        runner.solve(SolveOptions(url="https://example.com", profile=profile))
    assert profile.is_dir()
    context.close.assert_called_once()
    launch.assert_called_once()


def test_navigation_error_propagates(monkeypatch):
    launch, context, page, session, upstream_solve = browser_double(monkeypatch)
    page.goto.side_effect = RuntimeError("navigation failed")
    with pytest.raises(RuntimeError, match="navigation failed"):
        runner.solve(SolveOptions(url="https://example.com"))
    upstream_solve.assert_not_called()
    context.close.assert_called_once()
    assert not Path(launch.call_args.args[0]).exists()


def test_fresh_uses_same_target(monkeypatch):
    launch, context, page, session, upstream_solve = browser_double(monkeypatch)
    drop = Mock()
    monkeypatch.setattr(runner.upstream, "drop_clearance", drop)
    runner.solve(SolveOptions(url="https://example.com", fresh=True))
    assert drop.call_args.args[1:] == ("EXACT-TARGET", "example.com")
    page.reload.assert_called_once()


def test_missing_node_is_explicit(monkeypatch):
    monkeypatch.setattr(runner.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="Node.js"):
        runner.solve(SolveOptions(url="https://example.com"))
