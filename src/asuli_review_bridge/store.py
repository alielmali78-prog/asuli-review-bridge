"""SQLite is canonical; Markdown is a human-readable projection, not a queue."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

RECIPIENTS = {"GEMINI", "ABDUR", "KIMI", "MOCK"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS requests (
          id TEXT PRIMARY KEY, created_at TEXT NOT NULL, recipient TEXT NOT NULL,
          body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', error TEXT);
        CREATE TABLE IF NOT EXISTS replies (
          id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE REFERENCES requests(id),
          created_at TEXT NOT NULL, body TEXT NOT NULL, provider TEXT NOT NULL,
          model TEXT NOT NULL, usage TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS decisions (
          id TEXT PRIMARY KEY, request_id TEXT NOT NULL REFERENCES requests(id),
          created_at TEXT NOT NULL, verdict TEXT NOT NULL, rationale TEXT NOT NULL,
          evidence TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    def post(self, recipient, body):
        recipient = recipient.upper()
        if recipient not in RECIPIENTS:
            raise ValueError("Unsupported recipient")
        if not body.strip() or len(body) > 12000:
            raise ValueError("Request must contain 1–12000 characters")
        rid = "review-" + uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO requests(id,created_at,recipient,body) VALUES(?,?,?,?)",
                            (rid, now(), recipient, body.strip()))
        return rid

    def claim(self, recipient):
        # Commit the reservation BEFORE any network request. Concurrent workers
        # cannot claim the same request. A crash leaves UNKNOWN/INFLIGHT, never
        # an automatic repeat of a possibly billed call.
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT * FROM requests WHERE recipient=? AND status='PENDING' ORDER BY rowid LIMIT 1",
                                  (recipient,)).fetchone()
            if row:
                self.db.execute("UPDATE requests SET status='INFLIGHT' WHERE id=?", (row["id"],))
            self.db.commit()
            return dict(row) if row else None
        except BaseException:
            self.db.rollback()
            raise

    def complete(self, request_id, result):
        if not isinstance(result.get("text"), str) or not result["text"].strip():
            raise ValueError("Empty reply")
        with self.db:
            row = self.db.execute("SELECT status FROM requests WHERE id=?", (request_id,)).fetchone()
            if not row or row[0] != "INFLIGHT":
                raise ValueError("Request is not INFLIGHT")
            self.db.execute("INSERT INTO replies VALUES(?,?,?,?,?,?,?)",
                            ("reply-" + uuid.uuid4().hex, request_id, now(), result["text"].strip(),
                             result["provider"], result["model"], json.dumps(result.get("usage", {}))))
            self.db.execute("UPDATE requests SET status='DONE',error=NULL WHERE id=?", (request_id,))

    def hold(self, request_id, error):
        with self.db:
            self.db.execute("UPDATE requests SET status='HOLD',error=? WHERE id=? AND status='INFLIGHT'",
                            (error, request_id))

    def decide(self, request_id, verdict, rationale, evidence):
        if verdict not in {"ACCEPT", "REJECT", "NEEDS_EVIDENCE"}:
            raise ValueError("Invalid verdict")
        if not rationale.strip() or not evidence.strip():
            raise ValueError("Rationale and evidence reference required")
        with self.db:
            if not self.db.execute("SELECT 1 FROM replies WHERE request_id=?", (request_id,)).fetchone():
                raise ValueError("A completed reply is required")
            self.db.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?)",
                            ("decision-" + uuid.uuid4().hex, request_id, now(), verdict, rationale, evidence))

    def export(self):
        lines = ["# Asuli Review Bridge", "", "Generated from SQLite. Advisory output is untrusted text.", ""]
        for row in self.db.execute("SELECT * FROM requests ORDER BY rowid"):
            lines += ["## " + row["id"], "", "- Recipient: " + row["recipient"],
                      "- Status: " + row["status"], "- Created: " + row["created_at"], "", "### Request", ""]
            # Quote all external content so model-supplied headings/HTML are not
            # presented as trusted decision sections in the projection.
            lines += ["> " + line.replace("<", "&lt;").replace(">", "&gt;") for line in row["body"].splitlines()]
            reply = self.db.execute("SELECT * FROM replies WHERE request_id=?", (row["id"],)).fetchone()
            if reply:
                lines += ["", "### Advisory reply", "", "Provider/model: " + reply["provider"] + "/" + reply["model"], ""]
                lines += ["> " + line.replace("<", "&lt;").replace(">", "&gt;") for line in reply["body"].splitlines()]
            for decision in self.db.execute("SELECT * FROM decisions WHERE request_id=? ORDER BY rowid", (row["id"],)):
                lines += ["", "### Operator decision", "", decision["verdict"], "",
                          "Rationale: " + decision["rationale"], "Evidence: " + decision["evidence"]]
            lines += [""]
        return "\n".join(lines)
