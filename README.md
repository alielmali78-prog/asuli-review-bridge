# Asuli Review Bridge

**A small, traceable multi-model advisory workflow by Ali Elmalı.**

[Türkçe doküman](README.tr.md)

Ask Gemini, Claude (called **Abdur** in Asuli), or Kimi to critique a proposal.
Keep each reply linked to its question. Record the operator's reasoned decision
separately. A model reply never executes a command or grants approval.

This is a **portable reference extraction**, not a dump of the running Asuli
environment. It includes a complete offline demo and optional text-only API
adapters. The original deployment uses an append-only Markdown mailbox; this
edition deliberately uses SQLite for transactional reservations and exports
Markdown for reading. See [provenance](docs/provenance.md).

## Quick start (no API key, no network)

Python 3.11+; runtime uses the standard library only.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --no-build-isolation -e .
python examples/offline_demo.py
python -m unittest discover -s tests -v
```

If your venv lacks setuptools, install the build dependencies from
`pyproject.toml` first. Alternatively run without installation:

```bash
export PYTHONPATH="$PWD/src"
python examples/offline_demo.py
python -m unittest discover -s tests -v
```

The demo uses a temporary database and prints a synthetic question, a clearly
labeled mock reply, and a `NEEDS_EVIDENCE` decision. It is not a model benchmark.

## CLI

```bash
asuli-review post --to MOCK --file examples/review-request.md
asuli-review worker --to MOCK
asuli-review export
# Copy the request ID printed by post:
asuli-review decide --request REVIEW_ID --verdict NEEDS_EVIDENCE \
  --rationale "No scheduled execution trace supplied" \
  --evidence "Synthetic fixture only"
```

Use `--db /path/to/reviews.sqlite3` **before** the subcommand to select a database.
`ACCEPT` means the operator recorded an assessment; it does not start work.

## Optional live providers

Set the matching `*_API_KEY` and `*_MODEL` environment variables from
[.env.example](.env.example). The program does not load `.env` automatically.
Select a currently available text model yourself; no price or model availability
is promised. Kimi must support `thinking: {type: disabled}`.

```bash
asuli-review post --to KIMI --file examples/review-request.md
asuli-review worker --to KIMI --allow-network
```

Replace `KIMI` with `GEMINI` or `ABDUR`. Each worker invocation handles at most
one pending request, with a 12000-character input limit, 1200-token requested
output limit and 60-second HTTP timeout. **These are not a monetary hard cap.**
No automatic retries, model fallback, batch fan-out or scheduler is installed.
Live adapters were checked with mocked HTTP responses; this extracted edition
has **not** made paid live acceptance calls. See [provider references](docs/providers.md).

## State and guarantees

`PENDING → INFLIGHT → DONE` or `HOLD`.

A SQLite transaction reserves the request before the external call. A crash
after reservation leaves it `INFLIGHT`; a timeout or rejected response goes to
`HOLD`. Neither is automatically retried, because a provider may already have
accepted or charged for the request. There is no exactly-once external API
guarantee and no automatic crash recovery. See [operations](docs/operations.md).

## Scope

- Included: request/reply linkage, explicit decisions, SQLite storage, Markdown
  export, mock demo, three optional API adapters, behavior tests.
- Not included: production Asuli deployment, Gemini tool access, Notion/Telegram
  integration, a web UI, timers, automatic approval, cost accounting, benchmark.
- Supported test platform: Linux / Python 3.12. Other platforms are unverified.

Private messages, runtime databases, API keys, host addresses and personal
Notion pages are deliberately absent. Review the input before explicitly
sending it to an external provider.

## Article companion

The accompanying Turkish article is **“Üç Yapay Zekâya Sormak Yetmiyor:
Asuli’de Cevabı Karardan Nasıl Ayırıyoruz?”** It describes the original running
system. [Article mapping](docs/article-companion.md) distinguishes that system
from this reference implementation. No public article URL is asserted yet.

## License

Copyright 2026 Ali Elmalı. All rights reserved pending the owner's choice of
license. No open-source license is granted by this draft package. Provider SDKs
are not bundled. Public availability, if later enabled, is not a license grant.
