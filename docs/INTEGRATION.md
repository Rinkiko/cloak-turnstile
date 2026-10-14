# Integration design

```text
cloak-turnstile CLI
  -> SolveOptions validation
  -> cloakbrowser.launch_persistent_context(headless=False)
  -> Playwright page navigation and exact Target.getTargetInfo
  -> upstream solve_agent_browser.solve(local CDP port, target ID)
  -> verified token / clearance result
  -> context.close() and temporary profile cleanup
```

## Why this integration

The official persistent launch API supplies the binary, fingerprint flags, proxy handling, license environment and profile seed. Starting a separate DrissionPage Chrome would lose that launch configuration and create a second browser owner. This project therefore reuses the CDP solver, not the original multi-lane dispatcher. Node.js is still required by that solver's CDP transport.

The legacy agent-browser helpers remain in the vendored upstream module to preserve provenance, but the integration never invokes agent-browser, DrissionPage, Camoufox or an external paid solving service. No such lane is a fallback.

## Semantics

- A per-run CDP port is bound only to 127.0.0.1. There is a small allocation/launch race after releasing the ephemeral socket; a launch error propagates instead of attaching to another browser.
- Use the actual Playwright page's CDP target ID, not an arbitrary tab from `/json/list`.
- The official launcher starts one persistent context. A temporary profile is removed after close; a user-selected profile is retained even on failure.
- The adapter checks token/clearance length independently of upstream `kind`. An upstream `cf_passed` without either proof is rejected.
- Clearance values are not copied into output. An explicitly selected profile retains the browser session.
- Raw CDP interactions are controlled by the upstream solver. The CloakBrowser `humanize` option is not advertised because it does not alter that raw CDP path.
- The upstream extension is loaded by default, and may be explicitly disabled. Current binaries may already fix CDP mouse coordinates; compatibility depends on the binary/site.
- HTTP/HTTPS URLs only. No automatic timeout retries, proxy rotation or replacement browser.

## Updating upstream

1. Review the exact new commit and license.
2. Replace only the listed upstream files. Reapply the package-relative import patch.
3. Update `upstream-lock.json`, version pin and `THIRD_PARTY_NOTICES.md`.
4. Run tests, wheel/sdist build, installed-wheel checks, and an explicitly selected live test.
5. Do not copy `.git`, `.venv`, profiles, keys, browser binaries or output containing live tokens.

The project name is descriptive and does not imply endorsement by either upstream.
