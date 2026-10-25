"""Offline Courier acceptance runner. No host/network effects."""
from __future__ import annotations
import argparse,subprocess,sys
from .courier_acceptance import REQUIRED_OFFLINE,assess_courier_acceptance

INVARIANT_TESTS={
 "PAIRWISE_ISOLATION":("tests.test_wp624_pairwise_trust_domain","tests.test_wp648_fleet_transport_isolation"),
 "DURABLE_SEQUENCE":("tests.test_wp646_send_sequence","tests.test_wp697_sequence_reservation_recovery"),
 "CURRENT_CREDENTIAL_SESSION":("tests.test_wp630_credential_registry","tests.test_wp631_transport_contract"),
 "QUEUE_STATE_MACHINE":("tests.test_wp638_courier_queue","tests.test_wp679_state_space"),
 "ACK_BINDING":("tests.test_wp640_courier_ack",),
 "ANTI_REPLAY":("tests.test_wp626_session_antireplay","tests.test_wp641_courier_receive"),
 "UNKNOWN_EFFECT_RECONCILIATION":("tests.test_wp642_wp643_reconcile_limits","tests.test_wp680_crash_points"),
 "LAST_MOMENT_AUTHORITY":("tests.test_wp657_wp661_pre_effect_gate",),
 "REVOCATION_KILL":("tests.test_wp657_wp661_pre_effect_gate",),
 "TARGET_CLASSIFICATION_BINDING":("tests.test_wp657_wp661_pre_effect_gate",),
 "DELIVERY_HISTORY":("tests.test_wp649_wp650_delivery_journal",),
 "STAGING_QUARANTINE":("tests.test_wp652_wp654_artifact_store",),
 "DURABLE_FAILURE_FAIL_CLOSED":("tests.test_wp663_durable_write_failures",),
}
def run_invariant_checks()->dict[str,bool]:
 out={}
 for name in REQUIRED_OFFLINE:
  tests=INVARIANT_TESTS[name]
  p=subprocess.run([sys.executable,"-m","unittest",*tests],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
  out[name]=p.returncode==0
 return out
def build_report(*,checks=None,tests_passed=None,framing_complete=False,protection_provider_complete=False,
                 production_protection_approved=False,production_network_approved=False,assistant_independence_verified=False):
 if checks is None:checks={x:bool(tests_passed) for x in REQUIRED_OFFLINE}
 return assess_courier_acceptance(checks=checks,framing_complete=framing_complete,
  protection_provider_complete=protection_provider_complete,production_protection_approved=production_protection_approved,
  production_network_approved=production_network_approved,assistant_independence_verified=assistant_independence_verified)
def main(argv=None):
 argparse.ArgumentParser().parse_args(argv);r=build_report(checks=run_invariant_checks());print(r.to_json(),end="")
 return 0 if r.offline_invariants_passed else 1
if __name__=="__main__":raise SystemExit(main())
