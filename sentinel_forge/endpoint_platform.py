"""Supported endpoint platform profiles for Forge enrollment package generation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .enrollment import EnrollmentError

class PlatformFamily(str,Enum):
 WINDOWS_10="windows-10"
 WINDOWS_11="windows-11"
 UBUNTU_DESKTOP="ubuntu-desktop"
 UBUNTU_SERVER="ubuntu-server"
 DEBIAN_WORKSTATION="debian-workstation"
 DEBIAN_SERVER="debian-server"

@dataclass(frozen=True)
class PlatformProfile:
 family:PlatformFamily;version:str;architecture:str;package_manager:str;service_manager:str
 shell:str;state_root:str;config_root:str;credential_store:str;script_name:str

def build_platform_profile(family:PlatformFamily,*,version="auto",architecture="auto"):
 if not isinstance(family,PlatformFamily):raise EnrollmentError("supported platform family required")
 if not isinstance(version,str) or not version.strip():raise EnrollmentError("platform version required")
 if not isinstance(architecture,str) or not architecture.strip():raise EnrollmentError("architecture required")
 if family in {PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11}:
  return PlatformProfile(family,version,architecture,"Windows provider discovery","Windows Service Control Manager",
   "PowerShell",r"%ProgramData%\Sentinel\Courier",r"%ProgramData%\Sentinel\Courier\config",
   "Windows protected credential boundary","Enroll-SentinelCourier.ps1")
 distro="Ubuntu" if family in {PlatformFamily.UBUNTU_DESKTOP,PlatformFamily.UBUNTU_SERVER} else "Debian"
 return PlatformProfile(family,version,architecture,"apt/dpkg","systemd","POSIX sh",
  "/var/lib/sentinel-courier","/etc/sentinel-courier",f"{distro} root-readable credential boundary","enroll-sentinel-courier.sh")
