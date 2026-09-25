"""Read-only structural checks for WP5 proposals; no host, runtime or semantic security validation."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / 'docs/architecture/forge-operational-architecture.md'
PLAN = ROOT / 'docs/plans/wp5-operational-requirements.md'


def rows(text, pattern):
    return [line for line in text.splitlines() if re.match(pattern, line)]


class WP5DocumentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arch = ARCH.read_text()
        cls.plan = PLAN.read_text()
        cls.combined = cls.arch + '\n' + cls.plan

    def test_required_topics_and_draft_status(self):
        topics = {
            self.arch: ['Scope and non-goals', 'Component responsibilities and authority boundaries',
                        'Trust-boundary model', 'Proposed logical interfaces and data flows',
                        'AI orchestration trust boundary',
                        'External dependencies', 'Identity and access requirements',
                        'Monitoring and audit requirements', 'Failure and fail-closed requirements',
                        'Recovery requirements and objectives', 'Security invariants',
                        'Decision state and capability-scoped deferrals'],
            self.plan: ['WP5 scope and explicit non-goals', 'Assumptions and known facts',
                        'Operator decision register', 'Measurable operational requirements',
                        'Threat and failure coverage', 'Acceptance criteria',
                        'Validation approach', 'Stop conditions', 'WP5 exit criteria',
                        'Requirements for entering WP6'],
        }
        for document, headings in topics.items():
            self.assertIn('Status: WP5 DRAFT', document)
            self.assertIn('OPERATOR REVIEW REQUIRED', document)
            for heading in headings:
                self.assertIn('\n## ' + heading + '\n', document)
            self.assertEqual(document.count('```') % 2, 0)

    def test_requirement_definitions_unique_complete_and_references_resolve(self):
        definitions = rows(self.plan, r'^\| FORGE-[A-Z]+-\d{3} \|')
        ids = [line.split('|')[1].strip() for line in definitions]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))
        for line in definitions:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            self.assertEqual(len(cells), 4)
            self.assertTrue(all(cells))
        references = set(re.findall(r'\bFORGE-[A-Z]+-\d{3}\b', self.combined))
        self.assertEqual(references, set(ids))
        self.assertEqual({i.split('-')[1] for i in ids},
                         {'AUTH', 'IF', 'IAM', 'MON', 'FAIL', 'REC', 'ACC', 'AI'})

    def test_decisions_have_options_tradeoffs_and_operator_status(self):
        definitions = rows(self.plan, r'^\| DEC-\d{2} \|')
        ids = [line.split('|')[1].strip() for line in definitions]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))
        for line in definitions:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            self.assertEqual(len(cells), 6)
            self.assertTrue(all(cells))
            approved = {
                'DEC-01', 'DEC-02', 'DEC-03', 'DEC-04', 'DEC-05',
                'DEC-14', 'DEC-15', 'DEC-16'
            }
            deferred = {
                'DEC-06', 'DEC-07', 'DEC-08', 'DEC-09',
                'DEC-10', 'DEC-11', 'DEC-12', 'DEC-13'
            }

            if cells[0] in approved:
                expected = 'OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25'
            elif cells[0] in deferred:
                expected = (
                    'OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL '
                    'FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25'
                )
            else:
                self.fail(f'unclassified decision state: {cells[0]}')

            self.assertEqual(cells[-1], expected)
        self.assertEqual(set(re.findall(r'\bDEC-\d{2}\b', self.combined)), set(ids))

    def test_capability_scoped_deferrals_are_explicit_and_fail_closed(self):
        deferred = {
            'DEC-06', 'DEC-07', 'DEC-08', 'DEC-09',
            'DEC-10', 'DEC-11', 'DEC-12', 'DEC-13'
        }

        definitions = {
            line.split('|')[1].strip():
                [cell.strip() for cell in line.split('|')[1:-1]]
            for line in rows(self.plan, r'^\| DEC-\d{2} \|')
        }

        self.assertTrue(deferred <= set(definitions))

        expected_status = (
            'OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL '
            'FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25'
        )

        for decision in deferred:
            cells = definitions[decision]
            self.assertEqual(cells[-1], expected_status)
            self.assertIn('DEFERRED FOR INITIAL CAPABILITY:', cells[-2])
            self.assertNotIn('APPROVED:', cells[-2])

        self.assertIn(
            'A deferral is not an architectural approval of an unknown value',
            self.plan
        )
        self.assertIn(
            'permit a missing choice to become an executable default',
            self.plan
        )
        self.assertIn(
            'affected work stops at that dependency for operator disposition',
            self.arch
        )
        self.assertIn(
            'WP5 itself remains pending operator architecture/security review',
            self.arch
        )

    def test_no_stale_blanket_decision_state_language(self):
        stale = (
            'DEC-01 through DEC-03 and DEC-14 through DEC-16 have',
            'DEC-04 through DEC-13 remain unresolved',
            'unresolved and approved architectural statuses',
            'Unresolved decisions requiring operator approval',
        )
        for phrase in stale:
            self.assertNotIn(phrase, self.combined)

        for document in (self.arch, self.plan):
            self.assertIn('DEC-01 through DEC-05', document)
            self.assertIn('DEC-06 through DEC-13', document)
            self.assertIn('capability-scoped', document)

    def test_interface_and_threat_coverage(self):
        definitions = rows(self.arch, r'^\| IF-\d{2} ')
        ids = [re.search(r'IF-\d{2}', line).group() for line in definitions]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {f'IF-{i:02}' for i in range(1, 10)})
        for line in definitions:
            self.assertIn('DEC-', line)
        threats = ['Unauthorized caller', 'Replay', 'Substitution/tampering',
                   'Stale artifact/state', 'Identity mismatch', 'Partial transfer',
                   'Interrupted operation', 'Unavailable dependency', 'Duplicate operation',
                   'Evidence loss', 'Monitoring failure', 'Clock/time ambiguity',
                   'Privilege-boundary violation']
        for threat in threats:
            matching = [line for line in self.plan.splitlines()
                        if line.startswith('| ' + threat + ' |')]
            self.assertEqual(len(matching), 1)
            self.assertRegex(matching[0], r'FORGE-[A-Z]+-\d{3}')

    def test_ai_definitions_and_gate_references_present(self):
        # Structural presence/reference integrity only, not security effectiveness.
        ai_ids = {line.split('|')[1].strip()
                  for line in rows(self.plan, r'^\| FORGE-AI-\d{3} \|')}
        self.assertTrue({f'FORGE-AI-{i:03}' for i in range(1, 12)} <= ai_ids)
        decisions = {line.split('|')[1].strip()
                     for line in rows(self.plan, r'^\| DEC-\d{2} \|')}
        self.assertTrue({'DEC-14', 'DEC-15', 'DEC-16'} <= decisions)
        interface = rows(self.arch, r'^\| IF-09 ')
        self.assertEqual(len(interface), 1)
        entry = self.plan.split('## Requirements for entering WP6\n', 1)[1]
        for decision in ('DEC-14', 'DEC-15', 'DEC-16'):
            self.assertIn(decision, interface[0])
            self.assertIn(decision, entry)
        defined_interfaces = {re.search(r'IF-\d{2}', line).group()
                              for line in rows(self.arch, r'^\| IF-\d{2} ')}
        self.assertEqual(set(re.findall(r'\bIF-\d{2}\b', self.combined)),
                         defined_interfaces)

    def test_ai_threat_cases_reference_ai_requirements(self):
        for concern in ('Prompt injection', 'Malicious model output',
                        'Hallucinated tool request', 'Scope expansion',
                        'Approval spoofing', 'Poisoned model context',
                        'Sensitive provider disclosure', 'Model/provider substitution',
                        'Model version drift', 'Runaway/repeated repair loop',
                        'Tool outside work-package authority',
                        'Governing policy self-modification'):
            matching = [line for line in self.plan.splitlines()
                        if line.startswith('| ' + concern + ' |')]
            self.assertEqual(len(matching), 1)
            self.assertRegex(matching[0], r'FORGE-AI-\d{3}')

    def test_local_document_links_resolve(self):
        for path in (ARCH, PLAN):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                relative = target.split('#', 1)[0]
                self.assertNotIn('://', relative)
                self.assertTrue((path.parent / relative).resolve().is_relative_to(ROOT))
                self.assertTrue((path.parent / relative).is_file(), target)

    def test_no_affirmative_status_claims(self):
        # Narrow status guard only; semantic approval/security review remains manual.
        for claim in (r'(?im)^Status:\s*(?:WP5\s+)?(?:APPROVED|COMPLETE|DEPLOYED)\b',
                      r'(?i)\bForge is operationally ready\b',
                      r'(?i)\bWP5 (?:is|has been) (?:approved|completed)\b'):
            self.assertNotRegex(self.combined, claim)


if __name__ == '__main__':
    unittest.main()
