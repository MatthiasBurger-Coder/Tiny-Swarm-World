#!/usr/bin/env python3
"""Report branch coverage for non-comment lines added by a Git diff."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git base revision for the comparison.")
    parser.add_argument("--coverage-json", type=Path, required=True)
    args = parser.parse_args()

    added_lines = _added_source_lines(args.base)
    coverage = json.loads(args.coverage_json.read_text(encoding="utf-8"))
    covered_lines = 0
    total_lines = 0
    covered_arcs = 0
    total_arcs = 0

    for relative_path, line_numbers in sorted(added_lines.items()):
        source_path = Path(relative_path)
        source_lines = source_path.read_text(encoding="utf-8").splitlines()
        executable_lines = {
            line_number
            for line_number in line_numbers
            if 0 < line_number <= len(source_lines)
            and source_lines[line_number - 1].strip()
            and not source_lines[line_number - 1].lstrip().startswith("#")
        }
        file_coverage = coverage.get("files", {}).get(relative_path, {})
        executed = set(file_coverage.get("executed_lines", []))
        covered_lines += len(executable_lines & executed)
        total_lines += len(executable_lines)

        executed_arcs = {
            tuple(arc) for arc in file_coverage.get("executed_branches", [])
        }
        missing_arcs = {
            tuple(arc) for arc in file_coverage.get("missing_branches", [])
        }
        added_arcs = {
            arc for arc in executed_arcs | missing_arcs if arc and arc[0] in executable_lines
        }
        covered_arcs += len(added_arcs & executed_arcs)
        total_arcs += len(added_arcs)

    _print_metric("Added non-comment production lines", covered_lines, total_lines)
    _print_metric("Added source branch arcs", covered_arcs, total_arcs)
    return 0 if _passes(covered_lines, total_lines) and _passes(covered_arcs, total_arcs) else 1


def _added_source_lines(base: str) -> dict[str, set[int]]:
    result = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}...HEAD", "--", "src"],
        check=True,
        capture_output=True,
        text=True,
    )
    added: dict[str, set[int]] = {}
    relative_path = ""
    next_line = 0
    for raw_line in result.stdout.splitlines():
        if raw_line.startswith("+++ b/"):
            relative_path = raw_line[6:]
            if not relative_path.endswith(".py"):
                relative_path = ""
            continue
        hunk = _HUNK.match(raw_line)
        if hunk:
            next_line = int(hunk.group("start"))
            continue
        if not relative_path or not next_line:
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            added.setdefault(relative_path, set()).add(next_line)
            next_line += 1
        elif raw_line.startswith("-"):
            continue
        else:
            next_line += 1
    return added


def _print_metric(name: str, covered: int, total: int) -> None:
    percentage = 100.0 if total == 0 else covered * 100.0 / total
    print(f"{name}: {covered}/{total} ({percentage:.1f}%)")


def _passes(covered: int, total: int) -> bool:
    return total == 0 or covered * 100 >= total * 95


if __name__ == "__main__":
    raise SystemExit(main())
