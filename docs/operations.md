# Operations

Run workers manually. No daemon or timer is installed. Calls are text only;
providers receive no system tools, filesystem access or execution privileges.

## Interrupted calls

Inspect `INFLIGHT` and `HOLD` using SQLite or the Markdown export. Before
re-submitting, reconcile provider-side activity and charges. Create a new
request only after deciding whether another call is appropriate. There is
deliberately no automatic reset/requeue command.

The at-most-once claim protects one local request from duplicate workers;
it does not make an external provider exactly-once. Failure after a provider
responds but before the local commit can lose the reply while keeping a billed
call. Store the database and protect its backups accordingly.

## Data handling

Keep the database outside a source checkout when processing private content.
`data/`, `.env` and SQLite files are git-ignored. Exported Markdown can contain
the full question, reply and operator evidence references. Never commit private
exports. Use only synthetic examples in a public repository.

## Acceptance before live use

1. Run offline tests and demo.
2. Select a supported model and check provider access/pricing.
3. Send one non-sensitive synthetic live question with explicit network opt-in.
4. Confirm stop reason, nonempty reply, linkage and usage in SQLite.
5. Exercise a rejected/truncated response and confirm HOLD with no retry.

Steps 3–5 have not been completed against live providers in this extracted
edition. The original Asuli deployment's acceptance is not inherited.
