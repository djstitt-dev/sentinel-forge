"""Explicitly authorized OpenSSH bootstrap execution adapter."""
from __future__ import annotations
from dataclasses import dataclass
import subprocess
from .enrollment import EnrollmentError
from .ssh_bootstrap import SshBootstrapPlan

@dataclass(frozen=True)
class BootstrapExecution:
 copied:bool;installed:bool;copy_returncode:int;install_returncode:int

def execute_bootstrap(plan:SshBootstrapPlan,*,operator_approved:bool,timeout_seconds:int=120,runner=subprocess.run):
 if not isinstance(plan,SshBootstrapPlan):raise EnrollmentError("SSH bootstrap plan required")
 if operator_approved is not True:raise EnrollmentError("SSH bootstrap execution requires explicit operator approval")
 if type(timeout_seconds) is not int or not 1<=timeout_seconds<=900:raise EnrollmentError("SSH bootstrap timeout invalid")
 def go(argv):
  try:return runner(argv,capture_output=True,text=True,timeout=timeout_seconds,check=False,shell=False)
  except (OSError,subprocess.SubprocessError) as e:raise EnrollmentError("SSH bootstrap execution failed") from e
 a=go(plan.copy_argv)
 if a.returncode!=0:return BootstrapExecution(False,False,a.returncode,-1)
 b=go(plan.install_argv)
 return BootstrapExecution(True,b.returncode==0,a.returncode,b.returncode)
