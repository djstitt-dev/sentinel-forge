"""OpenSSH bootstrap command builder. Construction is safe; execution requires explicit caller authority."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class SshBootstrapPlan:
 child_identity:str;host:str;user:str;port:int;known_hosts:str;remote_staging:str;copy_argv:tuple[str,...];install_argv:tuple[str,...]

def build_ssh_bootstrap_plan(*,child_identity,host,user,port,known_hosts,local_artifact,remote_staging="/tmp/sentinel-courier-enrollment.tgz"):
 for x in (child_identity,host,user,known_hosts,local_artifact,remote_staging):
  if not isinstance(x,str) or not x.strip():raise EnrollmentError("SSH bootstrap field required")
 if type(port) is not int or not 1<=port<=65535:raise EnrollmentError("SSH port invalid")
 if not Path(local_artifact).is_absolute():raise EnrollmentError("local artifact path must be absolute")
 if not remote_staging.startswith("/"):raise EnrollmentError("remote staging path must be absolute")
 base=("-p",str(port),"-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o",f"UserKnownHostsFile={known_hosts}")
 target=f"{user}@{host}"
 copy=("scp",*base,local_artifact,f"{target}:{remote_staging}")
 sshbase=("-p",str(port),"-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o",f"UserKnownHostsFile={known_hosts}")
 install=("ssh",*sshbase,target,"sentinel-courier-enroll","--artifact",remote_staging,"--noninteractive")
 return SshBootstrapPlan(child_identity,host,user,port,known_hosts,remote_staging,copy,install)
