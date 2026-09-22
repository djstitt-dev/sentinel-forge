#!/usr/bin/env python3
"""Operator-run read-only WP4B preflight; importing this module performs no I/O.

Run only in explicitly established FORGE PRIVILEGED HOST CONTEXT. No writer or
AIDE invocation occurs. No-atime failures stop without a less-safe fallback.
Repository identity uses approved ancestry, an attached branch, a clean index and
working tree, and exact HEAD blobs for this file and the approved writer. No
self-referential commit ID is needed. This preparation does not authorize execution.
"""
import hashlib
import json
import os
import pwd
import shlex
import stat
import subprocess
import sys
from contextlib import ExitStack
from datetime import datetime, timezone

REPO = "/home/forgeadmin/Project-Sentinel-Forge"
APPROVED_ANCESTOR = "26a1dca85931d2bcb861b168cc3a328216b8a83e"
PREFLIGHT_REL = "scripts/verify/preflight_f117k42.py"
WRITER_REL = "scripts/changes/close_f117k42.py"
PREFLIGHT = REPO + "/" + PREFLIGHT_REL
WRITER = REPO + "/scripts/changes/close_f117k42.py"
WRITER_HASH = "23c40f541e9d23c88c29118d16e517af689bcf44bd1f5839b402ac4d0d9356a9"
TRUSTED = "/var/lib/aide/aide.db"
CANDIDATE = "/var/lib/aide/aide.db.new"
POLICY = "/etc/aide/aide.conf.d/90_sentinel_forge_local"
K41 = "/var/lib/aide/trusted-history/f117k41-final-post-promotion-verification.txt"
TARGET = "/var/lib/aide/trusted-history/f117k42-evidence-closure.txt"
HOSTNAME = "sentinel-forge"
MACHINE_ID = "c1c620cdbd8b4c4fbdd827ed2d769b4f"
OS_IDENTITY = {
    "ID": "ubuntu", "VERSION_ID": "26.04", "VERSION_CODENAME": "resolute",
    "PRETTY_NAME": "Ubuntu 26.04.1 LTS",
}
KERNEL = "7.0.0-31-generic"
ARCHITECTURE = "x86_64"
VIRTUALIZATION = "oracle"
INTERFACE = "enp0s8"
IPV4 = "192.168.56.104"
PREFIXLEN = 24
EXPECTED = {
    TRUSTED: "3c63b0d1bca62c4cc0472239962fbeef84979842207cee5bbd9ebcd22f39b18f",
    POLICY: "72e121a5151844906acdfb2b12a7201d4a9ec382fc7db39b7317e064f14a4407",
    K41: "32ba78267a8a980b6c2067ba98038446e807acad1b1d748241ba0ebe3646b05f",
}
ENV = {
    "PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C",
    "GIT_OPTIONAL_LOCKS": "0", "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_NO_LAZY_FETCH": "1",
}
GIT = [
    "/usr/bin/git", "--no-optional-locks", "--no-replace-objects",
    "-c", "safe.directory=" + REPO,
    "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "-C", REPO,
]


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def run(*args, binary=False):
    result = subprocess.run(args, env=ENV, text=not binary, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {args!r}\n"
                           + repr(result.stdout) + repr(result.stderr))
    return result.stdout if binary else result.stdout.strip()


def metadata(path, s):
    print(f"METADATA {path}: type={stat.filemode(s.st_mode)[0]} "
          f"uid={s.st_uid} gid={s.st_gid} mode={stat.S_IMODE(s.st_mode):04o} "
          f"links={s.st_nlink} device={s.st_dev} inode={s.st_ino} size={s.st_size}",
          flush=True)


def fingerprint(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid,
            s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def directory_identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink)


def sha256(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    h = hashlib.sha256()
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return h.hexdigest()
        h.update(chunk)


def no_aide_process():
    rows = run("/usr/bin/ps", "-e", "-o", "pid=", "-o", "comm=")
    matches = []
    for row in rows.splitlines():
        fields = row.strip().split(None, 1)
        if len(fields) == 2 and fields[1].lower().startswith("aide"):
            matches.append(row.strip())
    if matches:
        print("Possible AIDE processes:\n" + "\n".join(matches), flush=True)
    require(not matches, "Obvious AIDE process detected; preserve state and STOP")
    print("PASS: no obvious AIDE process by process name", flush=True)


def descriptor_bytes(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def verify_repository(preflight_entry, writer_entry, initial=None):
    require(os.path.abspath(__file__) == PREFLIGHT,
            "Preflight must execute from its tracked repository pathname")
    require(run(*(GIT + ["rev-parse", "--show-toplevel"])) == REPO,
            "Unexpected repository root")
    branch = run(*(GIT + ["symbolic-ref", "--quiet", "HEAD"]))
    require(branch.startswith("refs/heads/"), "Attached local branch required")
    head = run(*(GIT + ["rev-parse", "--verify", "HEAD^{commit}"]))
    print("Repository HEAD:", head)
    require(head != APPROVED_ANCESTOR, "Committed preflight descendant required")
    run(*(GIT + ["merge-base", "--is-ancestor", APPROVED_ANCESTOR, head]))
    if initial is not None:
        require((branch, head) == initial, "Repository branch/HEAD changed during inspection")
    # Do not let index flags conceal working-tree changes from status/diff.
    entries = run(*(GIT + ["ls-files", "-v", "-z"]))
    require(all(row.startswith("H ") for row in entries.split("\0") if row),
            "Unexpected index flags (including skip-worktree/assume-unchanged)")
    status = run(*(GIT + ["status", "--porcelain=v1", "--untracked-files=all",
                         "--ignore-submodules=none"]))
    if status:
        print(status, flush=True)
    require(not status, "Repository working tree is not clean")
    run(*(GIT + ["diff-index", "--cached", "--quiet", head, "--"]))
    run(*(GIT + ["diff-files", "--quiet", "--"]))
    for relative, path, entry in ((PREFLIGHT_REL, PREFLIGHT, preflight_entry),
                                  (WRITER_REL, WRITER, writer_entry)):
        require(run(*(GIT + ["ls-files", "--error-unmatch", "--", relative])) == relative,
                "Required package file is not tracked: " + relative)
        blob = run(*(GIT + ["cat-file", "blob", head + ":" + relative]), binary=True)
        actual = descriptor_bytes(entry[0])
        require(blob == actual, "HEAD blob differs from inspected bytes: " + relative)
        if relative == WRITER_REL:
            require(hashlib.sha256(actual).hexdigest() == WRITER_HASH,
                    "Approved writer SHA256 mismatch")
        verify_unchanged(path, entry)
    require(run(*(GIT + ["symbolic-ref", "--quiet", "HEAD"])) == branch
            and run(*(GIT + ["rev-parse", "--verify", "HEAD^{commit}"])) == head,
            "Repository changed during identity validation")
    print("PASS: attached descendant; clean index/tree; tracked package bytes match HEAD")
    return branch, head


class Inspection:
    """Pinned read-only descriptors; metadata rules match reviewed preflight."""

    def __init__(self, stack):
        self.stack = stack
        self.flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NOATIME
        self.root = os.open("/", self.flags)
        stack.callback(os.close, self.root)
        self.directories = {}
        self.operator = pwd.getpwnam("forgeadmin")

    def check_directory(self, path, fd, repository=False):
        s = os.fstat(fd)
        require(stat.S_ISDIR(s.st_mode), "Not a directory: " + path)
        if repository:
            require(s.st_uid in (0, self.operator.pw_uid),
                    "Unexpected repository ancestor owner: " + path)
            # Repository group-writable paths are permitted only for root or the
            # forgeadmin group; world-writable paths remain refused.
            require(not (s.st_mode & 0o002),
                    "World-writable repository ancestor: " + path)
            require(not (s.st_mode & 0o020)
                    or s.st_gid in (0, self.operator.pw_gid),
                    "Unexpected writable repository ancestor group: " + path)
        else:
            require(s.st_uid == 0 and not (s.st_mode & 0o022),
                    "Unsafe host ancestor ownership/mode: " + path)
        key = (path, repository)
        if key not in self.directories:
            metadata(path, s)
            self.directories[key] = (fd, directory_identity(s))
        else:
            require(directory_identity(s) == self.directories[key][1],
                    "Directory changed: " + path)

    def open_directory(self, path, repository=False):
        require(path.startswith("/"), "Absolute directory path required")
        self.check_directory("/", self.root, repository)
        fd, current = self.root, ""
        for part in path.strip("/").split("/"):
            if not part and path == "/":
                break
            require(part not in ("", ".", ".."), "Unsafe directory component")
            current += "/" + part
            fd = os.open(part, self.flags, dir_fd=fd)
            self.stack.callback(os.close, fd)
            self.check_directory(current, fd, repository)
        return fd

    def open_regular(self, path, repository=False):
        parent = self.open_directory(os.path.dirname(path), repository)
        name = os.path.basename(path)
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        metadata(path, before)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                "Source must be a singly-linked regular file: " + path)
        owners = (0, self.operator.pw_uid) if repository else (0,)
        require(before.st_uid in owners,
                "Unexpected source owner; root required for AIDE evidence: " + path)
        if repository:
            require(not (before.st_mode & 0o002),
                    "World-writable repository source refused: " + path)
            require(not (before.st_mode & 0o020)
                    or before.st_gid in (0, self.operator.pw_gid),
                    "Unexpected repository source group: " + path)
        else:
            require(not (before.st_mode & 0o022),
                    "Group/world-writable source refused: " + path)
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW |
                     os.O_NONBLOCK | os.O_NOATIME, dir_fd=parent)
        self.stack.callback(os.close, fd)
        require(fingerprint(os.fstat(fd)) == fingerprint(before),
                "Source changed while opening: " + path)
        return fd, parent, name, fingerprint(before)

    def read_identity(self, path):
        entry = self.open_regular(path)
        data = b""
        while True:
            block = os.read(entry[0], 4096)
            if not block:
                break
            data += block
            require(len(data) <= 65536, "Unexpectedly large identity file")
        verify_unchanged(path, entry)
        return data.decode()

    def verify_directories(self):
        for (path, repository), (fd, identity) in list(self.directories.items()):
            require(directory_identity(os.fstat(fd)) == identity,
                    "Pinned directory changed: " + path)
            reopened = self.open_directory(path, repository)
            require(directory_identity(os.fstat(reopened)) == identity,
                    "Reachable directory identity changed: " + path)


def verify_unchanged(path, entry):
    fd, parent, name, before = entry
    require(fingerprint(os.fstat(fd)) == before
            and fingerprint(os.stat(name, dir_fd=parent,
                                    follow_symlinks=False)) == before,
            "Source identity/metadata changed: " + path)


def target_absent(parent):
    try:
        s = os.stat(os.path.basename(TARGET), dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        print("PASS: K42 target absent, including no dangling symlink")
        return
    metadata(TARGET, s)
    raise RuntimeError("K42 target exists; preserve it and STOP")


def preflight():
    require(os.geteuid() == 0, "Effective UID must be 0")
    print("Context: FORGE PRIVILEGED HOST CONTEXT — operator-established")
    print("UTC:", datetime.now(timezone.utc).isoformat())
    print("EUID:", os.geteuid())
    print("Python:", sys.version.replace("\n", " "))
    require(sys.version_info.major == 3, "Python 3 required")
    hostname = run("/usr/bin/hostname")
    print("Hostname:", hostname)
    require(hostname == HOSTNAME, "Hostname mismatch")
    with ExitStack() as stack:
        view = Inspection(stack)
        machine_id = view.read_identity("/etc/machine-id").strip()
        print("Machine ID:", machine_id)
        require(machine_id == MACHINE_ID, "Machine ID mismatch")
        # Resolve only the conventional OS identity alias before safe traversal.
        os_path = os.path.realpath("/etc/os-release", strict=True)
        print("OS identity resolved path:", os_path)
        release = {}
        for line in view.read_identity(os_path).splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                require(key not in release, "Duplicate OS identity key: " + key)
                release[key] = " ".join(shlex.split(value))
        for key, value in OS_IDENTITY.items():
            print(f"OS {key}={release.get(key)!r}")
            require(release.get(key) == value, "OS identity mismatch: " + key)
        uts = os.uname()
        print("Kernel:", uts.release)
        print("Architecture:", uts.machine)
        require(uts.release == KERNEL, "Kernel mismatch")
        require(uts.machine == ARCHITECTURE, "Architecture mismatch")
        virtualization = run("/usr/bin/systemd-detect-virt")
        print("Virtualization:", virtualization)
        require(virtualization == VIRTUALIZATION, "Virtualization mismatch")
        addresses = json.loads(run("ip", "-j", "-4", "address", "show", "dev", INTERFACE))
        require(any(
            interface.get("ifname") == INTERFACE
            and any(a.get("family") == "inet" and a.get("local") == IPV4
                    and a.get("prefixlen") == PREFIXLEN
                    for a in interface.get("addr_info", []))
            for interface in addresses
        ), "Expected enp0s8 IPv4/prefix missing")
        print("PASS: enp0s8 contains 192.168.56.104/24")
        preflight_entry = view.open_regular(PREFLIGHT, repository=True)
        writer = view.open_regular(WRITER, repository=True)
        writer_hash = sha256(writer[0])
        print("Writer SHA256:", writer_hash)
        require(writer_hash == WRITER_HASH, "Writer SHA256 mismatch")
        verify_unchanged(WRITER, writer)
        repository_identity = verify_repository(preflight_entry, writer)
        no_aide_process()
        parent = view.open_directory(os.path.dirname(TARGET))
        target_absent(parent)
        # All metadata is checked before evidence hashing. A non-root candidate
        # stops after its exact numeric metadata is printed, before opening it.
        sources = {path: view.open_regular(path)
                   for path in (TRUSTED, CANDIDATE, POLICY, K41)}
        for path, entry in sources.items():
            value = sha256(entry[0])
            print("SHA256", path, value, flush=True)
            if path in EXPECTED:
                require(value == EXPECTED[path], "Anchor SHA256 mismatch: " + path)
            verify_unchanged(path, entry)
        left, right = sources[TRUSTED][0], sources[CANDIDATE][0]
        os.lseek(left, 0, os.SEEK_SET)
        os.lseek(right, 0, os.SEEK_SET)
        while True:
            a, b = os.read(left, 1024 * 1024), os.read(right, 1024 * 1024)
            require(a == b, "Trusted/candidate byte mismatch")
            if not a:
                break
        print("PASS: trusted and candidate databases are byte-identical")
        verify_repository(preflight_entry, writer, repository_identity)
        require(sha256(writer[0]) == WRITER_HASH, "Writer hash changed")
        verify_unchanged(WRITER, writer)
        for path, entry in sources.items():
            verify_unchanged(path, entry)
        view.verify_directories()
        target_absent(parent)
        no_aide_process()
        for path, entry in sources.items():
            verify_unchanged(path, entry)
        verify_unchanged(WRITER, writer)
        verify_unchanged(PREFLIGHT, preflight_entry)
    print("PREFLIGHT PASS — K42 writer was NOT executed; no record was created.")
    print("Return the complete output for operator review before proceeding.")


def main():
    try:
        preflight()
        return 0
    except BaseException as exc:
        print("PREFLIGHT STOP:", type(exc).__name__, str(exc), file=sys.stderr, flush=True)
        print("Preserve all state. Do not repair, change ownership, or execute K42.",
              file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
