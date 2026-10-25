"""Bounded evaluator for Canonical Ubuntu USN OVAL dpkg package tests."""
from __future__ import annotations
import bz2,hashlib,xml.etree.ElementTree as ET
from .vulnerability_intelligence import AdvisoryRecord,package_inventory,assess

def parse_ubuntu_usn_oval(path,release="resolute",kev_ids=frozenset()):
 raw=__import__("pathlib").Path(path).read_bytes();digest="sha256:"+hashlib.sha256(raw).hexdigest()
 xml=bz2.decompress(raw) if str(path).endswith(".bz2") else raw
 root=ET.fromstring(xml)
 byid={e.attrib.get("id"):e for e in root.iter() if e.attrib.get("id")}
 records=[]
 for definition in root.iter():
  if not definition.tag.endswith("definition") or definition.attrib.get("class")!="patch":continue
  metadata=next((x for x in definition if x.tag.endswith("metadata")),None)
  if metadata is None:continue
  cves=[];severity=None
  for x in metadata.iter():
   if x.tag.endswith("reference") and x.attrib.get("source")=="CVE":cves.append(x.attrib.get("ref_id"))
   if x.tag.endswith("severity") and x.text:severity=x.text.strip().lower()
  testrefs=[]
  for x in definition.iter():
   if x.tag.endswith("criterion") and x.attrib.get("test_ref"):testrefs.append(x.attrib["test_ref"])
  for tref in testrefs:
   test=byid.get(tref)
   if test is None or not test.tag.endswith("dpkginfo_test"):continue
   objref=stateref=None
   for x in test:
    if x.tag.endswith("object"):objref=x.attrib.get("object_ref")
    if x.tag.endswith("state"):stateref=x.attrib.get("state_ref")
   obj=byid.get(objref);state=byid.get(stateref)
   if obj is None or state is None:continue
   varref=None
   for x in obj:
    if x.tag.endswith("name"):varref=x.attrib.get("var_ref")
   var=byid.get(varref)
   packages=[(x.text or "").strip() for x in var] if var is not None else []
   fixed=None
   for x in state:
    if x.tag.endswith("evr") and x.attrib.get("operation")=="less than":fixed=(x.text or "").strip()
   if not fixed:continue
   for cve in cves:
    if not cve:continue
    for pkg in packages:
     if pkg:records.append(AdvisoryRecord(cve,pkg,release,fixed,severity,"ubuntu-oval",digest,cve in kev_ids))
 return records

def evaluate_ubuntu_usn_oval(path,release="resolute",kev_ids=frozenset()):
 inv=package_inventory();records=parse_ubuntu_usn_oval(path,release,kev_ids)
 return [assess(r,inv) for r in records]
