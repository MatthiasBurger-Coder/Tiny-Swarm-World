"""Audit project skill discovery and registry invariants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
REGISTRY = ROOT / "documentation/process/skills/audit/skill-registry.json"


def classify_skill(name: str) -> str:
    """Return the stable governance class for a discoverable project skill."""
    if name in {"issue-completion-auditor", "audit-evidence-manager", "traceability-engineer"}:
        return "governance"
    if any(token in name for token in ("security", "owasp", "isms", "supply-chain", "secrets")):
        return "security"
    if any(token in name for token in ("docker", "swarm", "kubernetes", "incus", "registry", "nexus", "jenkins", "sonarqube", "portainer", "bootstrap", "deployment", "devops", "image-", "network", "linux-host")):
        return "runtime"
    if any(token in name for token in ("test", "tdd", "bdd", "quality", "junit", "archunit", "acceptance")):
        return "quality"
    if any(token in name for token in ("frontend", "console", "terminal", "ux")):
        return "ui"
    if any(token in name for token in ("grpc", "protobuf", "contract")):
        return "contracts"
    if any(token in name for token in ("workflow", "orchestration", "execution", "s3d", "swarm-coordination")):
        return "orchestration"
    return "architecture"


def _frontmatter(path: Path) -> dict[str, str] | None:
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    if match is None:
        return None
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def audit() -> dict[str, object]:
    files = sorted(SKILLS.glob("*/SKILL.md"))
    findings: list[dict[str, str]] = []
    names: list[str] = []
    for path in files:
        metadata = _frontmatter(path)
        if metadata is None:
            findings.append({"code": "MISSING_FRONTMATTER", "skill": path.parent.name})
            continue
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if name != path.parent.name or not description:
            findings.append({"code": "INVALID_DISCOVERY_METADATA", "skill": path.parent.name})
        names.append(name)
    duplicates = sorted({name for name in names if names.count(name) > 1})
    findings.extend({"code": "DUPLICATE_SKILL_NAME", "skill": name} for name in duplicates)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    expected = registry["counts"]["project_skill_entrypoints"]
    if expected != len(files):
        findings.append({"code": "REGISTRY_COUNT_MISMATCH", "expected": str(expected), "actual": str(len(files))})
    classifications = {path.parent.name: classify_skill(path.parent.name) for path in files}
    return {
        "result": "failed" if findings else "passed",
        "project_skill_entrypoints": len(files),
        "findings": findings,
        "classifications": classifications,
    }


def audit_activation(selected_skills: set[str], relevant_skills: set[str]) -> dict[str, object]:
    """Reject activation of skills without evidence of slice relevance."""
    unnecessary = sorted(selected_skills - relevant_skills)
    return {
        "result": "failed" if unnecessary else "passed",
        "activated_count": len(selected_skills),
        "rejected_count": 0,
        "findings": [
            {"code": "UNNECESSARY_SKILL_ACTIVATION", "skill": skill}
            for skill in unnecessary
        ],
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(1 if result["result"] == "failed" else 0)
