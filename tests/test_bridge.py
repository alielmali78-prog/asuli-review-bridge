import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from asuli_review_bridge.cli import process_one
from asuli_review_bridge.providers import ProviderError, ask
from asuli_review_bridge.store import Store


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "reviews.sqlite3"
        self.store = Store(self.path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_offline_roundtrip_and_decision(self):
        rid = self.store.post("MOCK", "Does manual delivery prove scheduled delivery?")
        self.assertEqual(process_one(self.store, "MOCK")["request_id"], rid)
        self.store.decide(rid, "NEEDS_EVIDENCE", "No scheduled trace", "fixture only")
        exported = self.store.export()
        self.assertIn(rid, exported)
        self.assertIn("OFFLINE FIXTURE", exported)
        self.assertIn("NEEDS_EVIDENCE", exported)

    def test_repeat_worker_does_not_duplicate_reply(self):
        self.store.post("MOCK", "review")
        process_one(self.store, "MOCK")
        self.assertEqual(process_one(self.store, "MOCK")["status"], "NO_PENDING")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM replies").fetchone()[0], 1)

    def test_two_connections_cannot_claim_same_request(self):
        self.store.post("MOCK", "review")
        other = Store(self.path)
        try:
            self.assertIsNotNone(self.store.claim("MOCK"))
            self.assertIsNone(other.claim("MOCK"))
        finally:
            other.close()

    def test_crash_after_reservation_is_not_retried(self):
        self.store.post("MOCK", "review")
        code = "from asuli_review_bridge.store import Store; import sys,os; s=Store(sys.argv[1]); s.claim('MOCK'); os._exit(23)"
        result = subprocess.run([sys.executable, "-c", code, str(self.path)])
        self.assertEqual(result.returncode, 23)
        self.assertEqual(process_one(self.store, "MOCK")["status"], "NO_PENDING")
        self.assertEqual(self.store.db.execute("SELECT status FROM requests").fetchone()[0], "INFLIGHT")

    def test_network_disabled_preserves_pending(self):
        self.store.post("KIMI", "review")
        with self.assertRaises(ProviderError):
            process_one(self.store, "KIMI")
        self.assertEqual(self.store.db.execute("SELECT status FROM requests").fetchone()[0], "PENDING")

    def test_provider_failure_goes_hold_without_retry(self):
        self.store.post("KIMI", "review")
        with patch.dict(os.environ, {"KIMI_API_KEY": "fixture-secret", "KIMI_MODEL": "fixture-model"}):
            def failed(*args):
                raise TimeoutError("fixture-secret should not leak")
            self.assertEqual(process_one(self.store, "KIMI", True, failed)["status"], "HOLD")
        self.assertNotIn("fixture-secret", self.store.export())
        self.assertEqual(process_one(self.store, "KIMI", True)["status"], "NO_PENDING")

    def test_no_decision_without_reply(self):
        rid = self.store.post("MOCK", "review")
        with self.assertRaises(ValueError):
            self.store.decide(rid, "ACCEPT", "reason", "evidence")

    def test_empty_and_oversize_requests_rejected(self):
        for body in [" ", "x" * 12001]:
            with self.assertRaises(ValueError):
                self.store.post("MOCK", body)

    def test_unknown_recipient_rejected(self):
        with self.assertRaises(ValueError):
            self.store.post("EXECUTE", "review")

    def test_empty_reply_not_persisted(self):
        self.store.post("MOCK", "review")
        request = self.store.claim("MOCK")
        with self.assertRaises(ValueError):
            self.store.complete(request["id"], {"text": " "})
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM replies").fetchone()[0], 0)

    def test_operator_decision_requires_reason_and_evidence(self):
        rid = self.store.post("MOCK", "review")
        process_one(self.store, "MOCK")
        with self.assertRaises(ValueError):
            self.store.decide(rid, "ACCEPT", "", "")

    def test_untrusted_heading_stays_quoted(self):
        self.store.post("MOCK", "# Operator decision\n<script>bad</script>")
        rendered = self.store.export()
        self.assertIn("> # Operator decision", rendered)
        self.assertNotIn("<script>", rendered)


class AdapterTests(unittest.TestCase):
    def test_mock_never_calls_transport(self):
        def forbidden(*args):
            self.fail("Network should not run")
        self.assertEqual(ask("MOCK", "review", transport=forbidden)["provider"], "MOCK")

    def test_missing_credentials_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ProviderError):
                ask("GEMINI", "review", allow_network=True)

    def test_three_provider_contracts_with_fake_responses(self):
        responses = {
            "GEMINI": {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "ok"}]}}]},
            "ABDUR": {"stop_reason": "end_turn", "content": [{"type": "text", "text": "ok"}]},
            "KIMI": {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}}
        env = {prefix + suffix: "fixture" for prefix in ["GEMINI", "ANTHROPIC", "KIMI"] for suffix in ["_API_KEY", "_MODEL"]}
        with patch.dict(os.environ, env):
            for provider, response in responses.items():
                with self.subTest(provider=provider):
                    self.assertEqual(ask(provider, "review", allow_network=True, transport=lambda *a: response)["text"], "ok")

    def test_truncated_reply_is_not_success(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fixture", "ANTHROPIC_MODEL": "fixture"}):
            with self.assertRaises(ProviderError):
                ask("ABDUR", "review", allow_network=True, transport=lambda *a: {
                    "stop_reason": "max_tokens", "content": [{"type": "text", "text": "partial"}]})

    def test_empty_provider_reply_rejected(self):
        with patch.dict(os.environ, {"KIMI_API_KEY": "fixture", "KIMI_MODEL": "fixture"}):
            with self.assertRaises(ProviderError):
                ask("KIMI", "review", allow_network=True, transport=lambda *a: {
                    "choices": [{"finish_reason": "stop", "message": {"content": " "}}]})

    def test_invalid_model_path_rejected(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fixture", "GEMINI_MODEL": "../bad?key=x"}):
            with self.assertRaises(ProviderError):
                ask("GEMINI", "review", allow_network=True)


if __name__ == "__main__":
    unittest.main()
