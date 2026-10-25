import json,hashlib
def load_kev(path):
 raw=__import__("pathlib").Path(path).read_bytes();doc=json.loads(raw);ids=set()
 for x in doc.get("vulnerabilities",[]):
  c=x.get("cveID")
  if isinstance(c,str):ids.add(c)
 return frozenset(ids),"sha256:"+hashlib.sha256(raw).hexdigest()
