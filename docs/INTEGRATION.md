# Runtime architecture

```text
CLI / Python call
  -> validate SolveOptions
  -> allocate temporary or persistent profile
  -> launch a headed browser context
  -> navigate and bind the exact CDP target
  -> run challenge handling over loopback CDP
  -> check token / clearance completeness
  -> return JSON, close browser, clean temporary profile
```

## Responsibilities

| Layer | Responsibility |
|---|---|
| `cli.py` | Commands, option parsing, stdout/stderr separation and exit codes |
| `runner.py` | Options, browser lifecycle, profile ownership and result checking |
| Browser runtime | Binary selection, fingerprint configuration, proxy configuration and launch |
| CDP challenge component | Inspect the active page and attempt challenge handling |
| Compatibility extension | Mouse-event compatibility inside challenge frames |

The runtime uses CloakBrowser's official persistent-context API. The CDP challenge component and extension are maintained copies of third-party code. Exact origins, revisions and modifications are recorded in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and `upstream-lock.json`.

## One browser owner

The runner owns one browser context for the entire request. Navigation and challenge interactions address the same browser session, so proxy settings and profile state remain consistent between phases. The challenge component does not start a second browser or choose a replacement service on failure.

## Semantics

- A per-run CDP port is bound only to 127.0.0.1. There is a small allocation/launch race after releasing the ephemeral socket; a launch error propagates instead of attaching to another browser.
- Use the actual Playwright page's CDP target ID, not an arbitrary tab from `/json/list`.
- The browser context is closed after extracting the result. A temporary profile is removed after close; a user-selected profile is retained even on failure. Concurrent processes must not share one profile.
- The runner checks token/clearance length independently of `kind`. A `cf_passed` result without a token or clearance is rejected. Length greater than 20 satisfies the client's completeness check, not cryptographic validation or server-side acceptance.
- Clearance values are not copied into output. An explicitly selected profile retains the browser session.
- Mouse interactions use raw CDP. The runtime's Playwright `humanize` option is not exposed because it does not change that interaction path.
- The mouse-event compatibility extension is loaded by default, and may be explicitly disabled. Current binaries may already fix CDP mouse coordinates; compatibility depends on the binary/site.
- HTTP/HTTPS URLs only. No automatic timeout retries, proxy rotation or replacement browser.

## Maintenance

1. Review dependency/API changes and licensing before updating.
2. Record third-party revisions and modifications in the provenance files.
3. Run tests, package builds and installed-wheel resource checks.
4. Run a separate browser-level test before claiming live target compatibility.
5. Keep profiles, credentials, browser binaries and real tokens out of the repository.

The project does not imply endorsement by its dependency providers.
