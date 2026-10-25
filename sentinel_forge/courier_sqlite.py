"""Non-normative SQLite durable backend for the disconnected Courier reference.

SQLite is an implementation choice here, not a WP6 architectural requirement.
No network or privileged operations are performed.
"""

from __future__ import annotations
from .secure_io import ensure_private_file

import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping

from .contract import ContractBundle
from .courier import CourierReceipt, CourierRejected, ConflictingReplay, _fingerprint

SCHEMA_VERSION = 1
MAX_RECORD_BYTES = 16 * 1024
MAX_RECORDS = 4096

class DurableStateError(RuntimeError): pass

class SQLiteDisconnectedCourier:
    def __init__(self, database: Path, courier_identity: str = "courier-reference"):
        if not courier_identity:
            raise DurableStateError("courier identity is required")
        self._path = Path(database)
        self._identity = courier_identity
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        ensure_private_file(self._path)
        con = sqlite3.connect(self._path, timeout=0.25, isolation_level=None)
        con.execute("PRAGMA busy_timeout=250")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            try:
                con.execute("""CREATE TABLE IF NOT EXISTS courier_meta (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    schema_version INTEGER NOT NULL,
                    courier_identity TEXT NOT NULL
                )""")
                con.execute("""CREATE TABLE IF NOT EXISTS courier_records (
                    correlation_identity TEXT PRIMARY KEY,
                    request_fingerprint TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    CHECK(length(correlation_identity) BETWEEN 1 AND 4096),
                    CHECK(length(request_fingerprint) BETWEEN 1 AND 4096),
                    CHECK(length(receipt_json) BETWEEN 2 AND 16384)
                )""")
                row=con.execute("SELECT schema_version,courier_identity FROM courier_meta WHERE singleton=1").fetchone()
                if row is None:
                    con.execute("INSERT INTO courier_meta VALUES(1,?,?)",(SCHEMA_VERSION,self._identity))
                elif row != (SCHEMA_VERSION,self._identity):
                    raise DurableStateError("database schema/authority identity mismatch")
                self._validate_schema(con)
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
        finally:
            con.close()

    def _validate_schema(self, con: sqlite3.Connection) -> None:
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != {"courier_meta","courier_records"}:
            raise DurableStateError("unexpected durable-state table set")
        meta=[r[1] for r in con.execute("PRAGMA table_info(courier_meta)")]
        records=[r[1] for r in con.execute("PRAGMA table_info(courier_records)")]
        if meta != ["singleton","schema_version","courier_identity"]:
            raise DurableStateError("malformed courier_meta schema")
        if records != ["correlation_identity","request_fingerprint","receipt_json"]:
            raise DurableStateError("malformed courier_records schema")

    def submit(self, objects: Mapping[str, Mapping[str, Any]]) -> CourierReceipt:
        result=ContractBundle(objects).validate()
        if not result.accepted:
            raise CourierRejected("proposal fails governing logical validation")
        request=dict(objects["TransferRequest"])
        correlation=request["correlation_identity"]
        fingerprint=_fingerprint(request)
        receipt={
            "courier_identity":self._identity,
            "source_identity":request["source_identity"],
            "destination":request["destination"],
            "transfer_operation":request["transfer_operation"],
            "work_package_revision":request["work_package_revision"],
            "authorization_reference":request["authorization_reference"],
            "artifact_identity":request["artifact_identity"],
            "correlation_identity":correlation,
            "policy_classification":request["classification_handling"],
            "transfer_disposition":"PROPOSED",
            "validation_outcome":"PASS_OFFLINE_ONLY",
            "completeness_state":"COMPLETE",
            "retry_reconciliation_state":request["prior_attempt_reconciliation_state"],
            "provenance":"DISCONNECTED_SQLITE_REFERENCE_COURIER",
        }
        encoded=_encode(receipt)
        if len(encoded.encode("utf-8")) > MAX_RECORD_BYTES:
            raise CourierRejected("receipt exceeds durable record bound")

        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            try:
                self._validate_schema(con)
                row=con.execute(
                    "SELECT request_fingerprint,receipt_json FROM courier_records WHERE correlation_identity=?",
                    (correlation,)).fetchone()
                if row is not None:
                    stored_fp,stored_json=row
                    if stored_fp != fingerprint:
                        raise ConflictingReplay("correlation identity reused for a different request")
                    stored=_decode_receipt(stored_json, correlation, stored_fp)
                    con.execute("COMMIT")
                    return CourierReceipt(stored,fingerprint,replayed=True)
                count=con.execute("SELECT COUNT(*) FROM courier_records").fetchone()[0]
                if count >= MAX_RECORDS:
                    raise DurableStateError("durable record bound reached")
                con.execute("INSERT INTO courier_records VALUES(?,?,?)",
                            (correlation,fingerprint,encoded))
                con.execute("COMMIT")
                return CourierReceipt(receipt,fingerprint)
            except Exception:
                con.execute("ROLLBACK")
                raise
        finally:
            con.close()

    def lookup(self, correlation_identity: str) -> CourierReceipt | None:
        con = self._connect()
        try:
            self._validate_schema(con)
            row=con.execute(
                "SELECT request_fingerprint,receipt_json FROM courier_records WHERE correlation_identity=?",
                (correlation_identity,)).fetchone()
            if row is None: return None
            fp,raw=row
            return CourierReceipt(_decode_receipt(raw,correlation_identity,fp),fp,replayed=True)
        finally:
            con.close()

def _encode(receipt: Mapping[str,Any]) -> str:
    return json.dumps(dict(receipt),sort_keys=True,separators=(",",":"))

def _decode_receipt(raw: str, correlation: str, fingerprint: str) -> dict[str,Any]:
    try:
        value=json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DurableStateError("malformed durable receipt JSON") from exc
    if not isinstance(value,dict):
        raise DurableStateError("durable receipt is not an object")
    if value.get("correlation_identity") != correlation:
        raise DurableStateError("durable receipt correlation mismatch")
    if value.get("transfer_disposition") != "PROPOSED":
        raise DurableStateError("disconnected backend contains impossible transfer disposition")
    if value.get("validation_outcome") != "PASS_OFFLINE_ONLY":
        raise DurableStateError("disconnected backend contains invalid validation outcome")
    return value
