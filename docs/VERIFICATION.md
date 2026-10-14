# Verification record

The repository was checked on 2026-10-14 with Python 3.12.7 on Windows.

| Check | Result |
|---|---|
| `python -m ruff check src tests` | pass |
| `python -m pytest -q` | 25 passed |
| Package resource test | pass; MV3 manifest and script are present |
| Browser launch test | mocked; exact target ID is passed to the CDP challenge component |
| Real challenge solve | not run in this build; it requires a downloaded browser runtime, visible desktop, Node 22+, target network access and a live page |
| CLI presentation | product name and stable command help tested |

## Reproduce locally

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build
```

Then run the explicit integration check:

```powershell
.\.venv\Scripts\cloak-turnstile.exe doctor
.\.venv\Scripts\cloak-turnstile.exe fetch
.\.venv\Scripts\cloak-turnstile.exe solve --url https://demo.turnstile.workers.dev/ --timeout 45
```

The last command is a live check and returns one JSON object. Keep its output private; tokens and clearance values are session-bound. A successful client result has `ok: true` and either `tokenLen > 20` or `clearanceLen > 20`. That completeness check does not establish server-side acceptance.

## What this check does not establish

Local unit tests do not prove that a production Cloudflare policy will accept a token. IP reputation, site configuration, challenge mode, profile state, browser version, proxy, and token lifetime are external variables. The adapter reports the upstream failure directly so those conditions remain visible.
