# Third-party notices

## turnstile-bypass

- Source: https://github.com/Sophomoresty/turnstile-bypass
- Commit: `abff97cb5345bcff0609472e5b2b789f1f9a9e18`
- Copyright (c) 2026 Sophomoresty; MIT license in `licenses/turnstile-bypass-MIT.txt`.
- Included: `scripts/solve_agent_browser.py`, `scripts/runtime.py`, `assets/turnstilePatch/manifest.json`, `assets/turnstilePatch/script.js`.
- Location: `src/cloak_turnstile/_vendor/turnstile/`.
- Change: replace the solver's global `sys.path` / `import runtime` block with a package-relative import. No change to the challenge algorithm. Package marker files are added for distribution.

## CloakBrowser

- Source: https://github.com/CloakHQ/CloakBrowser
- Reviewed commit: `04c3c027c2b68e0a929a5da1ae5ebf82e3aee423`; wrapper version 0.6.2.
- Copyright (c) 2026 CloakHQ; wrapper MIT license in `licenses/CloakBrowser-wrapper-MIT.txt`.
- Installed through the Python dependency `cloakbrowser==0.6.2`; wrapper source and browser binary are not vendored.
- Browser binaries are downloaded by users directly through official CloakBrowser distribution. They are covered by a separate [binary license](https://github.com/CloakHQ/CloakBrowser/blob/04c3c027c2b68e0a929a5da1ae5ebf82e3aee423/BINARY-LICENSE.md), not this project's MIT license.

Playwright and other transitive dependencies retain their respective upstream licenses; this repository does not bundle their runtimes.
