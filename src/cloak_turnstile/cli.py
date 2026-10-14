"""JSON-only command results; dependency/browser output stays on stderr."""
from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .runner import PATCH_DIR, SolveOptions, solve


def doctor() -> dict:
    node = shutil.which("node")
    node_version = None
    node_ok = False
    if node:
        proc = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10)
        node_version = proc.stdout.strip()
        node_ok = proc.returncode == 0 and int(node_version.lstrip("v").split(".")[0]) >= 22
    installed = importlib.util.find_spec("cloakbrowser") is not None
    display = sys.platform in {"win32", "darwin"} or bool(os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"))
    patch = all((PATCH_DIR / name).is_file() for name in ("manifest.json", "script.js"))
    output = {
        "ok": bool(node_ok and installed and display and patch),
        "version": __version__,
        "python": sys.version.split()[0],
        "node": node_version,
        "node_ok": node_ok,
        "cloakbrowser": importlib.metadata.version("cloakbrowser") if installed else None,
        "display_ok": display,
        "patch_ok": patch,
        "checks": "runtime dependencies only; use fetch to download/verify the binary",
    }
    return output


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="CloakBrowser + turnstile-bypass")
    ap.add_argument("--version", action="version", version=__version__)
    commands = ap.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check dependencies without downloading or launching a browser")
    commands.add_parser("fetch", help="Download and verify the official CloakBrowser binary")
    run = commands.add_parser("solve", help="Launch CloakBrowser and run the upstream CDP solver")
    run.add_argument("--url", required=True)
    run.add_argument("--timeout", type=float, default=45.0)
    run.add_argument("--proxy", default=os.getenv("CLOAK_TURNSTILE_PROXY"))
    run.add_argument("--profile", type=Path, help="Persistent profile directory; otherwise use a temporary profile")
    run.add_argument("--timezone")
    run.add_argument("--locale")
    run.add_argument("--seed", type=int)
    run.add_argument("--geoip", action="store_true")
    run.add_argument("--fresh", action="store_true", help="Delete this host's CF cookies before solving")
    run.add_argument("--no-patch", action="store_true", help="Do not load the upstream MouseEvent extension")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            if args.command == "doctor":
                result = doctor()
            elif args.command == "fetch":
                from cloakbrowser import ensure_binary

                result = {"ok": True, "binary_path": ensure_binary()}
            else:
                result = solve(SolveOptions(
                    url=args.url, timeout=args.timeout, proxy=args.proxy, profile=args.profile,
                    timezone=args.timezone, locale=args.locale, seed=args.seed,
                    geoip=args.geoip, fresh=args.fresh, patch=not args.no_patch,
                ))
    except Exception as exc:
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1
