import unittest
from pathlib import Path
from sentinel_forge.cisa_kev import load_kev
from sentinel_forge.ubuntu_oval import parse_ubuntu_usn_oval,evaluate_ubuntu_usn_oval
ROOT=Path(__file__).resolve().parents[1]
OVAL=ROOT/"evidence/vulnerability-intelligence/feeds/com.ubuntu.resolute.usn.oval.xml.bz2"
KEV=ROOT/"evidence/vulnerability-intelligence/feeds/cisa-kev.json"
class UbuntuOvalTests(unittest.TestCase):
 def test_feed_parses_many_records(self):
  self.assertGreater(len(parse_ubuntu_usn_oval(OVAL)),1000)
 def test_live_assessment_finds_fixed_records(self):
  kev,_=load_kev(KEV);items=evaluate_ubuntu_usn_oval(OVAL,kev_ids=kev)
  self.assertTrue(any(x.state.value=="fixed" for x in items))
 def test_kev_never_overrides_state(self):
  records=parse_ubuntu_usn_oval(OVAL,kev_ids=frozenset({"CVE-2026-9277"}))
  x=next(r for r in records if r.cve_id=="CVE-2026-9277" and r.package=="node-shell-quote")
  self.assertTrue(x.known_exploited)
