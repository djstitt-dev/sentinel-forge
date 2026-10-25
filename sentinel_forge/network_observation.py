"""Bounded read-only networking observations for Sentinel Forge."""
from __future__ import annotations
from datetime import datetime, timezone
import json, subprocess
from pathlib import Path
from .enrollment import EnrollmentError

IP="/usr/sbin/ip"
SS="/usr/bin/ss"
RESOLVECTL="/usr/bin/resolvectl"

def _run_json(argv, runner=subprocess.run):
    try:
        r=runner(tuple(argv),capture_output=True,text=True,timeout=10,check=False,shell=False)
    except (OSError,subprocess.SubprocessError) as exc:
        raise EnrollmentError("network observation unavailable") from exc
    if r.returncode != 0:
        raise EnrollmentError("network observation command failed")
    try:
        data=json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        raise EnrollmentError("network observation invalid JSON") from exc
    return data

def observe_routes():
    rows=_run_json((IP,"-j","route","show"))
    if not isinstance(rows,list): raise EnrollmentError("route observation invalid")
    routes=[]; defaults=[]
    for row in rows:
        if not isinstance(row,dict): raise EnrollmentError("route record invalid")
        rec={k:row.get(k) for k in ("dst","gateway","dev","protocol","scope","prefsrc","metric")}
        routes.append(rec)
        if row.get("dst")=="default":
            defaults.append(rec)
    return {"collected_at_utc":datetime.now(timezone.utc).isoformat(),"routes":routes,"default_routes":defaults}

def observe_neighbors():
    rows=_run_json((IP,"-j","neigh","show"))
    if not isinstance(rows,list): raise EnrollmentError("neighbor observation invalid")
    out=[]
    for row in rows:
        if not isinstance(row,dict): raise EnrollmentError("neighbor record invalid")
        out.append({
            "destination":row.get("dst"),"interface":row.get("dev"),
            "link_layer_address":row.get("lladdr"),"state":row.get("state",[]),
        })
    return {"collected_at_utc":datetime.now(timezone.utc).isoformat(),"neighbors":out}

def observe_listeners(runner=subprocess.run):
    argv=(SS,"-H","-lntu")
    try:
        r=runner(argv,capture_output=True,text=True,timeout=10,check=False,shell=False)
    except (OSError,subprocess.SubprocessError) as exc:
        raise EnrollmentError("listener observation unavailable") from exc
    if r.returncode != 0: raise EnrollmentError("listener observation failed")
    listeners=[]
    for line in r.stdout.splitlines():
        parts=line.split()
        if len(parts) < 5: continue
        proto=parts[0]; local=parts[4]
        listeners.append({"protocol":proto,"local":local})
    return {"collected_at_utc":datetime.now(timezone.utc).isoformat(),"listeners":listeners}

def observe_dns(runner=subprocess.run):
    argv=(RESOLVECTL,"dns")
    try:
        r=runner(argv,capture_output=True,text=True,timeout=10,check=False,shell=False)
    except (OSError,subprocess.SubprocessError) as exc:
        raise EnrollmentError("DNS observation unavailable") from exc
    if r.returncode != 0: raise EnrollmentError("DNS observation failed")
    return {
        "collected_at_utc":datetime.now(timezone.utc).isoformat(),
        "resolvectl_dns":r.stdout.strip().splitlines(),
        "resolv_conf":Path("/etc/resolv.conf").read_text(errors="replace").splitlines(),
    }

def observe_interface_stats():
    rows=_run_json((IP,"-s","-j","link","show"))
    if not isinstance(rows,list): raise EnrollmentError("link statistics invalid")
    out=[]
    for row in rows:
        if not isinstance(row,dict): continue
        out.append({
            "name":row.get("ifname"),"state":row.get("operstate"),"mtu":row.get("mtu"),
            "stats64":row.get("stats64") or row.get("stats"),
        })
    return {"collected_at_utc":datetime.now(timezone.utc).isoformat(),"interfaces":out}

def network_health():
    from .network_interfaces import collect_network_interfaces
    return {
        "collected_at_utc":datetime.now(timezone.utc).isoformat(),
        "interfaces":collect_network_interfaces(),
        "routes":observe_routes(),
        "dns":observe_dns(),
        "neighbors":observe_neighbors(),
        "listeners":observe_listeners(),
        "link_statistics":observe_interface_stats(),
        "observation":{
            "read_only":True,"network_probe_performed":False,
            "configuration_changed":False,"arbitrary_shell_input_accepted":False,
        },
    }

def as_json(value): return json.dumps(value,sort_keys=True)
