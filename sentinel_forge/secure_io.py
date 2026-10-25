"""Owner-only file creation primitives for Forge durable security state."""
from __future__ import annotations
import os
from pathlib import Path

def private_open(path, mode, *, encoding=None):
    path=Path(path)
    flags=getattr(os,"O_NOFOLLOW",0)
    if "r" in mode and all(x not in mode for x in "wax+"):
        flags|=os.O_RDONLY
    else:
        flags|=os.O_WRONLY|os.O_CREAT
        if "x" in mode: flags|=os.O_EXCL
        elif "a" in mode: flags|=os.O_APPEND
        else: flags|=os.O_TRUNC
    fd=os.open(path,flags,0o600)
    try:
        os.fchmod(fd,0o600)
        return os.fdopen(fd,mode,encoding=encoding)
    except BaseException:
        os.close(fd);raise

def ensure_private_file(path):
    path=Path(path)
    fd=os.open(path,os.O_RDWR|os.O_CREAT|getattr(os,"O_NOFOLLOW",0),0o600)
    try: os.fchmod(fd,0o600)
    finally: os.close(fd)
