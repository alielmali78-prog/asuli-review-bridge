# Provider contracts

The adapters use direct HTTP and keep credentials in headers. No provider SDK
or secrets are bundled. The caller chooses a model; provider terms, retention,
regional availability and fees remain the caller's responsibility.

Official contract references consulted while preparing this version:

- Gemini generateContent: https://ai.google.dev/api/generate-content
- Claude Messages stop reasons: https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons
- Moonshot official Kimi example (thinking disabled): https://github.com/MoonshotAI/Kimi-K2.5

Gemini accepts only `finishReason=STOP`; Claude accepts only
`stop_reason=end_turn`; Kimi accepts only `finish_reason=stop`. Empty,
truncated, blocked, tool-use or malformed responses are rejected. A natural
stop does not prove factual correctness or a complete argument.

No model-specific automatic fallback is attempted. Some models may need
different parameters; treat provider/schema changes as HOLD and update/test
the adapter before another live call. API usage values are stored but not
converted to currency; there is no local financial budget ledger.
