"""One browser owner; reuse upstream CDP solver rather than reimplement it."""
from __future__ import annotations

import math
import shutil
import socket
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from ._vendor.turnstile.scripts import solve_agent_browser as upstream

PATCH_DIR = Path(__file__).parent / "_vendor" / "turnstile" / "assets" / "turnstilePatch"


@dataclass(frozen=True)
class SolveOptions:
    url: str
    timeout: float = 45.0
    proxy: str | None = None
    profile: Path | None = None
    timezone: str | None = None
    locale: str | None = None
    seed: int | None = None
    geoip: bool = False
    fresh: bool = False
    patch: bool = True

    def validate(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("url must be an absolute HTTP or HTTPS URL")
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        if self.seed is not None and not 1 <= self.seed <= 2**31 - 1:
            raise ValueError("seed must be between 1 and 2147483647")
        if self.geoip and not self.proxy:
            raise ValueError("geoip requires a proxy")


def validate_result(result: dict) -> dict:
    """An origin title alone is not proof of a solved challenge."""
    token = str(result.get("token") or "")
    clearance = result.get("clearance") or {}
    token_ok = len(token) > 20
    clearance_len = int(clearance.get("len") or 0)
    cookie_ok = clearance_len > 20
    if not token_ok and not cookie_ok:
        raise RuntimeError("no verified token or cf_clearance; page navigation is not a solve")
    kind = "both" if token_ok and cookie_ok else "turnstile_token" if token_ok else "cf_clearance"
    return {
        "ok": True,
        "lane": "cloak",
        "kind": kind,
        "token": token if token_ok else "",
        "tokenLen": len(token) if token_ok else 0,
        "clearanceLen": clearance_len,
        "clearanceDomain": clearance.get("domain"),
        "attempts": result.get("attempts"),
        "steps": result.get("steps") or [],
    }


def launch_options(options: SolveOptions, port: int) -> dict:
    args = [f"--remote-debugging-port={port}", "--remote-debugging-address=127.0.0.1"]
    if options.seed is not None:
        args.append(f"--fingerprint={options.seed}")
    return {
        "headless": False,
        "proxy": options.proxy,
        "args": args,
        "timezone": options.timezone,
        "locale": options.locale,
        "geoip": options.geoip,
        "extension_paths": [str(PATCH_DIR)] if options.patch else None,
    }


@contextmanager
def profile_directory(profile: Path | None):
    if profile is not None:
        resolved = profile.expanduser().resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        yield resolved
    else:
        with tempfile.TemporaryDirectory(prefix="cloak-turnstile-") as directory:
            yield Path(directory)


def solve(options: SolveOptions) -> dict:
    options.validate()
    if not shutil.which("node"):
        raise RuntimeError("Node.js 22+ is required by the upstream CDP transport")
    if options.patch and not (PATCH_DIR / "manifest.json").is_file():
        raise FileNotFoundError(f"packaged extension missing: {PATCH_DIR}")
    # Lazy import keeps CLI help and diagnostics usable without a browser download.
    from cloakbrowser import launch_persistent_context

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    started = time.monotonic()
    with profile_directory(options.profile) as profile:
        context = launch_persistent_context(str(profile), **launch_options(options, port))
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(options.url, wait_until="domcontentloaded", timeout=options.timeout * 1000)
            page.bring_to_front()
            # Ask the page itself for its ID; never choose an arbitrary last tab.
            session = context.new_cdp_session(page)
            try:
                target = session.send("Target.getTargetInfo")["targetInfo"]["targetId"]
            finally:
                session.detach()
            if options.fresh:
                upstream.drop_clearance(port, target, upstream.host_key(options.url))
                page.reload(wait_until="domcontentloaded", timeout=options.timeout * 1000)
            result = upstream.solve(port, target, options.timeout, url=options.url)
            output = validate_result(result)
            output.update(url=page.url, elapsed_s=round(time.monotonic() - started, 2))
            return output
        finally:
            context.close()
