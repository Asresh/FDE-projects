"""Validation and source adapters for processor events and bank CSV rows."""

import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation


class InputError(ValueError):
    pass


def _text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise InputError(f"{field} must be a non-empty string of at most 128 characters")
    return value.strip()


def validate_processor_event(event):
    if not isinstance(event, dict):
        raise InputError("processor event must be a JSON object")
    if event.get("type") != "payout.settled":
        raise InputError("event type must be payout.settled")
    event_id = _text(event.get("event_id"), "event_id")
    data = event.get("data")
    if not isinstance(data, dict):
        raise InputError("data must be a JSON object")
    payout_id = _text(data.get("payout_id"), "payout_id")
    amount = data.get("amount_cents")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise InputError("amount_cents must be a positive integer")
    currency = data.get("currency")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        raise InputError("currency must be a three-letter uppercase code")
    expected_date = data.get("expected_date")
    try:
        date.fromisoformat(expected_date)
    except (TypeError, ValueError) as exc:
        raise InputError("expected_date must use YYYY-MM-DD format") from exc
    return {"event_id": event_id, "payout_id": payout_id, "amount_cents": amount,
            "currency": currency, "expected_date": expected_date, "payload": event}


REQUIRED_COLUMNS = ("payout_ref", "bank_ref", "amount", "currency", "booked_at")


def parse_bank_csv(content):
    if not isinstance(content, str) or len(content.encode("utf-8")) > 65536:
        raise InputError("CSV must be text no larger than 65536 bytes")
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames or any(name not in reader.fieldnames for name in REQUIRED_COLUMNS):
        raise InputError("CSV header must include: " + ", ".join(REQUIRED_COLUMNS))
    rows = []
    seen_payouts = set()
    for line_number, row in enumerate(reader, start=2):
        if None in row or any(row.get(key) is None for key in REQUIRED_COLUMNS):
            raise InputError(f"CSV row {line_number} has the wrong number of columns")
        payout_ref = _text(row["payout_ref"], f"row {line_number} payout_ref")
        bank_ref = _text(row["bank_ref"], f"row {line_number} bank_ref")
        if payout_ref in seen_payouts:
            raise InputError(f"duplicate payout_ref on CSV row {line_number}: {payout_ref}")
        seen_payouts.add(payout_ref)
        try:
            amount = Decimal(row["amount"].strip())
        except (InvalidOperation, AttributeError) as exc:
            raise InputError(f"CSV row {line_number} amount must be a decimal currency value") from exc
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise InputError(f"CSV row {line_number} amount must be positive with at most two decimals")
        cents = int(amount * 100)
        currency = row["currency"].strip()
        if not re.fullmatch(r"[A-Z]{3}", currency):
            raise InputError(f"CSV row {line_number} currency must be a three-letter uppercase code")
        booked_at = row["booked_at"].strip()
        try:
            date.fromisoformat(booked_at)
        except ValueError as exc:
            raise InputError(f"CSV row {line_number} booked_at must use YYYY-MM-DD format") from exc
        rows.append({"payout_ref": payout_ref, "bank_ref": bank_ref, "amount_cents": cents,
                     "currency": currency, "booked_at": booked_at})
        if len(rows) > 1000:
            raise InputError("CSV import is limited to 1000 rows")
    if not rows:
        raise InputError("CSV contains no bank statement rows")
    return rows
