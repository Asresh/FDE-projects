"""SQLite source ledger and durable reconciliation/alert records."""

import json
import sqlite3
from pathlib import Path


class Ledger:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def initialize(self):
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS processor_payouts (
                    payout_id TEXT PRIMARY KEY, event_id TEXT NOT NULL UNIQUE,
                    amount_cents INTEGER NOT NULL, currency TEXT NOT NULL,
                    expected_date TEXT NOT NULL, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bank_deposits (
                    payout_ref TEXT PRIMARY KEY, bank_ref TEXT NOT NULL UNIQUE,
                    amount_cents INTEGER NOT NULL, currency TEXT NOT NULL,
                    booked_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reconciliations (
                    payout_ref TEXT PRIMARY KEY, state TEXT NOT NULL,
                    processor_cents INTEGER, bank_cents INTEGER,
                    processor_currency TEXT, bank_currency TEXT,
                    delta_cents INTEGER, detail TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY, alert_key TEXT NOT NULL UNIQUE,
                    payout_ref TEXT NOT NULL, payload TEXT NOT NULL,
                    delivery_state TEXT NOT NULL DEFAULT 'pending', last_error TEXT
                );
            """)

    def save_processor_event(self, event):
        with self.connect() as db:
            exists = db.execute("SELECT 1 FROM processor_payouts WHERE event_id=? OR payout_id=?",
                                (event["event_id"], event["payout_id"])).fetchone()
            if exists:
                return False
            db.execute("INSERT INTO processor_payouts VALUES(?,?,?,?,?,?)",
                       (event["payout_id"], event["event_id"], event["amount_cents"],
                        event["currency"], event["expected_date"],
                        json.dumps(event["payload"], sort_keys=True)))
            return True

    def import_bank_rows(self, rows):
        inserted = 0
        updated = 0
        duplicates = 0
        with self.connect() as db:
            for row in rows:
                prior = db.execute("SELECT * FROM bank_deposits WHERE payout_ref=?",
                                   (row["payout_ref"],)).fetchone()
                ref_owner = db.execute("SELECT payout_ref FROM bank_deposits WHERE bank_ref=?",
                                       (row["bank_ref"],)).fetchone()
                if ref_owner and ref_owner["payout_ref"] != row["payout_ref"]:
                    raise ValueError(f"bank_ref {row['bank_ref']} is already linked to another payout")
                values = (row["bank_ref"], row["amount_cents"], row["currency"], row["booked_at"])
                if prior and tuple(prior[key] for key in
                                   ("bank_ref", "amount_cents", "currency", "booked_at")) == values:
                    duplicates += 1
                    continue
                if prior:
                    db.execute("UPDATE bank_deposits SET bank_ref=?,amount_cents=?,currency=?,booked_at=? WHERE payout_ref=?",
                               (*values, row["payout_ref"]))
                    updated += 1
                else:
                    db.execute("INSERT INTO bank_deposits VALUES(?,?,?,?,?)",
                               (row["payout_ref"], *values))
                    inserted += 1
        return {"inserted": inserted, "updated": updated, "duplicates": duplicates}

    def source_records(self):
        with self.connect() as db:
            processor = {row["payout_id"]: dict(row) for row in db.execute(
                "SELECT * FROM processor_payouts ORDER BY payout_id")}
            bank = {row["payout_ref"]: dict(row) for row in db.execute(
                "SELECT * FROM bank_deposits ORDER BY payout_ref")}
        return processor, bank

    def save_reconciliations(self, rows, updated_at):
        with self.connect() as db:
            for row in rows:
                db.execute("""INSERT INTO reconciliations VALUES(?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(payout_ref) DO UPDATE SET state=excluded.state,
                    processor_cents=excluded.processor_cents, bank_cents=excluded.bank_cents,
                    processor_currency=excluded.processor_currency, bank_currency=excluded.bank_currency,
                    delta_cents=excluded.delta_cents, detail=excluded.detail, updated_at=excluded.updated_at""",
                    (row["payout_ref"], row["state"], row["processor_cents"], row["bank_cents"],
                     row["processor_currency"], row["bank_currency"], row["delta_cents"],
                     row["detail"], updated_at))
                if row["state"] == "matched":
                    db.execute("UPDATE alerts SET delivery_state='resolved',last_error=NULL "
                               "WHERE payout_ref=? AND delivery_state='pending'",
                               (row["payout_ref"],))
                else:
                    alert = {"payout_ref": row["payout_ref"], "state": row["state"],
                             "processor_cents": row["processor_cents"], "bank_cents": row["bank_cents"],
                             "delta_cents": row["delta_cents"], "detail": row["detail"]}
                    key = f"{row['payout_ref']}:{row['state']}"
                    db.execute("UPDATE alerts SET delivery_state='superseded',last_error=NULL "
                               "WHERE payout_ref=? AND delivery_state='pending' AND alert_key<>?",
                               (row["payout_ref"], key))
                    db.execute("""INSERT INTO alerts(alert_key,payout_ref,payload) VALUES(?,?,?)
                        ON CONFLICT(alert_key) DO UPDATE SET payload=excluded.payload,
                        delivery_state='pending',last_error=NULL
                        WHERE alerts.delivery_state IN ('resolved','superseded')""",
                        (key, row["payout_ref"], json.dumps(alert, sort_keys=True)))

    def reconciliations(self):
        with self.connect() as db:
            rows = [dict(row) for row in db.execute(
                "SELECT * FROM reconciliations ORDER BY payout_ref")]
        return rows

    def pending_alerts(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM alerts WHERE delivery_state='pending' ORDER BY id")]

    def mark_alert(self, alert_key, state, error=None):
        with self.connect() as db:
            db.execute("UPDATE alerts SET delivery_state=?,last_error=? WHERE alert_key=?",
                       (state, error, alert_key))

    def alerts(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM alerts ORDER BY id")]

    def health(self):
        with self.connect() as db:
            db.execute("SELECT 1").fetchone()
        return True
