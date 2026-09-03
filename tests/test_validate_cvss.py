"""Tests for scripts/validate_cvss.py.

The base_score cases below are vectors with published CVSS v3.1 scores, so
these tests check the implementation against the specification rather than
against itself. If a refactor breaks the arithmetic, these fail before a
wrong score reaches a report.
"""
import glob
import os
import tempfile
import unittest

from . import context  # noqa: F401  (import for sys.path setup)
import validate_cvss


class BaseScoreTests(unittest.TestCase):
    """Vectors with known published scores, unchanged and changed scope."""

    KNOWN = [
        # Unchanged scope
        ("AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", 9.8),
        ("AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", 7.5),
        ("AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N", 5.3),
        ("AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H", 8.1),
        ("AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H", 7.2),
        ("AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", 6.5),
        ("AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", 7.8),
        ("AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H", 7.8),
        ("AV:P/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", 4.6),
        # Changed scope
        ("AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", 6.1),
        ("AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H", 9.9),
    ]

    def test_known_vectors_score_correctly(self):
        for vector, expected in self.KNOWN:
            with self.subTest(vector=vector):
                self.assertAlmostEqual(
                    validate_cvss.base_score(vector), expected, places=5
                )

    def test_no_impact_scores_zero(self):
        """A vector with no CIA impact is 0.0 whatever its exploitability."""
        self.assertEqual(
            validate_cvss.base_score("AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N"), 0.0
        )

    def test_score_is_capped_at_ten(self):
        for vector, _ in self.KNOWN:
            with self.subTest(vector=vector):
                self.assertLessEqual(validate_cvss.base_score(vector), 10.0)

    def test_changed_scope_scores_above_unchanged(self):
        """Scope change raises the score for otherwise identical metrics."""
        unchanged = validate_cvss.base_score("AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H")
        changed = validate_cvss.base_score("AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H")
        self.assertGreater(changed, unchanged)


class RoundupTests(unittest.TestCase):
    """CVSS v3.1 Appendix A: round to one decimal, always upward."""

    def test_exact_tenths_are_unchanged(self):
        for value in (0.0, 4.0, 7.5, 9.8, 10.0):
            with self.subTest(value=value):
                self.assertEqual(validate_cvss.roundup(value), value)

    def test_anything_above_a_tenth_rounds_up(self):
        self.assertEqual(validate_cvss.roundup(4.001), 4.1)
        self.assertEqual(validate_cvss.roundup(4.02), 4.1)
        self.assertEqual(validate_cvss.roundup(4.09), 4.1)

    def test_float_noise_below_the_threshold_does_not_round_up(self):
        """The integer-scaling form exists to stop 4.0 becoming 4.1."""
        self.assertEqual(validate_cvss.roundup(3.9999999999), 4.0)


class BandTests(unittest.TestCase):
    def test_band_boundaries(self):
        cases = [
            (10.0, "Critical"), (9.0, "Critical"), (8.9, "High"),
            (7.0, "High"), (6.9, "Medium"), (4.0, "Medium"),
            (3.9, "Low"), (0.1, "Low"), (0.0, "None"),
        ]
        for score, expected in cases:
            with self.subTest(score=score):
                self.assertEqual(validate_cvss.band(score), expected)


class CheckTests(unittest.TestCase):
    """check() must actually fail on an inconsistent report, not just pass."""

    GOOD_VECTOR = "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"  # scores 7.5, High

    def write_report(self, body):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        handle.write(body)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def report(
        self, severity="High", score="7.5", vector=None,
        table_severity=None, table_score=None,
    ):
        """A minimal but complete report: one glance row and one finding.

        Both halves are well-formed by default; each argument overrides one
        cell so a test can introduce exactly one inconsistency.
        """
        vector = self.GOOD_VECTOR if vector is None else vector
        table_severity = severity if table_severity is None else table_severity
        table_score = score if table_score is None else table_score
        body = (
            "## Findings at a glance\n\n"
            "| ID | Summary | Severity | Score |\n"
            "|---|---|---|---|\n"
            f"| F-01 | Example finding | **{table_severity}** | {table_score} |\n\n"
            "## Detailed findings\n\n"
            "### F-01: Example finding\n\n"
            "| Field | Value |\n|---|---|\n"
            f"| **Severity** | **{severity}** |\n"
            f"| **CVSS 3.1** | {score}, `{vector}` |\n"
        )
        return self.write_report(body)

    def test_a_consistent_finding_produces_no_problems(self):
        self.assertEqual(validate_cvss.check(self.report()), [])

    def test_a_wrong_score_is_reported(self):
        problems = validate_cvss.check(self.report(score="7.9", table_score="7.9"))
        self.assertTrue(any("does not match vector" in p for p in problems))

    def test_a_wrong_severity_band_is_reported(self):
        problems = validate_cvss.check(
            self.report(severity="Critical", table_severity="Critical")
        )
        self.assertTrue(any("severity Critical" in p for p in problems))

    def test_a_summary_table_disagreeing_with_the_finding_is_reported(self):
        problems = validate_cvss.check(self.report(table_score="8.1"))
        self.assertTrue(any("summary table says" in p for p in problems))

    def test_a_malformed_vector_is_reported_not_crashed(self):
        problems = validate_cvss.check(self.report(vector="AV:N/AC:L/PR:N"))
        self.assertTrue(any("valid CVSS v3.1" in p for p in problems))

    def test_an_impossible_metric_value_is_reported(self):
        problems = validate_cvss.check(
            self.report(vector="AV:X/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N")
        )
        self.assertTrue(any("valid CVSS v3.1" in p for p in problems))

    def test_a_finding_missing_from_the_glance_table_is_reported(self):
        # A detailed finding with no glance row: the check must not skip it.
        body = (
            "### F-01: Example finding\n\n"
            "| **Severity** | **High** |\n"
            f"| **CVSS 3.1** | 7.5, `{self.GOOD_VECTOR}` |\n"
        )
        problems = validate_cvss.check(self.write_report(body))
        self.assertTrue(any("missing from the findings-at-a-glance" in p for p in problems))

    def test_a_glance_row_with_no_detailed_finding_is_reported(self):
        with open(self.report(), encoding="utf-8") as handle:
            body = "| F-02 | Orphan row | **High** | 7.5 |\n\n" + handle.read()
        problems = validate_cvss.check(self.write_report(body))
        self.assertTrue(any("no detailed finding" in p for p in problems))

    def test_a_duplicate_glance_row_is_reported(self):
        body = (
            "| F-01 | Example finding | **High** | 7.5 |\n"
            "| F-01 | Example finding | **High** | 7.5 |\n\n"
            "### F-01: Example finding\n\n"
            "| **Severity** | **High** |\n"
            f"| **CVSS 3.1** | 7.5, `{self.GOOD_VECTOR}` |\n"
        )
        problems = validate_cvss.check(self.write_report(body))
        self.assertTrue(any("more than one" in p for p in problems))

    def test_severity_does_not_leak_from_the_previous_finding(self):
        # F-01 is Critical; F-02 omits its severity row. Without the per-heading
        # reset, F-02 would silently inherit F-01's Critical and pass.
        body = (
            "| F-01 | First | **Critical** | 9.8 |\n"
            "| F-02 | Second | **High** | 7.5 |\n\n"
            "### F-01: First\n\n"
            "| **Severity** | **Critical** |\n"
            "| **CVSS 3.1** | 9.8, `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |\n\n"
            "### F-02: Second\n\n"
            f"| **CVSS 3.1** | 7.5, `{self.GOOD_VECTOR}` |\n"
        )
        problems = validate_cvss.check(self.write_report(body))
        self.assertTrue(any("F-02 has no severity field" in p for p in problems))


class PublishedReportsTests(unittest.TestCase):
    """The reports actually in the repository must all validate.

    This is the same assertion the pre-commit hook makes, run as a test so a
    hand edit to a report is caught by the suite as well as by the hook.
    """

    def test_every_report_is_internally_consistent(self):
        reports = sorted(
            glob.glob(os.path.join(context.REPO_ROOT, "reports", "*.md"))
        )
        self.assertTrue(reports, "no reports found to validate")
        problems = []
        for report in reports:
            problems.extend(validate_cvss.check(report))
        self.assertEqual(problems, [], "\n".join(problems))


class MainFromAnyDirectoryTests(unittest.TestCase):
    """main() resolves reports by absolute path, so cwd must not matter.

    Before the fix it opened a repo-relative path against the process cwd and
    raised FileNotFoundError anywhere but the repo root.
    """

    def test_runs_from_an_unrelated_working_directory(self):
        original = os.getcwd()
        with tempfile.TemporaryDirectory() as elsewhere:
            os.chdir(elsewhere)
            try:
                self.assertEqual(validate_cvss.main(), 0)
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
