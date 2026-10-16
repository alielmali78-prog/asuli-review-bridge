import argparse
import json
from pathlib import Path

from .providers import ProviderError, ask
from .store import Store, RECIPIENTS


def process_one(store, recipient, allow_network=False, transport=None):
    # Misconfigured credentials/network must not consume a pending request.
    if recipient != "MOCK" and not allow_network:
        raise ProviderError("Network disabled; explicit --allow-network required")
    request = store.claim(recipient)
    if not request:
        return {"status": "NO_PENDING"}
    try:
        result = ask(recipient, request["body"], allow_network=allow_network, transport=transport)
        store.complete(request["id"], result)
        return {"status": "DONE", "request_id": request["id"]}
    except Exception:
        store.hold(request["id"], "ADAPTER_FAILED_OR_OUTPUT_REJECTED")
        return {"status": "HOLD", "request_id": request["id"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Traceable advisory reviews; offline by default")
    parser.add_argument("--db", default="data/reviews.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    post = commands.add_parser("post")
    post.add_argument("--to", choices=sorted(RECIPIENTS), required=True)
    post.add_argument("--file", type=Path, required=True)
    worker = commands.add_parser("worker")
    worker.add_argument("--to", choices=sorted(RECIPIENTS), required=True)
    worker.add_argument("--allow-network", action="store_true")
    commands.add_parser("export")
    decision = commands.add_parser("decide")
    decision.add_argument("--request", required=True)
    decision.add_argument("--verdict", choices=["ACCEPT", "REJECT", "NEEDS_EVIDENCE"], required=True)
    decision.add_argument("--rationale", required=True)
    decision.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)
    store = Store(args.db)
    try:
        if args.command == "post":
            print(store.post(args.to, args.file.read_text(encoding="utf-8")))
        elif args.command == "worker":
            result = process_one(store, args.to, args.allow_network)
            print(json.dumps(result))
            return 2 if result["status"] == "HOLD" else 0
        elif args.command == "export":
            print(store.export())
        else:
            store.decide(args.request, args.verdict, args.rationale, args.evidence)
            print("DECISION_RECORDED; no execution triggered")
        return 0
    except (ValueError, ProviderError, OSError):
        parser.exit(2, "Invalid input/configuration or unavailable file; no automatic retry.\n")
    finally:
        store.close()
