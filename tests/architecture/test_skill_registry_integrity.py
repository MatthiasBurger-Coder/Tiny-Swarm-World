import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPOSITORY_ROOT / ".agents" / "skills"
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "documentation"
    / "process"
    / "skills"
    / "audit"
    / "skill-registry.json"
)


class TestSkillRegistryIntegrity(unittest.TestCase):
    def test_all_project_skills_have_matching_discovery_metadata(self):
        registry = _registry()
        skill_files = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
        invalid = []
        names = []
        for skill_file in skill_files:
            frontmatter = re.match(
                r"^---\n(?P<metadata>.*?)\n---\n",
                skill_file.read_text(encoding="utf-8"),
                re.DOTALL,
            )
            if frontmatter is None:
                invalid.append(skill_file.parent.name)
                continue
            name = re.search(r"^name:\s*(.+)$", frontmatter["metadata"], re.MULTILINE)
            description = re.search(
                r"^description:\s*(.+)$",
                frontmatter["metadata"],
                re.MULTILINE,
            )
            if (
                name is None
                or description is None
                or name.group(1).strip() != skill_file.parent.name
                or not description.group(1).strip().strip('"')
            ):
                invalid.append(skill_file.parent.name)
                continue
            names.append(name.group(1).strip())

        self.assertEqual(invalid, [])
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            len(skill_files),
            registry["counts"]["project_skill_entrypoints_with_valid_metadata"],
        )

    def test_governing_hash_cache_matches_repository_files(self):
        registry = _registry()
        mismatches = {}
        for relative_path, expected_hash in registry["governing_hashes"].items():
            content = (REPOSITORY_ROOT / relative_path).read_bytes()
            actual_hash = hashlib.sha256(content).hexdigest().upper()
            if actual_hash != expected_hash:
                mismatches[relative_path] = {
                    "expected": expected_hash,
                    "actual": actual_hash,
                }

        self.assertEqual(mismatches, {})

    def test_routing_respects_tiny_swarm_world_project_identity(self):
        routing = (
            REPOSITORY_ROOT / ".agents" / "orchestrator" / "routing-rules.md"
        ).read_text(encoding="utf-8")
        workflow_prompt = (
            REPOSITORY_ROOT / ".agents" / "prompts" / "workflow-create.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn("roles/senior-analysis-storage-architect.md", routing)
        self.assertNotIn("roles/senior-joern-cpg-specialist.md", routing)
        self.assertNotIn("must use five mandatory roles", workflow_prompt.lower())
        self.assertIn("Console/status UI reviewer", workflow_prompt)

    def test_registry_required_skills_have_discoverable_entrypoints(self):
        registry = _registry()
        discovered = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}
        missing = sorted(set(registry["required_tiny_swarm_world_skills"]) - discovered)
        self.assertEqual(missing, [])

    def test_registry_separates_project_and_reusable_skill_counts(self):
        counts = _registry()["counts"]
        self.assertEqual(counts["project_skill_entrypoints"], 132)
        self.assertEqual(counts["project_skill_entrypoints_with_valid_metadata"], 132)
        self.assertEqual(counts["codex_skill_entrypoints"], 6)


def _registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
