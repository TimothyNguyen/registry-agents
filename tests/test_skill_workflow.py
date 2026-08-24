import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "skill_workflow.py"
SPEC = importlib.util.spec_from_file_location("skill_workflow", SCRIPT)
assert SPEC and SPEC.loader
skill_workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = skill_workflow
SPEC.loader.exec_module(skill_workflow)


class SkillWorkflowTests(unittest.TestCase):
    def test_discovers_every_skill_manifest_without_hardcoded_names(self):
        skills = skill_workflow.discover_skills(ROOT / "manifests" / "resources" / "skills")

        self.assertEqual(len(skills), 9)
        self.assertEqual([skill.name for skill in skills], sorted(skill.name for skill in skills))
        self.assertEqual(
            {skill.name for skill in skills},
            {
                "book-to-skill",
                "commit",
                "context-saver",
                "diagram-design",
                "review",
                "systematic-debugging",
                "test",
                "using-agent-skills",
                "verification-before-completion",
            },
        )

    def test_validates_skill_manifest_as_standalone_artifact(self):
        skill = skill_workflow.discover_skills(ROOT / "manifests" / "resources" / "skills")[0]

        result = skill_workflow.validate_skill(skill)

        self.assertTrue(result.ok, result.errors)
        self.assertTrue(result.body.startswith("---\n"))
        self.assertIn("\n---\n", result.body)

    def test_builds_independent_registry_commands(self):
        skill = skill_workflow.SkillManifest(
            name="example",
            path=ROOT / "manifests" / "resources" / "skills" / "example.yaml",
            text="",
        )

        commands = skill_workflow.commands_for(skill, target="claude", scope="project")

        self.assertEqual(
            commands,
            [
                ["tregistry", "apply", "-f", str(skill.path)],
                [
                    "tregistry",
                    "install",
                    "skill",
                    "example",
                    "--target",
                    "claude",
                    "--scope",
                    "project",
                ],
            ],
        )

    def test_selects_requested_skills_without_static_registry(self):
        skills = skill_workflow.discover_skills(ROOT / "manifests" / "resources" / "skills")

        selected = skill_workflow.select_skills(skills, ["review", "test"])

        self.assertEqual([skill.name for skill in selected], ["review", "test"])

        with self.assertRaises(ValueError):
            skill_workflow.select_skills(skills, ["missing-skill"])


if __name__ == "__main__":
    unittest.main()
