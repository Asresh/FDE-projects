"""SQLite inventory, sensor evidence, exception, and notification outbox."""

import json
import sqlite3
from pathlib import Path


class Repository:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def initialize(self):
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS inventory (
                    lot_id TEXT PRIMARY KEY, product TEXT NOT NULL,
                    location_id TEXT NOT NULL, min_c REAL NOT NULL, max_c REAL NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0)
                );
                CREATE INDEX IF NOT EXISTS inventory_location ON inventory(location_id);
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY, event_id TEXT NOT NULL, sensor_id TEXT NOT NULL,
                    location_id TEXT NOT NULL, observed_at TEXT NOT NULL,
                    temperature_c REAL NOT NULL, payload TEXT NOT NULL,
                    UNIQUE(sensor_id, event_id)
                );
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY, reading_id INTEGER NOT NULL UNIQUE REFERENCES readings(id),
                    status TEXT NOT NULL, severity TEXT NOT NULL, summary TEXT NOT NULL,
                    lot_ids TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    id INTEGER PRIMARY KEY, case_id TEXT NOT NULL UNIQUE REFERENCES cases(id),
                    idempotency_key TEXT NOT NULL UNIQUE, payload TEXT NOT NULL,
                    delivery_state TEXT NOT NULL DEFAULT 'pending', last_error TEXT
                );
            """)

    def import_inventory(self, records):
        with self.connect() as db:
            for row in records:
                db.execute("""INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(lot_id) DO UPDATE SET product=excluded.product,
                    location_id=excluded.location_id, min_c=excluded.min_c,
                    max_c=excluded.max_c, quantity=excluded.quantity""",
                    (row["lot_id"], row["product"], row["location_id"], row["min_c"],
                     row["max_c"], row["quantity"]))

    def lots_at(self, location_id):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM inventory WHERE location_id=? ORDER BY lot_id", (location_id,))]

    def save_reading(self, event):
        with self.connect() as db:
            cur = db.execute("""INSERT OR IGNORE INTO readings
                (event_id,sensor_id,location_id,observed_at,temperature_c,payload)
                VALUES(?,?,?,?,?,?)""",
                (event["event_id"], event["sensor_id"], event["location_id"],
                 event["observed_at"], event["temperature_c"], json.dumps(event, sort_keys=True)))
            if cur.rowcount == 0:
                row = db.execute("SELECT id FROM readings WHERE sensor_id=? AND event_id=?",
                                 (event["sensor_id"], event["event_id"])).fetchone()
                return row["id"], False
            return cur.lastrowid, True

    def reading_result(self, reading_id):
        with self.connect() as db:
            reading = db.execute("SELECT * FROM readings WHERE id=?", (reading_id,)).fetchone()
            case = db.execute("SELECT * FROM cases WHERE reading_id=?", (reading_id,)).fetchone()
            return dict(reading) if reading else None, dict(case) if case else None

    def create_case(self, case_id, reading_id, severity, summary, lot_ids, created_at):
        with self.connect() as db:
            db.execute("""INSERT OR IGNORE INTO cases
                (id,reading_id,status,severity,summary,lot_ids,created_at)
                VALUES(?,?,'open',?,?,?,?)""",
                (case_id, reading_id, severity, summary, json.dumps(lot_ids), created_at))
            row = db.execute("SELECT * FROM cases WHERE reading_id=?", (reading_id,)).fetchone()
            if not row:
                return None
            payload = {"case_id": row["id"], "severity": row["severity"],
                       "summary": row["summary"], "lot_ids": json.loads(row["lot_ids"]),
                       "idempotency_key": row["id"]}
            db.execute("INSERT OR IGNORE INTO outbox(case_id,idempotency_key,payload) VALUES(?,?,?)",
                       (row["id"], row["id"], json.dumps(payload, sort_keys=True)))
            return dict(row)

    def mark_delivery(self, case_id, state, error=None):
        with self.connect() as db:
            db.execute("UPDATE outbox SET delivery_state=?,last_error=? WHERE case_id=?",
                       (state, error, case_id))

    def cases(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM cases ORDER BY created_at,id")]

    def outbox(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM outbox ORDER BY id")]

    def health(self):
        with self.connect() as db:
            db.execute("SELECT 1").fetchone()
        return True
