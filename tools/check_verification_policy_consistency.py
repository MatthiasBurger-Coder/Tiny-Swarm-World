"""Validate the repository's canonical verification-state policy references."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

POLICY_RELATIVE_PATH = Path("documentation/process/verification-state-policy.md")
DEFAULT_LOCAL_GATE = "python3 tools/quality_gate.py quality"
LIVE_INSTALL_COMMAND = (
    "./install.sh --headless --confirm-reset --non-interactive-live-approval"
)

APPLICABILITY_STATES = frozenset(
    {
        "NOT_APPLICABLE",
        "APPLICABLE_LOCAL",
        "APPLICABLE_LIVE",
        "APPLICABLE_EXTERNAL",
    }
)
LIVE_STATES = frozenset(
    {
        "LIVE_NOT_APPLICABLE",
        "LIVE_CONSENT_MISSING",
        "LIVE_PREREQUISITE_MISSING",
        "LIVE_BLOCKED_BEFORE_MUTATION",
        "LIVE_FAILED_AFTER_MUTATION",
        "LIVE_PARTIAL",
        "LIVE_DEGRADED",
        "LIVE_VERIFIED",
    }
)
EXTERNAL_GATE_STATES = frozenset(
    {
        "EXTERNAL_GATE_NOT_APPLICABLE",
        "EXTERNAL_GATE_UNAVAILABLE",
        "EXTERNAL_GATE_BLOCKED",
        "EXTERNAL_GATE_FAILED",
        "EXTERNAL_GATE_VERIFIED",
    }
)
ALLOWED_STATES = APPLICABILITY_STATES | LIVE_STATES | EXTERNAL_GATE_STATES

_STATE_TOKEN = re.compile(
    r"\b(?:NOT_APPLICABLE|APPLICABLE_[A-Z_]+|LIVE_[A-Z_]+|EXTERNAL_GATE_[A-Z_]+)\b"
)
_FORBIDDEN_PHRASES = (
    "sonarqube is green",
    "sonarqube quality gate must return green",
    "selenium e2e evidence exists",
    "mandatory selenium",
    "run live installation automatically",
)
_SUCCESS_WORD = re.compile(r"\b(?:pass(?:ed)?|success(?:ful)?|green|verified)\b", re.I)
_UNAVAILABLE_WORD = re.compile(
    r"\b(?:skip(?:ped)?|unavailable|inaccessible|missing)\b", re.I
)
_CONSENT_WORD = re.compile(
    r"\b(?:consent|approval|authorized|authorised|explicit|opt[- ]?in|operator|"
    r"zustimmung|freigabe|applicable_live|live gate)\b",
    re.I,
)
_NEGATIVE_WORD = re.compile(
    r"\b(?:must not|mustn't|never|without|non[- ]success|not|cannot|forbidden|"
    r"prohibited|does not|do not|no)\b",
    re.I,
)


@dataclass(frozen=True)
class Finding:
    """One deterministic policy-consistency finding."""

    path: str
    line: int | None
    message: str

    def render(self) -> str:
        location = self.path if self.line is None else f"{self.path}:{self.line}"
        return f"{location}: {self.message}"


def check_repository(repository_root: Path) -> tuple[Finding, ...]:
    """Return policy-consistency findings for the repository at ``repository_root``."""

    root = repository_root.resolve()
    findings: list[Finding] = []
    policy_path = root / POLICY_RELATIVE_PATH
    if not policy_path.is_file():
        return (
            Finding(str(POLICY_RELATIVE_PATH), None, "canonical policy is missing"),
        )

    policy_text = policy_path.read_text(encoding="utf-8")
    findings.extend(_validate_canonical_policy(policy_text))

    for path in _governance_documents(root):
        if path.resolve() == policy_path.resolve():
            continue
        relative_path = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            findings.extend(
                _find_forbidden_wording(relative_path, line_number, line)
            )
            findings.extend(_find_unknown_states(relative_path, line_number, line))
            if LIVE_INSTALL_COMMAND in line and not _has_consent_context(
                lines, line_number - 1
            ):
                findings.append(
                    Finding(
                        relative_path,
                        line_number,
                        "live installation command has no nearby explicit consent context",
                    )
                )
    return tuple(findings)


def _validate_canonical_policy(policy_text: str) -> list[Finding]:
    missing = [
        fragment
        for fragment in (
            DEFAULT_LOCAL_GATE,
            LIVE_INSTALL_COMMAND,
            *sorted(APPLICABILITY_STATES),
            *sorted(LIVE_STATES),
            *sorted(EXTERNAL_GATE_STATES),
        )
        if fragment not in policy_text
    ]
    return [
        Finding(
            POLICY_RELATIVE_PATH.as_posix(),
            None,
            f"canonical policy is missing required fragment: {fragment}",
        )
        for fragment in missing
    ]


def _governance_documents(repository_root: Path) -> tuple[Path, ...]:
    paths = [repository_root / "AGENTS.md", repository_root / "QUALITY.md"]
    process_root = repository_root / "documentation" / "process"
    workflow_root = repository_root / "documentation" / "workflow"
    for directory in (process_root, workflow_root):
        if directory.is_dir():
            paths.extend(sorted(directory.rglob("*.md")))
    return tuple(path for path in paths if path.is_file())


def _find_forbidden_wording(path: str, line_number: int, line: str) -> list[Finding]:
    normalized = " ".join(line.casefold().split())
    findings: list[Finding] = []
    for phrase in _FORBIDDEN_PHRASES:
        if phrase in normalized and not _is_explicitly_negative(line):
            findings.append(
                Finding(path, line_number, f"unconditional verification wording: {phrase}")
            )
    if _UNAVAILABLE_WORD.search(line) and _SUCCESS_WORD.search(line):
        if not _is_explicitly_negative(line):
            findings.append(
                Finding(
                    path,
                    line_number,
                    "unavailable or skipped verification is described as success",
                )
            )
    return findings


def _find_unknown_states(path: str, line_number: int, line: str) -> list[Finding]:
    return [
        Finding(path, line_number, f"unknown verification state: {token}")
        for token in _STATE_TOKEN.findall(line)
        if token not in ALLOWED_STATES
    ]


def _is_explicitly_negative(line: str) -> bool:
    return bool(_NEGATIVE_WORD.search(line))


def _has_consent_context(lines: list[str], zero_based_line_number: int) -> bool:
    start = max(0, zero_based_line_number - 3)
    end = min(len(lines), zero_based_line_number + 4)
    context = " ".join(lines[start:end]).replace(LIVE_INSTALL_COMMAND, "")
    return bool(_CONSENT_WORD.search(context))


def main() -> int:
    repository_root = Path(__file__).resolve().parent.parent
    findings = check_repository(repository_root)
    if findings:
        print("Verification policy consistency: FAIL")
        for finding in findings:
            print(f"- {finding.render()}")
        return 1
    print("Verification policy consistency: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
