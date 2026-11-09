"""Tests that each skill hands its agent the content rules, except the screener.

The defaults live in one file, skills/resume/content-rules.md. Each agent
that writes content or checks a letter gets its path in the dispatch as
`defaults:`, and the content folder's CLAUDE.md as `own-rules:`. The
screener gets neither: it reads the page cold, as a recruiter who does not
know the writer's rules. These break if a skill and its agent disagree on
the dispatch block, the two keys are dropped or moved, a skill points at a
rules file that is not there, or the rules are handed to the screener.
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
RULES = PLUGIN / "skills" / "resume" / "content-rules.md"
RULES_PATH = re.compile(
    r"\$\{(CLAUDE_PLUGIN_ROOT|CLAUDE_SKILL_DIR)\}(/[^\s\"'`]*content-rules\.md)"
)
SCREENER = ("skills/resume-review/SKILL.md", "agents/screener.md")
RULES_KEY = re.compile(r"\b(defaults|own-rules):")
PAIRS = [
    ("skills/resume-review/SKILL.md", "agents/screener.md",
     "    content: <absolute path to the YAML>",
     ["content", "pdf", "posting", "today"]),
    ("skills/resume/SKILL.md", "agents/resume-writer.md",
     "    draft: <absolute path to the draft YAML>",
     ["draft", "role", "facts", "defaults", "own-rules"]),
    ("skills/cover-letter/SKILL.md", "agents/letter-reader.md",
     "    letter: <absolute path to the extracted letter text, nothing else in it>",
     ["letter", "application", "posting", "resume", "knowledge",
      "defaults", "own-rules", "bar", "words", "today"]),
]


def dispatch_block(text, first_line):
    """The contiguous four-space-indented lines from first_line on, or []."""
    lines = text.splitlines()
    if first_line not in lines:
        return []
    block = []
    for line in lines[lines.index(first_line):]:
        if not line.startswith("    "):
            break
        block.append(line)
    return block


def read(relative):
    return (PLUGIN / relative).read_text(encoding="utf-8")


class RulesDispatchTests(unittest.TestCase):
    def test_each_skill_and_its_agent_share_one_block(self):
        for skill, agent, first_line, _ in PAIRS:
            with self.subTest(skill=skill):
                block = dispatch_block(read(skill), first_line)
                self.assertNotEqual(block, [])
                self.assertEqual(block, dispatch_block(read(agent), first_line))

    def test_each_block_has_its_keys_in_order(self):
        for skill, _, first_line, keys in PAIRS:
            with self.subTest(skill=skill):
                block = dispatch_block(read(skill), first_line)
                self.assertEqual([line.strip().split(":", 1)[0] for line in block], keys)

    def test_the_screener_is_not_given_the_rules(self):
        for relative in SCREENER:
            with self.subTest(file=relative):
                text = read(relative)
                self.assertEqual(RULES_KEY.findall(text), [])
                self.assertEqual(RULES_PATH.findall(text), [])

    def test_each_rules_reader_names_both_keys(self):
        for skill, agent, _, _ in PAIRS:
            if (skill, agent) == SCREENER:
                continue
            for relative in (skill, agent):
                with self.subTest(file=relative):
                    self.assertEqual(
                        sorted(set(RULES_KEY.findall(read(relative)))),
                        ["defaults", "own-rules"],
                    )

    def test_each_skill_names_the_rules_file_that_exists(self):
        for skill, agent, _, _ in PAIRS:
            if (skill, agent) == SCREENER:
                continue
            with self.subTest(skill=skill):
                found = RULES_PATH.findall(read(skill))
                self.assertNotEqual(found, [])
                skill_dir = (PLUGIN / skill).parent
                for variable, path in found:
                    base = PLUGIN if variable == "CLAUDE_PLUGIN_ROOT" else skill_dir
                    self.assertEqual((base / path.lstrip("/")).resolve(), RULES.resolve())


if __name__ == "__main__":
    unittest.main()
