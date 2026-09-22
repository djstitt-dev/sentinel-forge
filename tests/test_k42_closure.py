"""Offline synthetic fixtures only; never open host AIDE paths."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
from contextlib import ExitStack
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('k42', ROOT / 'scripts/changes/close_f117k42.py')
k42 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k42)


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.k42-test-', dir=ROOT / 'tests')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, self.fd)
        self.data = {'trusted': b'synthetic database\n', 'candidate': b'synthetic database\n',
                     'policy': b'synthetic policy\n', 'k41': b'synthetic historical evidence\n'}
        for key, data in self.data.items():
            (self.root / key).write_bytes(data)
            (self.root / key).chmod(0o600)
        self.expected = {k: hashlib.sha256(self.data[k]).hexdigest()
                         for k in ('trusted', 'policy', 'k41')}
        self.sources = {k: (self.fd, k) for k in self.data}
        self.target = self.root / 'closure.txt'

    def run_writer(self):
        return k42.write_record(self.sources, (self.fd, self.target.name), self.expected,
                                owner=(os.geteuid(), os.getegid()),
                                context='CODEX SANDBOX CONTEXT (synthetic offline test)',
                                clock=lambda: '2026-09-22T00:00:00+00:00')

    def assert_no_record(self):
        self.assertFalse(os.path.lexists(self.target))

    def test_success_semantics_metadata_hash_and_unchanged_inputs(self):
        before = {k: k42.fingerprint((self.root / k).stat()) for k in self.data}
        result = self.run_writer()
        record = self.target.read_bytes()
        self.assertEqual(result, hashlib.sha256(record).hexdigest())
        s = self.target.stat()
        self.assertEqual((s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode)),
                         (os.geteuid(), os.getegid(), 0o600))
        for key, data in self.data.items():
            self.assertEqual((self.root / key).read_bytes(), data)
            self.assertEqual(k42.fingerprint((self.root / key).stat()), before[key])
            self.assertIn(hashlib.sha256(data).hexdigest().encode(), record)
        for text in ['No current live AIDE-clean assertion is being made.',
                     'Candidate lifecycle remains deferred.', 'outside F1.17 acceptance state',
                     'No new live AIDE integrity check', 'not a new baseline, candidate promotion',
                     'Codex setup', '2026-09-22T00:00:00+00:00', 'CODEX SANDBOX CONTEXT']:
            self.assertIn(text.encode(), record)
        self.assertEqual(set(p.name for p in self.root.iterdir()), set(self.data) | {'closure.txt'})

    def test_each_anchor_mismatch_no_write(self):
        for key in self.expected:
            with self.subTest(key=key):
                (self.root / key).write_bytes(b'tampered')
                with self.assertRaises(k42.Refusal):
                    self.run_writer()
                self.assert_no_record()
                (self.root / key).write_bytes(self.data[key])

    def test_candidate_mismatch_no_write(self):
        (self.root / 'candidate').write_bytes(b'different')
        with self.assertRaises(k42.Refusal):
            self.run_writer()
        self.assert_no_record()

    def test_missing_input_no_write(self):
        (self.root / 'policy').unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_writer()
        self.assert_no_record()

    def test_unreadable_input_no_write(self):
        real = os.open
        def guarded(name, *args, **kwargs):
            if name == 'policy':
                raise PermissionError('simulated unreadable fixture')
            return real(name, *args, **kwargs)
        with patch.object(k42.os, 'open', side_effect=guarded):
            with self.assertRaises(PermissionError):
                self.run_writer()
        self.assert_no_record()

    def test_symlink_source_no_write(self):
        (self.root / 'candidate').unlink()
        (self.root / 'candidate').symlink_to('trusted')
        with self.assertRaises(OSError):
            self.run_writer()
        self.assert_no_record()

    def test_nonregular_source_no_write(self):
        (self.root / 'policy').unlink()
        os.mkfifo(self.root / 'policy', 0o600)
        with self.assertRaises(k42.Refusal):
            self.run_writer()
        self.assert_no_record()

    def test_writable_source_no_write(self):
        (self.root / 'policy').chmod(0o620)
        with self.assertRaises(k42.Refusal):
            self.run_writer()
        self.assert_no_record()

    def test_unexpected_source_owner_no_write(self):
        real = os.fstat
        def wrong_owner(fd):
            s = real(fd)
            values = {name: getattr(s, name) for name in dir(s) if name.startswith('st_')}
            values['st_uid'] = os.geteuid() + 1
            return SimpleNamespace(**values)
        with patch.object(k42.os, 'fstat', side_effect=wrong_owner):
            with self.assertRaises(k42.Refusal):
                self.run_writer()
        self.assert_no_record()

    def test_hardlinked_source_no_write(self):
        os.link(self.root / 'policy', self.root / 'alias')
        with self.assertRaises(k42.Refusal):
            self.run_writer()
        self.assert_no_record()

    def test_existing_record_preserved(self):
        self.target.write_bytes(b'prior evidence')
        with self.assertRaises(k42.Refusal):
            self.run_writer()
        self.assertEqual(self.target.read_bytes(), b'prior evidence')

    def test_dangling_target_symlink_preserved(self):
        self.target.symlink_to('absent')
        with self.assertRaises(k42.Refusal):
            self.run_writer()
        self.assertTrue(self.target.is_symlink())
        self.assertFalse((self.root / 'absent').exists())

    def test_exclusive_create_race_preserves_other_record(self):
        real = os.open
        def race(name, flags, *args, **kwargs):
            if flags & os.O_EXCL:
                self.target.write_bytes(b'other writer')
            return real(name, flags, *args, **kwargs)
        with patch.object(k42.os, 'open', side_effect=race):
            with self.assertRaises(FileExistsError):
                self.run_writer()
        self.assertEqual(self.target.read_bytes(), b'other writer')

    def test_mutation_before_creation_no_write(self):
        real = k42.render
        def mutate(*args):
            (self.root / 'policy').write_bytes(b'changed during render')
            return real(*args)
        with patch.object(k42, 'render', side_effect=mutate):
            with self.assertRaises(k42.Refusal):
                self.run_writer()
        self.assert_no_record()

    def test_identical_source_replacement_no_write(self):
        real = k42.render
        def replace(*args):
            (self.root / 'replacement').write_bytes(self.data['policy'])
            (self.root / 'replacement').chmod(0o600)
            os.replace(self.root / 'replacement', self.root / 'policy')
            return real(*args)
        with patch.object(k42, 'render', side_effect=replace):
            with self.assertRaises(k42.Refusal):
                self.run_writer()
        self.assert_no_record()

    def test_partial_write_failure_preserves_record_and_refuses_retry(self):
        real = os.write
        count = 0
        def fail(fd, data):
            nonlocal count
            count += 1
            if count == 1:
                return real(fd, data[:20])
            raise OSError('simulated disk failure')
        with patch.object(k42.os, 'write', side_effect=fail):
            with self.assertRaisesRegex(k42.Refusal, 'K42 WAS CREATED'):
                self.run_writer()
        before = self.target.read_bytes()
        self.assertEqual(len(before), 20)
        with self.assertRaises(k42.Refusal):
            self.run_writer()
        self.assertEqual(self.target.read_bytes(), before)

    def test_postwrite_metadata_failure_preserves_record(self):
        real = os.fchmod
        with patch.object(k42.os, 'fchmod', side_effect=lambda fd, mode: real(fd, 0o640)):
            with self.assertRaisesRegex(k42.Refusal, 'K42 WAS CREATED'):
                self.run_writer()
        self.assertTrue(self.target.exists())

    def test_postwrite_hash_failure_preserves_record(self):
        real = k42.digest
        def corrupt(fd):
            value = real(fd)
            if self.target.exists() and os.fstat(fd).st_ino == self.target.stat().st_ino:
                return '0' * 64
            return value
        with patch.object(k42, 'digest', side_effect=corrupt):
            with self.assertRaisesRegex(k42.Refusal, 'K42 WAS CREATED'):
                self.run_writer()
        self.assertTrue(self.target.exists())

    def test_postwrite_source_mutation_preserves_record(self):
        real = os.fsync
        def mutate(fd):
            real(fd)
            (self.root / 'policy').write_bytes(b'concurrent change')
        with patch.object(k42.os, 'fsync', side_effect=mutate):
            with self.assertRaisesRegex(k42.Refusal, 'K42 WAS CREATED'):
                self.run_writer()
        self.assertTrue(self.target.exists())

    def test_ownership_set_failure_preserves_record(self):
        with patch.object(k42.os, 'fchown', side_effect=PermissionError('simulated')):
            with self.assertRaisesRegex(k42.Refusal, 'K42 WAS CREATED'):
                self.run_writer()
        self.assertTrue(self.target.exists())

    def test_fsync_failure_preserves_record(self):
        with patch.object(k42.os, 'fsync', side_effect=OSError('simulated')):
            with self.assertRaisesRegex(k42.Refusal, 'K42 WAS CREATED'):
                self.run_writer()
        self.assertTrue(self.target.exists())

    def test_cli_no_optin_cannot_open_host(self):
        with patch.object(k42, 'secure_directory', side_effect=AssertionError('host access')):
            with self.assertRaises(SystemExit):
                k42.main([])

    def test_cli_nonroot_cannot_open_host(self):
        with patch.object(k42.os, 'geteuid', return_value=1001):
            with patch.object(k42, 'secure_directory', side_effect=AssertionError('host access')):
                with self.assertRaises(SystemExit):
                    k42.main(['--execute-host', '--context', k42.CONTEXT])

    def test_cli_missing_context_cannot_open_host(self):
        with patch.object(k42, 'secure_directory', side_effect=AssertionError('host access')):
            with self.assertRaises(SystemExit):
                k42.main(['--execute-host'])

    def test_directory_chain_unsafe_owner_or_mode_refused_without_real_paths(self):
        for uid, mode in [(1001, 0o755), (0, 0o777)]:
            with self.subTest(uid=uid, mode=mode):
                with patch.object(k42.os, 'open', return_value=123):
                    with patch.object(k42.os, 'close'):
                        with patch.object(k42.os, 'fstat', side_effect=[
                                SimpleNamespace(st_uid=0, st_mode=0o755),
                                SimpleNamespace(st_uid=uid, st_mode=mode)]):
                            with ExitStack() as stack:
                                with self.assertRaises(k42.Refusal):
                                    k42.secure_directory('/synthetic', stack)

    def test_production_constants_match_manifest(self):
        m = json.loads((ROOT / 'evidence/manifests/aide-anchors.json').read_text())
        by_path = {a['path']: a['sha256'] for a in m['anchors']}
        for key, value in k42.EXPECTED.items():
            self.assertEqual(value, by_path[k42.LABELS[key]])
        self.assertIsNone(by_path[k42.CANDIDATE])


if __name__ == '__main__':
    unittest.main()
