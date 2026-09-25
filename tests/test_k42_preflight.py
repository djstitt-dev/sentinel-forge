"""Offline source inspection and mocked preflight checks; no host evidence I/O."""
import ast
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/verify/preflight_f117k42.py'
SOURCE = SCRIPT.read_text()
TREE = ast.parse(SOURCE)
spec = importlib.util.spec_from_file_location('k42_preflight', SCRIPT)
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)  # Inert import; main is guarded.


def file_stat(uid=0, gid=0, mode=stat.S_IFREG | 0o600, links=1):
    return SimpleNamespace(st_uid=uid, st_gid=gid, st_mode=mode, st_nlink=links,
                           st_dev=42, st_ino=123, st_size=456,
                           st_mtime_ns=100, st_ctime_ns=200)


class PreflightTests(unittest.TestCase):
    def test_parse_compile_and_inert_import(self):
        compile(SOURCE, str(SCRIPT), 'exec')  # In memory; no bytecode file.
        with patch.object(pf.os, 'open', side_effect=AssertionError('host open')):
            with patch.object(pf.subprocess, 'run', side_effect=AssertionError('command')):
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

    def test_k41_exact_single_literal_on_one_physical_line(self):
        wanted = '/var/lib/aide/trusted-history/f117k41-final-post-promotion-verification.txt'
        assignments = [n for n in TREE.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == 'K41' for t in n.targets)]
        self.assertEqual(len(assignments), 1)
        node = assignments[0]
        self.assertIsInstance(node.value, ast.Constant)
        self.assertEqual(node.value.value, wanted)
        self.assertEqual(node.lineno, node.end_lineno)
        self.assertEqual(SOURCE.splitlines()[node.lineno - 1], 'K41 = "' + wanted + '"')

    def test_approved_ancestor_and_writer_hash(self):
        self.assertEqual(pf.APPROVED_ANCESTOR, '26a1dca85931d2bcb861b168cc3a328216b8a83e')
        self.assertEqual(pf.WRITER_HASH,
                         '23c40f541e9d23c88c29118d16e517af689bcf44bd1f5839b402ac4d0d9356a9')
        self.assertEqual(hashlib.sha256((ROOT / 'scripts/changes/close_f117k42.py').read_bytes()).hexdigest(),
                         pf.WRITER_HASH)

    def test_exact_host_identity(self):
        self.assertEqual((pf.HOSTNAME, pf.MACHINE_ID, pf.KERNEL, pf.ARCHITECTURE,
                          pf.VIRTUALIZATION, pf.INTERFACE, pf.IPV4, pf.PREFIXLEN),
                         ('sentinel-forge', 'c1c620cdbd8b4c4fbdd827ed2d769b4f',
                          '7.0.0-31-generic', 'x86_64', 'oracle', 'enp0s8',
                          '192.168.56.104', 24))
        self.assertEqual(pf.OS_IDENTITY, {'ID': 'ubuntu', 'VERSION_ID': '26.04',
                         'VERSION_CODENAME': 'resolute', 'PRETTY_NAME': 'Ubuntu 26.04.1 LTS'})

    def test_anchor_constants_match_repository_manifest(self):
        manifest = json.loads((ROOT / 'evidence/manifests/aide-anchors.json').read_text())
        hashes = {a['path']: a['sha256'] for a in manifest['anchors']}
        self.assertEqual(pf.EXPECTED, {p: hashes[p] for p in (pf.TRUSTED, pf.POLICY, pf.K41)})
        self.assertIsNone(hashes[pf.CANDIDATE])
        self.assertEqual(pf.TARGET, '/var/lib/aide/trusted-history/f117k42-evidence-closure.txt')

    def test_only_readonly_os_operations_and_no_dynamic_code(self):
        allowed = {'open', 'close', 'stat', 'fstat', 'read', 'lseek', 'geteuid', 'uname'}
        for node in ast.walk(TREE):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'os':
                        self.assertIn(node.func.attr, allowed)
                    if node.func.value.id == 'subprocess':
                        self.assertEqual(node.func.attr, 'run')
                if isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {'open', 'exec', 'eval', 'compile', '__import__'})
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == 'os' and node.attr.startswith('O_'):
                    self.assertIn(node.attr, {'O_RDONLY', 'O_DIRECTORY', 'O_NOFOLLOW',
                                             'O_NOATIME', 'O_NONBLOCK'})
        opens = [n for n in ast.walk(TREE) if isinstance(n, ast.Call)
                 and ast.unparse(n.func) == 'os.open']
        self.assertEqual(len(opens), 3)
        for node in opens:
            self.assertIn(ast.unparse(node.args[1]), {
                'self.flags', 'os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOATIME'})
        constructor = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)
                           and n.name == '__init__')
        self.assertIn('os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NOATIME',
                      ast.unparse(constructor))

    def test_no_aide_or_writer_execution_and_only_readonly_commands(self):
        calls = [n for n in ast.walk(TREE) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'run']
        signatures = {ast.unparse(n) for n in calls}
        expected_calls = {
            "run('/usr/bin/ps', '-e', '-o', 'pid=', '-o', 'comm=')",
            "run(*(GIT + ['rev-parse', '--show-toplevel']))",
            "run(*(GIT + ['symbolic-ref', '--quiet', 'HEAD']))",
            "run(*(GIT + ['rev-parse', '--verify', 'HEAD^{commit}']))",
            "run(*(GIT + ['merge-base', '--is-ancestor', APPROVED_ANCESTOR, head]))",
            "run(*(GIT + ['ls-files', '-v', '-z']))",
            "run(*(GIT + ['diff-index', '--cached', '--quiet', head, '--']))",
            "run(*(GIT + ['diff-files', '--quiet', '--']))",
            "run(*(GIT + ['ls-files', '--error-unmatch', '--', relative]))",
            "run(*(GIT + ['cat-file', 'blob', head + ':' + relative]), binary=True)",
            "run(*(GIT + ['status', '--porcelain=v1', '--untracked-files=all', '--ignore-submodules=none']))",
            "run('/usr/bin/hostname')", "run('/usr/bin/systemd-detect-virt')",
            "run('ip', '-j', '-4', 'address', 'show', 'dev', INTERFACE)",
        }
        self.assertEqual(signatures, {
            ast.unparse(ast.parse(call, mode='eval').body) for call in expected_calls
        })
        subprocess_calls = [n for n in ast.walk(TREE) if isinstance(n, ast.Call)
                            and ast.unparse(n.func) == 'subprocess.run']
        self.assertEqual(len(subprocess_calls), 1)
        self.assertEqual(ast.unparse(subprocess_calls[0]),
                         'subprocess.run(args, env=ENV, text=not binary, capture_output=True)')
        self.assertIn('--no-optional-locks', pf.GIT)
        self.assertEqual(pf.ENV['GIT_OPTIONAL_LOCKS'], '0')

    def test_nonroot_candidate_metadata_printed_before_refusal_without_open(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.open_directory = Mock(return_value=99)
        output = io.StringIO()
        with patch.object(pf.os, 'stat', return_value=file_stat(uid=111)) as stat_call:
            with patch.object(pf.os, 'open', side_effect=AssertionError('must not open candidate')):
                with redirect_stdout(output):
                    with self.assertRaisesRegex(RuntimeError, 'root required'):
                        view.open_regular(pf.CANDIDATE)
        self.assertEqual(output.getvalue(),
                         'METADATA ' + pf.CANDIDATE + ': type=- uid=111 gid=0 mode=0600 '
                         'links=1 device=42 inode=123 size=456\n')
        stat_call.assert_called_once_with('aide.db.new', dir_fd=99, follow_symlinks=False)

    def test_unsafe_source_type_mode_or_links_refused(self):
        for s in (file_stat(mode=stat.S_IFLNK | 0o777), file_stat(links=2),
                  file_stat(mode=stat.S_IFREG | 0o620)):
            view = pf.Inspection.__new__(pf.Inspection)
            view.open_directory = Mock(return_value=99)
            with patch.object(pf.os, 'stat', return_value=s):
                with patch.object(pf.os, 'open', side_effect=AssertionError('host open')):
                    with redirect_stdout(io.StringIO()):
                        with self.assertRaises(RuntimeError):
                            view.open_regular(pf.CANDIDATE)

    def test_aide_runtime_directory_accepts_pinned_service_identity(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.operator = SimpleNamespace(pw_uid=1001, pw_gid=1001)
        view.aide = SimpleNamespace(pw_uid=pf.AIDE_UID, pw_gid=pf.AIDE_GID)
        view.directories = {}
        runtime = file_stat(uid=pf.AIDE_UID, gid=0,
                            mode=stat.S_IFDIR | 0o700)
        with patch.object(pf.os, 'fstat', return_value=runtime):
            with redirect_stdout(io.StringIO()):
                view.check_directory(pf.AIDE_RUNTIME, 2)

    def test_trusted_history_remains_root_controlled_below_aide_runtime(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.operator = SimpleNamespace(pw_uid=1001, pw_gid=1001)
        view.aide = SimpleNamespace(pw_uid=pf.AIDE_UID, pw_gid=pf.AIDE_GID)
        view.directories = {}

        safe = file_stat(uid=0, gid=0, mode=stat.S_IFDIR | 0o700)
        with patch.object(pf.os, 'fstat', return_value=safe):
            with redirect_stdout(io.StringIO()):
                view.check_directory('/var/lib/aide/trusted-history', 2)

        for unsafe in (
            file_stat(uid=pf.AIDE_UID, gid=0, mode=stat.S_IFDIR | 0o700),
            file_stat(uid=0, gid=0, mode=stat.S_IFDIR | 0o720),
            file_stat(uid=0, gid=0, mode=stat.S_IFDIR | 0o702),
        ):
            view.directories = {}
            with patch.object(pf.os, 'fstat', return_value=unsafe):
                with self.assertRaisesRegex(RuntimeError,
                                            'Unsafe host ancestor ownership/mode'):
                    view.check_directory('/var/lib/aide/trusted-history', 2)

    def test_repository_file_0664_owned_by_forgeadmin_is_allowed(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.stack = SimpleNamespace(callback=lambda *args: None)
        view.operator = SimpleNamespace(pw_uid=1001, pw_gid=1001)
        view.open_directory = Mock(return_value=99)
        s = file_stat(uid=1001, gid=1001, mode=stat.S_IFREG | 0o664)
        with patch.object(pf.os, 'stat', return_value=s):
            with patch.object(pf.os, 'open', return_value=123):
                with patch.object(pf.os, 'fstat', return_value=s):
                    entry = view.open_regular(pf.PREFLIGHT, repository=True)
        self.assertEqual(entry[0], 123)

    def test_repository_directory_0775_owned_by_forgeadmin_is_allowed(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.operator = SimpleNamespace(pw_uid=1001, pw_gid=1001)
        view.directories = {}
        s = file_stat(uid=1001, mode=stat.S_IFDIR | 0o775)
        with patch.object(pf.os, 'fstat', return_value=s):
            view.check_directory('/repository', 2, repository=True)

    def test_repository_world_writable_file_and_directory_refused(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.operator = SimpleNamespace(pw_uid=1001, pw_gid=1001)
        view.open_directory = Mock(return_value=99)
        for mode in (stat.S_IFREG | 0o666, stat.S_IFREG | 0o607):
            with self.subTest(mode=oct(mode)):
                with patch.object(pf.os, 'stat', return_value=file_stat(uid=1001, mode=mode)):
                    with self.assertRaisesRegex(RuntimeError, 'World-writable repository'):
                        view.open_regular(pf.PREFLIGHT, repository=True)
        view.directories = {}
        with patch.object(pf.os, 'fstat', return_value=file_stat(uid=1001, mode=stat.S_IFDIR | 0o777)):
            with self.assertRaisesRegex(RuntimeError, 'World-writable repository ancestor'):
                view.check_directory('/repository', 2, repository=True)

    def test_repository_symlink_and_hardlink_refused(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.operator = SimpleNamespace(pw_uid=1001, pw_gid=1001)
        view.open_directory = Mock(return_value=99)
        for mode, links in ((stat.S_IFLNK | 0o777, 1), (stat.S_IFREG | 0o664, 2)):
            with self.subTest(mode=oct(mode), links=links):
                with patch.object(pf.os, 'stat', return_value=file_stat(uid=1001, mode=mode, links=links)):
                    with self.assertRaises(RuntimeError):
                        view.open_regular(pf.PREFLIGHT, repository=True)

    def test_privileged_evidence_remains_root_only_and_strict(self):
        view = pf.Inspection.__new__(pf.Inspection)
        view.operator = SimpleNamespace(pw_uid=1001, pw_gid=1001)
        view.open_directory = Mock(return_value=99)
        for uid, mode in ((1001, stat.S_IFREG | 0o600), (0, stat.S_IFREG | 0o620)):
            with self.subTest(uid=uid, mode=oct(mode)):
                with patch.object(pf.os, 'stat', return_value=file_stat(uid=uid, mode=mode)):
                    with self.assertRaisesRegex(RuntimeError, 'root required|Group/world-writable'):
                        view.open_regular(pf.CANDIDATE, repository=False)

    def test_target_absent_never_creates_and_existing_symlink_stops(self):
        with patch.object(pf.os, 'open', side_effect=AssertionError('target creation')):
            with patch.object(pf.os, 'stat', side_effect=FileNotFoundError):
                with redirect_stdout(io.StringIO()):
                    pf.target_absent(99)
            with patch.object(pf.os, 'stat', return_value=file_stat(mode=stat.S_IFLNK | 0o777)):
                with redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(RuntimeError, 'target exists'):
                        pf.target_absent(99)

    def test_nonroot_stops_before_host_access(self):
        with patch.object(pf.os, 'geteuid', return_value=1001):
            with patch.object(pf.os, 'open', side_effect=AssertionError('host open')):
                with patch.object(pf, 'run', side_effect=AssertionError('host command')):
                    with redirect_stderr(io.StringIO()):
                        self.assertEqual(pf.main(), 1)

    def test_obvious_aide_process_stops(self):
        with patch.object(pf, 'run', return_value='123 aide\n456 python3'):
            with redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, 'AIDE process detected'):
                    pf.no_aide_process()

    def test_final_rechecks_present(self):
        node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'preflight')
        calls = [ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)]
        self.assertEqual(calls.count('verify_repository'), 2)
        self.assertEqual(calls.count('no_aide_process'), 2)
        self.assertEqual(calls.count('target_absent'), 2)
        self.assertEqual(calls.count('view.verify_directories'), 1)
        self.assertIn('require(sha256(writer[0]) == WRITER_HASH', ast.unparse(node))

    def test_binary_command_output_is_not_decoded_or_stripped(self):
        payload = b'\x00\xfftrailing spaces \n\n'
        with patch.object(pf.subprocess, 'run', return_value=SimpleNamespace(
                returncode=0, stdout=payload, stderr=b'')) as command:
            self.assertEqual(pf.run('synthetic-command', binary=True), payload)
            self.assertFalse(command.call_args.kwargs['text'])

    def test_git_error_is_not_treated_as_success(self):
        with patch.object(pf.subprocess, 'run', return_value=SimpleNamespace(
                returncode=1, stdout=b'', stderr=b'missing object')):
            with self.assertRaisesRegex(RuntimeError, 'Command failed'):
                pf.run('synthetic-command', binary=True)


class RepositoryGateTests(unittest.TestCase):
    """Exercise real gate control flow with fake Git responses and pinned bytes.

    No host paths or repository mutations: all process and descriptor I/O mocked.
    """
    def setUp(self):
        self.head = 'a' * 40
        self.branch = 'refs/heads/main'
        self.status = ''
        self.flags = 'H scripts/verify/preflight_f117k42.py\0'
        self.top = pf.REPO
        self.ancestor_ok = True
        self.index_ok = True
        self.tree_ok = True
        self.missing = None
        self.blobs = {pf.PREFLIGHT_REL: SOURCE.encode(),
                      pf.WRITER_REL: (ROOT / 'scripts/changes/close_f117k42.py').read_bytes()}
        self.bytes = dict(self.blobs)
        self.calls = []
        self.preflight_entry = (101, 99, 'preflight_f117k42.py', ())
        self.writer_entry = (102, 99, 'close_f117k42.py', ())

    def fake_git(self, *args, binary=False):
        self.assertEqual(list(args[:len(pf.GIT)]), pf.GIT)
        cmd = list(args[len(pf.GIT):])
        self.calls.append(cmd)
        if cmd == ['rev-parse', '--show-toplevel']:
            return self.top
        if cmd == ['symbolic-ref', '--quiet', 'HEAD']:
            if self.branch is None:
                raise RuntimeError('detached HEAD')
            return self.branch
        if cmd == ['rev-parse', '--verify', 'HEAD^{commit}']:
            return self.head
        if cmd == ['merge-base', '--is-ancestor', pf.APPROVED_ANCESTOR, self.head]:
            if not self.ancestor_ok:
                raise RuntimeError('unrelated ancestry')
            return ''
        if cmd == ['ls-files', '-v', '-z']:
            return self.flags
        if cmd == ['status', '--porcelain=v1', '--untracked-files=all', '--ignore-submodules=none']:
            return self.status
        if cmd == ['diff-index', '--cached', '--quiet', self.head, '--']:
            if not self.index_ok:
                raise RuntimeError('dirty index')
            return ''
        if cmd == ['diff-files', '--quiet', '--']:
            if not self.tree_ok:
                raise RuntimeError('dirty working tree')
            return ''
        if cmd[:3] == ['ls-files', '--error-unmatch', '--']:
            if cmd[3] == self.missing:
                raise RuntimeError('untracked package file')
            return cmd[3]
        if cmd[:2] == ['cat-file', 'blob']:
            self.assertTrue(binary)
            return self.blobs[cmd[2].split(':', 1)[1]]
        raise AssertionError('Unapproved command: ' + repr(cmd))

    def gate(self, initial=None):
        by_fd = {101: self.bytes[pf.PREFLIGHT_REL], 102: self.bytes[pf.WRITER_REL]}
        with patch.object(pf, 'run', side_effect=self.fake_git):
            with patch.object(pf, 'descriptor_bytes', side_effect=by_fd.__getitem__):
                with patch.object(pf, 'verify_unchanged') as stable:
                    with patch.object(pf.os, 'open', side_effect=AssertionError('host I/O')):
                        with redirect_stdout(io.StringIO()):
                            result = pf.verify_repository(self.preflight_entry, self.writer_entry, initial)
                    self.assertEqual(stable.call_count, 2)
                    return result

    def test_attached_clean_descendant_with_exact_blobs_passes(self):
        self.assertEqual(self.gate(), (self.branch, self.head))

    def test_another_descendant_does_not_require_source_edit(self):
        self.head = 'b' * 40
        self.assertEqual(self.gate(), (self.branch, self.head))

    def test_ancestor_itself_without_package_refused(self):
        self.head = pf.APPROVED_ANCESTOR
        with self.assertRaises(RuntimeError):
            self.gate()

    def test_detached_head_refused_even_with_matching_files(self):
        self.branch = None
        with self.assertRaisesRegex(RuntimeError, 'detached'):
            self.gate()

    def test_unrelated_history_refused_even_with_matching_files(self):
        self.ancestor_ok = False
        with self.assertRaisesRegex(RuntimeError, 'ancestry'):
            self.gate()

    def test_wrong_repository_root_refused(self):
        self.top = '/synthetic/other-repository'
        with self.assertRaisesRegex(RuntimeError, 'repository root'):
            self.gate()

    def test_execution_from_copied_script_refused(self):
        with patch.object(pf, '__file__', '/synthetic/copied-preflight.py'):
            with self.assertRaisesRegex(RuntimeError, 'tracked repository pathname'):
                self.gate()

    def test_untracked_or_dirty_status_refused(self):
        for status in ['?? unexpected.txt', ' M README.md', 'M  README.md', 'UU conflict.txt']:
            self.status = status
            with self.subTest(status=status), self.assertRaises(RuntimeError):
                self.gate()

    def test_dirty_index_or_worktree_refused_even_if_status_empty(self):
        self.index_ok = False
        with self.assertRaisesRegex(RuntimeError, 'dirty index'):
            self.gate()
        self.index_ok, self.tree_ok = True, False
        with self.assertRaisesRegex(RuntimeError, 'dirty working tree'):
            self.gate()

    def test_hidden_index_flags_refused(self):
        for flag in ['S', 'h', 's']:
            self.flags = flag + ' hidden.txt\0'
            with self.subTest(flag=flag), self.assertRaises(RuntimeError):
                self.gate()

    def test_each_package_file_must_be_tracked(self):
        for path in self.blobs:
            self.missing = path
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'untracked'):
                self.gate()

    def test_exact_byte_comparison_includes_trailing_newline(self):
        for path in self.blobs:
            original = self.blobs[path]
            self.blobs[path] = original + b'\n'
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'HEAD blob differs'):
                self.gate()
            self.blobs[path] = original

    def test_matching_writer_blob_still_requires_approved_hash(self):
        self.blobs[pf.WRITER_REL] = self.bytes[pf.WRITER_REL] = b'unapproved writer'
        with self.assertRaisesRegex(RuntimeError, 'writer SHA256'):
            self.gate()

    def test_final_head_or_branch_switch_refused(self):
        for initial in [(self.branch, 'b' * 40), ('refs/heads/other', self.head)]:
            with self.subTest(initial=initial), self.assertRaisesRegex(RuntimeError, 'changed'):
                self.gate(initial)

    def test_same_initial_identity_passes_final_gate(self):
        initial = (self.branch, self.head)
        self.assertEqual(self.gate(initial), initial)


if __name__ == '__main__':
    unittest.main()
