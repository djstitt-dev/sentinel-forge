import copy
import multiprocessing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from sentinel_forge.assembly import AssemblyContext, assemble_outbound
from sentinel_forge.courier import ConflictingReplay
from sentinel_forge.courier_sqlite import DurableStateError, SQLiteDisconnectedCourier
from sentinel_forge.package import build_manifest

def _submit_worker(db, objects, queue):
    try:
        r=SQLiteDisconnectedCourier(Path(db),"courier-test").submit(objects)
        queue.put(("ok",r.replayed,r.request_fingerprint))
    except Exception as exc:
        queue.put((type(exc).__name__,str(exc)))

class SQLiteCourierTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); self.root=Path(self.td.name)
        (self.root/"x").write_bytes(b"x")
        m=build_manifest(self.root,["x"],work_package_revision="r1",
            artifact_type_class="candidate",classification_handling="controlled")
        c=AssemblyContext(work_package_id="wp",revision_id="r1",authorization_id="a1",
            authorizing_authority="operator",authorized_principal="forge",scope_reference="scope",
            target="scribe",operation="controlled-transfer",policy_reference="p1",
            classification_handling="controlled",correlation_id="c1",
            allowed_action_classes="transfer",intended_purpose_disposition="scribe-evaluation",
            expected_transfer_effect_class="controlled-copy",canonical_integrity_reference="ri1")
        self.objects=assemble_outbound(m,c).objects
        self.db=self.root/"courier.sqlite"

    def tearDown(self): self.td.cleanup()

    def courier(self): return SQLiteDisconnectedCourier(self.db,"courier-test")

    def test_persists_exact_replay_across_restart(self):
        first=self.courier().submit(self.objects)
        second=self.courier().submit(self.objects)
        self.assertFalse(first.replayed); self.assertTrue(second.replayed)
        self.assertEqual(first.receipt,second.receipt)

    def test_conflicting_replay_survives_restart_and_preserves_original(self):
        first=self.courier().submit(self.objects)
        altered=copy.deepcopy(self.objects)
        altered["TransferRequest"]["intended_purpose_disposition"]="different"
        with self.assertRaises(ConflictingReplay): self.courier().submit(altered)
        self.assertEqual(first.receipt,self.courier().lookup("c1").receipt)

    def test_authority_identity_mismatch_fails_closed(self):
        self.courier()
        with self.assertRaises(DurableStateError):
            SQLiteDisconnectedCourier(self.db,"foreign-courier")

    def test_malformed_receipt_json_fails_closed(self):
        self.courier().submit(self.objects)
        con=sqlite3.connect(self.db)
        try:
            con.execute("UPDATE courier_records SET receipt_json='not-json' WHERE correlation_identity='c1'")
            con.commit()
        finally:
            con.close()
        with self.assertRaises(DurableStateError): self.courier().lookup("c1")

    def test_impossible_transferred_state_fails_closed(self):
        self.courier().submit(self.objects)
        con=sqlite3.connect(self.db)
        try:
            raw=con.execute("SELECT receipt_json FROM courier_records").fetchone()[0]
            raw=raw.replace('"transfer_disposition":"PROPOSED"','"transfer_disposition":"TRANSFERRED"')
            con.execute("UPDATE courier_records SET receipt_json=?",(raw,))
            con.commit()
        finally:
            con.close()
        with self.assertRaises(DurableStateError): self.courier().lookup("c1")

    def test_extra_table_is_rejected(self):
        self.courier()
        con=sqlite3.connect(self.db)
        try:
            con.execute("CREATE TABLE evil(x)")
            con.commit()
        finally:
            con.close()
        with self.assertRaises(DurableStateError): self.courier().lookup("c1")

    def test_multiprocess_same_request_has_one_first_writer(self):
        q=multiprocessing.Queue()
        ps=[multiprocessing.Process(target=_submit_worker,args=(str(self.db),self.objects,q)) for _ in range(4)]
        for p in ps:p.start()
        for p in ps:p.join(5)
        results=[q.get(timeout=2) for _ in ps]
        self.assertTrue(all(x[0]=="ok" for x in results),results)
        self.assertEqual(1,sum(1 for x in results if x[1] is False),results)
        self.assertEqual(3,sum(1 for x in results if x[1] is True),results)
        self.assertEqual(1,len({x[2] for x in results}))

    def test_multiprocess_conflicting_requests_have_single_semantic_winner(self):
        altered=copy.deepcopy(self.objects)
        altered["TransferRequest"]["intended_purpose_disposition"]="different"
        q=multiprocessing.Queue()
        ps=[
            multiprocessing.Process(target=_submit_worker,args=(str(self.db),self.objects,q)),
            multiprocessing.Process(target=_submit_worker,args=(str(self.db),altered,q)),
        ]
        for p in ps:p.start()
        for p in ps:p.join(5)
        results=[q.get(timeout=2) for _ in ps]
        self.assertEqual(1,sum(1 for x in results if x[0]=="ok"),results)
        self.assertEqual(1,sum(1 for x in results if x[0]=="ConflictingReplay"),results)

if __name__=="__main__": unittest.main()
