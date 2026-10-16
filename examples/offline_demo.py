"""Run after installation: python examples/offline_demo.py"""
from pathlib import Path
from tempfile import TemporaryDirectory
from asuli_review_bridge.store import Store
from asuli_review_bridge.cli import process_one

with TemporaryDirectory() as directory:
    store = Store(Path(directory) / "demo.sqlite3")
    request = store.post("MOCK", Path(__file__).with_name("review-request.md").read_text())
    print(process_one(store, "MOCK"))
    store.decide(request, "NEEDS_EVIDENCE", "Manual readback does not prove scheduled execution.",
                 "Synthetic example: no scheduled-run trace supplied")
    print(store.export())
    store.close()
