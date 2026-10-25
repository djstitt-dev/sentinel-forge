"""Durable effect-attempt coordinator for a future Courier transport."""

from __future__ import annotations
from .secure_io import ensure_private_file
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping
from .courier import ConflictingReplay, CourierRejected, _fingerprint
from .contract import ContractBundle
from .transport import Transport, TransportOutcome

class EffectStateError(RuntimeError): pass
class ReconciliationRequired(EffectStateError): pass

FINAL={"TRANSFERRED","REJECTED"}
UNCERTAIN={"PARTIAL","OUTCOME_UNKNOWN"}

class DurableEffectCoordinator:
    def __init__(self, database: Path):
        self.path=Path(database); self.path.parent.mkdir(parents=True,exist_ok=True)
        con=self._connect()
        try:
            con.execute("""CREATE TABLE IF NOT EXISTS effect_attempts(
                correlation_identity TEXT PRIMARY KEY,
                request_fingerprint TEXT NOT NULL,
                state TEXT NOT NULL,
                acknowledgement TEXT,
                CHECK(state IN ('PREPARED','IN_FLIGHT','TRANSFERRED','REJECTED','PARTIAL','OUTCOME_UNKNOWN'))
            )""")
            con.commit()
            self._validate_schema(con)
        finally: con.close()

    def _connect(self):
        ensure_private_file(self.path)
        con=sqlite3.connect(self.path,timeout=.25,isolation_level=None)
        con.execute("PRAGMA busy_timeout=250")
        return con

    def _validate_schema(self,con):
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != {"effect_attempts"}: raise EffectStateError("unexpected effect-state table set")
        cols=[r[1] for r in con.execute("PRAGMA table_info(effect_attempts)")]
        if cols != ["correlation_identity","request_fingerprint","state","acknowledgement"]:
            raise EffectStateError("malformed effect-state schema")

    def execute(self, objects: Mapping[str,Mapping[str,Any]], transport: Transport) -> TransportOutcome:
        valid=ContractBundle(objects).validate()
        if not valid.accepted: raise CourierRejected("proposal fails logical validation")
        req=dict(objects["TransferRequest"]); corr=req["correlation_identity"]; fp=_fingerprint(req)
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE"); self._validate_schema(con)
            row=con.execute("SELECT request_fingerprint,state,acknowledgement FROM effect_attempts WHERE correlation_identity=?",(corr,)).fetchone()
            if row:
                old_fp,state,ack=row
                if old_fp != fp: raise ConflictingReplay("correlation reused for different request")
                if state in UNCERTAIN or state == "IN_FLIGHT":
                    raise ReconciliationRequired(f"prior effect state requires reconciliation: {state}")
                con.execute("COMMIT")
                return TransportOutcome(state,ack)
            con.execute("INSERT INTO effect_attempts VALUES(?,?,?,NULL)",(corr,fp,"PREPARED"))
            con.execute("UPDATE effect_attempts SET state='IN_FLIGHT' WHERE correlation_identity=?",(corr,))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK"); raise
        finally: con.close()

        # External-effect boundary. Once invoked, an exception means we cannot
        # infer whether the effect happened.
        try:
            outcome=transport.effect(req)
        except Exception:
            self._set_state(corr,fp,"OUTCOME_UNKNOWN",None)
            raise ReconciliationRequired("transport raised after effect boundary; outcome unknown")

        if outcome.state == "NOT_ATTEMPTED":
            self._set_state(corr,fp,"REJECTED",None)
            return TransportOutcome("REJECTED")
        if outcome.state not in FINAL | UNCERTAIN:
            self._set_state(corr,fp,"OUTCOME_UNKNOWN",None)
            raise ReconciliationRequired("transport returned unrecognized outcome")
        self._set_state(corr,fp,outcome.state,outcome.acknowledgement)
        return outcome

    def _set_state(self,corr,fp,state,ack):
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row=con.execute("SELECT request_fingerprint FROM effect_attempts WHERE correlation_identity=?",(corr,)).fetchone()
            if row is None or row[0] != fp: raise EffectStateError("effect record identity changed")
            con.execute("UPDATE effect_attempts SET state=?,acknowledgement=? WHERE correlation_identity=?",(state,ack,corr))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK"); raise
        finally: con.close()

    def state(self,corr):
        con=self._connect()
        try:
            self._validate_schema(con)
            row=con.execute("SELECT state,acknowledgement FROM effect_attempts WHERE correlation_identity=?",(corr,)).fetchone()
            return None if row is None else TransportOutcome(*row)
        finally: con.close()

    def reconcile(self,corr, *, established_state: str, acknowledgement: str | None = None):
        if established_state not in FINAL: raise EffectStateError("reconciliation must establish TRANSFERRED or REJECTED")
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row=con.execute("SELECT state FROM effect_attempts WHERE correlation_identity=?",(corr,)).fetchone()
            if row is None: raise EffectStateError("no prior attempt to reconcile")
            if row[0] not in UNCERTAIN | {"IN_FLIGHT"}: raise EffectStateError("state does not require reconciliation")
            con.execute("UPDATE effect_attempts SET state=?,acknowledgement=? WHERE correlation_identity=?",(established_state,acknowledgement,corr))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK"); raise
        finally: con.close()
