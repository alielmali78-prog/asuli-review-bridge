# Provenance: original scripts versus portable extraction

Prepared for Ali Elmalı from the existing Asuli advisory scripts, 2026-10-17.
Original source files inspected read-only:

- `mailbox_common.py`: message metadata, linked replies, append-only Markdown.
- `mailbox_post.py`: sender/recipient/body CLI.
- `mailbox_worker.py`: Gemini review routing and quota behavior.
- `kimi_mailbox_worker.py`: text-only Kimi adapter and output guards.
- `claude_mailbox_worker.py`: Claude adapter and pre-call reservation ledger.

No source runtime directories, private histories or credential files are
copied. This repository is an adaptation, not a claim that these exact modules
ran in the original acceptance tests.

Intentional differences:

| Original deployment | Reference edition |
| --- | --- |
| Shared Markdown mailbox plus worker state | SQLite canonical store, Markdown export |
| Fedora-specific paths and services | Caller-selected local database; no services |
| Gemini read-only tool routing | Text-only adapters for every provider |
| Existing Telegram/Notion integration | No account integrations |
| Private model aliases and pilot budgets | Explicit model selection; no price assumptions |
| Original production acceptance records | Separate offline behavior tests |

The original append-only mailbox used a file lock and flush, not an fsync-based
message transaction. The extraction's SQLite reservations are a new design
choice. They must not be retroactively attributed to the original system.
