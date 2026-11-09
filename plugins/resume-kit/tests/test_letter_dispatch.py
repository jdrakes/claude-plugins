"""Tests that the cover-letter skill and the letter-reader agent agree.

The skill sends the dispatch block; the agent documents what it receives.
These tests break if the block is edited in one file and not the other, a
key is added, dropped or reordered, the agent gains a write tool, the skill
names the agent without its plugin prefix (which fails with "Agent type not
found"), or the skill points at a plugin file that has been moved or
renamed.
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SKILL = PLUGIN / "skills" / "cover-letter" / "SKILL.md"
AGENT = PLUGIN / "agents" / "letter-reader.md"
FIRST_LINE = "    letter: <absolute path to the extracted letter text, nothing else in it>"
PLUGIN_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}(/[^\s\"'`]+)")


def dispatch_block(text):
    """The contiguous four-space-indented lines from the `letter:` line on.

    Empty when the `letter:` line is absent, so a missing block fails the
    comparison rather than raising.
    """
    lines = text.splitlines()
    if FIRST_LINE not in lines:
        return []
    block = []
    for line in lines[lines.index(FIRST_LINE):]:
        if not line.startswith("    "):
            break
        block.append(line)
    return block


def frontmatter(text):
    """The lines between the opening and closing `---`."""
    lines = text.splitlines()
    return lines[1:lines.index("---", 1)]


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")
        self.agent = AGENT.read_text(encoding="utf-8")

    def test_the_block_is_identical_in_skill_and_agent(self):
        self.assertNotEqual(dispatch_block(self.skill), [])
        self.assertEqual(dispatch_block(self.skill), dispatch_block(self.agent))

    def test_the_block_has_the_eight_keys_in_order(self):
        keys = [line.strip().split(":", 1)[0] for line in dispatch_block(self.skill)]
        self.assertEqual(
            keys,
            ["letter", "application", "posting", "resume", "knowledge", "bar", "words", "today"],
        )

    def test_the_agent_is_read_only(self):
        self.assertIn("tools: Read, Grep, Glob", frontmatter(self.agent))

    def test_the_skill_dispatches_by_the_plugin_qualified_name(self):
        self.assertIn("subagent_type: resume-kit:letter-reader", self.skill)
        self.assertNotIn("subagent_type: letter-reader", self.skill)

    def test_every_plugin_path_the_skill_names_exists(self):
        paths = PLUGIN_PATH.findall(self.skill)
        self.assertIn("/skills/cover-letter/bin/build-letter", paths)
        self.assertIn(
            "/skills/cover-letter/examples/applications/2026-01-12-base-backend-engineer-cover-letter.md",
            paths,
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue((PLUGIN / path.lstrip("/")).exists())


class DispatchBlockHelperTests(unittest.TestCase):
    def test_the_block_stops_at_the_first_unindented_line(self):
        text = "intro\n" + FIRST_LINE + "\n    today: <YYYY-MM-DD>\n\n    later: x\n"
        self.assertEqual(dispatch_block(text), [FIRST_LINE, "    today: <YYYY-MM-DD>"])

    def test_a_text_without_the_letter_line_has_no_block(self):
        self.assertEqual(dispatch_block("    today: <YYYY-MM-DD>\n"), [])


if __name__ == "__main__":
    unittest.main()
