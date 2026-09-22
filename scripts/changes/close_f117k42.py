#!/usr/bin/env python3
"""Proposed K42 writer. No host access unless --execute-host is explicit."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import os
import stat
import sys

TRUSTED = '/var/lib/aide/aide.db'
CANDIDATE = '/var/lib/aide/aide.db.new'
POLICY = '/etc/aide/aide.conf.d/90_sentinel_forge_local'
K41 = '/var/lib/aide/trusted-history/f117k41-final-post-promotion-verification.txt'
TARGET = '/var/lib/aide/trusted-history/f117k42-evidence-closure.txt'
EXPECTED = {
    'trusted': '3c63b0d1bca62c4cc0472239962fbeef84979842207cee5bbd9ebcd22f39b18f',
    'policy': '72e121a5151844906acdfb2b12a7201d4a9ec382fc7db39b7317e064f14a4407',
    'k41': '32ba78267a8a980b6c2067ba98038446e807acad1b1d748241ba0ebe3646b05f',
}
LABELS = {'trusted': TRUSTED, 'candidate': CANDIDATE, 'policy': POLICY, 'k41': K41}
CONTEXT = 'FORGE PRIVILEGED HOST CONTEXT'


class Refusal(RuntimeError):
    """No success claim; preserve any file already created."""


def fingerprint(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def secure_directory(path, stack):
    """Pin root-owned, non-writable-by-others directory chain; reject symlinks."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NOATIME
    fd = os.open('/', flags)
    stack.callback(os.close, fd)
    root_stat = os.fstat(fd)
    if root_stat.st_uid != 0 or root_stat.st_mode & 0o022:
        raise Refusal('Unsafe filesystem root ownership/mode')
    for component in path.strip('/').split('/'):
        if not component or component in ('.', '..'):
            raise Refusal('Invalid directory path')
        fd = os.open(component, flags, dir_fd=fd)
        stack.callback(os.close, fd)
        s = os.fstat(fd)
        if s.st_uid != 0 or s.st_mode & 0o022:
            raise Refusal('Directory ownership/mode unsafe: ' + path)
    return fd


def digest(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    h = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024):
        h.update(chunk)
    return h.hexdigest()


def identical(left, right):
    os.lseek(left, 0, os.SEEK_SET)
    os.lseek(right, 0, os.SEEK_SET)
    while True:
        a, b = os.read(left, 1024 * 1024), os.read(right, 1024 * 1024)
        if a != b:
            return False
        if not a:
            return True


def render(hashes, timestamp, context):
    lines = [
        'F1.17K42 evidence closure',
        'Execution context: ' + context,
        'Execution UTC: ' + timestamp,
        'Expected anchor provenance: operator-verified F1.17 host evidence.',
        'Original operator collection times and privilege context were not supplied.',
        'Verification method: SHA256 of pinned regular files and byte comparison.',
        'The hashes below were validated by this procedure at execution time.',
    ]
    lines += [f'SHA256 {LABELS[key]}: {hashes[key]}' for key in LABELS]
    lines += [
        'Trusted and candidate databases are byte-identical at closure validation.',
        'Temporal boundary: this closes the previously validated F1.17 evidence chain.',
        'Software and filesystem changes occurred after K41, including Codex setup',
        'and supporting packages/files. These are outside F1.17 acceptance state.',
        'No current live AIDE-clean assertion is being made.',
        'No new live AIDE integrity check was performed by this procedure.',
        'This is not a new baseline, candidate promotion, or authorization to alter',
        'aide.db or aide.db.new or normalize post-K41 filesystem changes.',
        'Candidate lifecycle remains deferred.',
        'This record does not attest its own post-write verification; successful',
        'post-write ownership, mode, and SHA256 verification is reported to stdout.',
    ]
    return ('\n'.join(lines) + '\n').encode('utf-8')


def write_record(sources, destination, expected, *, owner, context, clock):
    """Shared engine: callers supply pinned directory FDs; no implicit host paths.

    Tests use synthetic files and the current user's ownership. The host CLI
    alone supplies fixed host paths, root ownership, and the production anchors.
    """
    parent, name = destination
    created = False
    try:
        # lexists semantics, including dangling symlinks; exclusive open below
        # also protects against another creator after this preflight.
        try:
            os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise Refusal('K42 target already exists; preserve and review it')
        with ExitStack() as stack:
            fds, snapshots = {}, {}
            for key, (directory, basename) in sources.items():
                fd = os.open(basename, os.O_RDONLY | os.O_NOFOLLOW |
                             os.O_NONBLOCK | os.O_NOATIME, dir_fd=directory)
                stack.callback(os.close, fd)
                s = os.fstat(fd)
                if (not stat.S_ISREG(s.st_mode) or s.st_uid != owner[0]
                        or s.st_mode & 0o022 or s.st_nlink != 1):
                    raise Refusal('Unsafe source file: ' + key)
                fds[key], snapshots[key] = fd, fingerprint(s)

            def validate():
                hashes = {key: digest(fd) for key, fd in fds.items()}
                for key, value in expected.items():
                    if hashes[key] != value:
                        raise Refusal('Anchor SHA256 mismatch: ' + key)
                if not identical(fds['trusted'], fds['candidate']):
                    raise Refusal('Trusted/candidate byte mismatch')
                for key, fd in fds.items():
                    directory, basename = sources[key]
                    if (fingerprint(os.fstat(fd)) != snapshots[key] or
                            fingerprint(os.stat(basename, dir_fd=directory,
                                                follow_symlinks=False)) != snapshots[key]):
                        raise Refusal('Source changed during validation: ' + key)
                return hashes

            hashes = validate()
            payload = render(hashes, clock(), context)
            # A second read detects changes while assembling the record.
            if validate() != hashes:
                raise Refusal('Source hashes changed before creation')
            wanted = hashlib.sha256(payload).hexdigest()
            mask = os.umask(0o077)
            try:
                out = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL |
                              os.O_NOFOLLOW | os.O_NOATIME, 0o600, dir_fd=parent)
            finally:
                os.umask(mask)
            created = True
            stack.callback(os.close, out)
            os.fchown(out, *owner)
            os.fchmod(out, 0o600)
            remaining = memoryview(payload)
            while remaining:
                n = os.write(out, remaining)
                if n <= 0:
                    raise Refusal('Short write without progress')
                remaining = remaining[n:]
            os.fsync(out)
            os.fsync(parent)
            # A detected race after creation retains evidence and fails closed.
            if validate() != hashes:
                raise Refusal('Source hashes changed after creation')
            s = os.fstat(out)
            actual = digest(out)
            at_path = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (not stat.S_ISREG(s.st_mode) or s.st_uid != owner[0] or
                    s.st_gid != owner[1] or stat.S_IMODE(s.st_mode) != 0o600 or
                    s.st_nlink != 1 or s.st_size != len(payload) or
                    fingerprint(at_path) != fingerprint(s) or
                    fingerprint(os.fstat(out)) != fingerprint(s) or actual != wanted):
                raise Refusal('Post-write ownership/mode/path/SHA256 verification failed')
            return actual
    except Exception as exc:
        if created:
            raise Refusal('K42 WAS CREATED but verification did not complete. '
                          'Preserve it; do not delete, overwrite, or retry. ' + str(exc)) from exc
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-host', action='store_true',
                        help='requires separate operator authorization on actual Forge host')
    parser.add_argument('--context', choices=[CONTEXT])
    args = parser.parse_args(argv)
    if not args.execute_host or args.context != CONTEXT:
        parser.error('explicit --execute-host and privileged host context required')
    if os.geteuid() != 0:
        parser.error('root required; no host files accessed')
    # Context is an operator attestation, not inferred from UID or hostname.
    try:
        with ExitStack() as stack:
            paths = dict(LABELS, target=TARGET)
            directories = {os.path.dirname(p) for p in paths.values()}
            handles = {p: secure_directory(p, stack) for p in sorted(directories)}
            locations = {k: (handles[os.path.dirname(p)], os.path.basename(p))
                         for k, p in paths.items()}
            result = write_record(
                {k: locations[k] for k in LABELS}, locations['target'], EXPECTED,
                owner=(0, 0), context=CONTEXT,
                clock=lambda: datetime.now(timezone.utc).isoformat(timespec='seconds'))
            for path, fd in handles.items():
                reopened = secure_directory(path, stack)
                old, new = os.fstat(fd), os.fstat(reopened)
                if (old.st_dev, old.st_ino) != (new.st_dev, new.st_ino):
                    raise Refusal('Directory changed after creation; preserve K42 and investigate')
        print('Verified root:root mode 0600; SHA256 ' + TARGET + ': ' + result)
        return 0
    except Exception as exc:
        print('STOP: ' + str(exc) + '\nIf any K42 record exists, preserve it; '
              'do not delete, overwrite, or retry without operator review.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
