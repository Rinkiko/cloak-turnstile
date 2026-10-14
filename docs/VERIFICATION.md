# Verification record

The repository was checked on 2026-10-14 with Python 3.12.7 on Windows.

| Check | Result |
|---|---|
| `python -m ruff check src tests` | pass |
| `python -m pytest -q` | 24 passed |
| Package resource test | pass; MV3 manifest and script are present |
| Browser launch test | mocked; exact target ID is passed to the upstream CDP solver |
| Real challenge solve | not run in this build; it requires a downloaded CloakBrowser binary, visible desktop, Node 22+, target network access and a live page |

## Reproduce locally

```powershell
$env:TEMP = 'D:\CodexProjects\.tmp'
$env:TMP = $env:TEMP
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

The last command is a live check and returns one JSON object. Keep its output private; tokens and clearance values are session-bound. A successful result has `ok: true` and `tokenLen > 20`, `clearanceLen > 20`, or `kind: both`.

## What this check does not establish

Local unit tests do not prove that a production Cloudflare policy will accept a token. IP reputation, site configuration, challenge mode, profile state, browser version, proxy, and token lifetime are external variables. The adapter reports the upstream failure directly so those conditions remain visible.
