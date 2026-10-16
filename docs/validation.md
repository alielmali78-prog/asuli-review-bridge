# Validation record — 2026-10-17 (Europe/Istanbul)

Environment: Linux, Python 3.12.14. Reference edition 0.1.0 preview.

Actually executed:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **18/18 PASS**.
- `PYTHONPATH=src python3 examples/offline_demo.py`: **PASS**.
- `python3 -m pip wheel --no-deps --no-build-isolation .`: **PASS**.
- Wheel installed into a separate target directory: **PASS**.
- Installed-package CLI post → MOCK worker → decision → Markdown export:
  **PASS**, output `INSTALLED_WHEEL_CLI_ROUNDTRIP_PASS`.
- `git diff --check`: **PASS**.
- Targeted scan for known private paths/addresses, real-key patterns and account
  identifiers in deliverable sources: no matches. This is a bounded scan, not a
  claim of formal secret-audit certification.

Behavior tests cover duplicate worker invocation, separate database
connections, a real child process exiting after reservation, no automatic
retry, explicit network opt-in, empty/truncated responses, linkage, input
bounds and separation of operator decisions.

During development the first test run caught incorrect SQL placeholder counts
in reply persistence; these were corrected before the final passing run.

Not performed: paid live API acceptance, actual GitHub Actions run, physical
power-loss test, adversarial security audit, Windows/macOS acceptance,
quantitative model-quality benchmark, Notion/Telegram integration tests.

The included CI file is prepared configuration, not evidence that hosted CI
has run. The package has not been uploaded to GitHub or PyPI in this validation.
