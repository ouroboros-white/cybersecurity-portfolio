"""Validate CVSS v3.1 base scores in reports against their own vectors.

Every finding in reports/ states a score and a vector, e.g.

    | **CVSS 3.1** | 7.8, `AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` |

The score is derived from the vector, so the two can never legitimately
disagree. This recomputes each score from the specification arithmetic and
reports any mismatch, and also checks the stated severity band and the score
in the findings-at-a-glance table.

Usage:
    python scripts/validate_cvss.py

Exits non-zero if any report fails, so it can be used as a pre-commit check.
"""

import glob
import math
import os
import re
import sys

AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
AC = {"L": 0.77, "H": 0.44}
PR_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
PR_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.50}
UI = {"N": 0.85, "R": 0.62}
CIA = {"H": 0.56, "L": 0.22, "N": 0.0}

FINDING_RE = re.compile(r"\*\*CVSS 3\.1\*\*\s*\|\s*([0-9.]+),\s*`(AV:[^`]+)`")
SEVERITY_RE = re.compile(r"\*\*Severity\*\*\s*\|\s*\*\*(\w+)\*\*")
TABLE_RE = re.compile(r"^\|\s*(F-\d+)\s*\|.*\|\s*\*\*(\w+)\*\*\s*\|\s*([0-9.]+)\s*\|")


def roundup(value):
    """CVSS v3.1 Appendix A roundup: round to one decimal, always upward."""
    scaled = int(round(value * 100000))
    if scaled % 10000 == 0:
        return scaled / 100000.0
    return (math.floor(scaled / 10000) + 1) / 10.0


def base_score(vector):
    metrics = dict(part.split(":") for part in vector.split("/"))
    changed = metrics["S"] == "C"

    iss = 1 - (
        (1 - CIA[metrics["C"]]) * (1 - CIA[metrics["I"]]) * (1 - CIA[metrics["A"]])
    )
    if changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    else:
        impact = 6.42 * iss

    privileges = PR_CHANGED if changed else PR_UNCHANGED
    exploitability = (
        8.22
        * AV[metrics["AV"]]
        * AC[metrics["AC"]]
        * privileges[metrics["PR"]]
        * UI[metrics["UI"]]
    )

    if impact <= 0:
        return 0.0
    if changed:
        return roundup(min(1.08 * (impact + exploitability), 10))
    return roundup(min(impact + exploitability, 10))


def band(score):
    if score >= 9.0:
        return "Critical"
    if score >= 7.0:
        return "High"
    if score >= 4.0:
        return "Medium"
    if score > 0.0:
        return "Low"
    return "None"


def check(path):
    problems = []
    lines = open(path, encoding="utf-8").read().splitlines()

    # Findings-at-a-glance rows: {finding id: (severity, score)}
    table = {}
    for line in lines:
        match = TABLE_RE.match(line)
        if match:
            table[match.group(1)] = (match.group(2), float(match.group(3)))

    current_severity = None
    current_id = None
    for number, line in enumerate(lines, 1):
        heading = re.match(r"^###\s+(F-\d+)", line)
        if heading:
            current_id = heading.group(1)
        severity = SEVERITY_RE.search(line)
        if severity:
            current_severity = severity.group(1)

        match = FINDING_RE.search(line)
        if not match:
            continue

        claimed = float(match.group(1))
        vector = match.group(2)
        actual = base_score(vector)

        if abs(actual - claimed) > 0.001:
            problems.append(
                f"{path}:{number}: score {claimed} does not match vector "
                f"{vector} (computed {actual})"
            )
        if current_severity and current_severity != band(actual):
            problems.append(
                f"{path}:{number}: severity {current_severity} does not match "
                f"score {actual} (band {band(actual)})"
            )
        if current_id in table:
            table_severity, table_score = table[current_id]
            if abs(table_score - actual) > 0.001:
                problems.append(
                    f"{path}:{number}: {current_id} summary table says "
                    f"{table_score}, detailed finding computes {actual}"
                )
            if table_severity != band(actual):
                problems.append(
                    f"{path}:{number}: {current_id} summary table severity "
                    f"{table_severity} does not match band {band(actual)}"
                )

    return problems


def main():
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    reports = sorted(glob.glob(os.path.join(root, "reports", "*.md")))
    if not reports:
        print("no reports found")
        return 1

    problems = []
    for report in reports:
        problems.extend(check(os.path.relpath(report, root)))

    if problems:
        for problem in problems:
            print(problem)
        print(f"\n{len(problems)} problem(s) across {len(reports)} report(s)")
        return 1

    print(f"all CVSS scores consistent across {len(reports)} report(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
