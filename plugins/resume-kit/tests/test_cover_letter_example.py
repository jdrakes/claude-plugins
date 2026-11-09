"""Tests for the cover-letter skill's invented example folder.

The skill finds a base letter by the glob `applications/*base*-cover-letter.md`
and points a user with no base of their own at this one, and the letter
reader traces claims against this KNOWLEDGE.md. These tests break if the base
is renamed out of the glob, its signature stops parsing, its header loses the
"Use when" line, its sections are reordered, or KNOWLEDGE.md drops a role or
the "Not on file" list.
"""
import importlib.machinery
import importlib.util
import re
import unittest
from pathlib import Path

import yaml

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "skills" / "cover-letter" / "bin" / "build-letter"
loader = importlib.machinery.SourceFileLoader("build_letter", str(SCRIPT))
spec = importlib.util.spec_from_loader("build_letter", loader)
build_letter = importlib.util.module_from_spec(spec)
loader.exec_module(build_letter)

EXAMPLES = PLUGIN / "skills" / "cover-letter" / "examples"
BASE = EXAMPLES / "applications" / "2026-01-12-base-backend-engineer-cover-letter.md"
SAMPLE_RESUME = PLUGIN / "skills" / "resume" / "examples" / "sample-resume.yaml"


class BaseLetterTests(unittest.TestCase):
    def setUp(self):
        self.text = BASE.read_text(encoding="utf-8")

    def test_the_lookup_glob_finds_exactly_the_one_base(self):
        self.assertEqual(sorted(EXAMPLES.glob("applications/*base*-cover-letter.md")), [BASE])

    def test_the_letter_parses_with_the_example_signature(self):
        section, error = build_letter.letter_section(self.text)
        self.assertIsNone(error)
        payload, error = build_letter.letter_payload(section)
        self.assertIsNone(error)
        self.assertEqual(payload["name"], "Alex Rivera")
        self.assertEqual(payload["contact"], ["alex.rivera@example.com", "555-0142"])

    def test_the_header_says_when_the_base_applies(self):
        header = self.text.split("\n## Letter\n", 1)[0]
        self.assertIn("Use when", header)

    def test_letter_rulings_and_evidence_come_in_that_order(self):
        headings = re.findall(r"^## (.+)$", self.text, re.M)
        self.assertEqual(headings, ["Letter", "Rulings", "Evidence"])


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        text = (EXAMPLES / "KNOWLEDGE.md").read_text(encoding="utf-8")
        self.headings = re.findall(r"^## (.+)$", text, re.M)

    def test_it_has_a_not_on_file_section(self):
        self.assertIn("Not on file", self.headings)

    def test_every_role_in_the_sample_resume_has_a_section(self):
        resume = yaml.safe_load(SAMPLE_RESUME.read_text(encoding="utf-8"))
        companies = [role["company"] for role in resume["experience"]]
        self.assertEqual(companies, ["Northwind Systems", "Cobalt Harbor", "Pinegrove Labs"])
        for company in companies:
            with self.subTest(company=company):
                self.assertTrue(any(heading.startswith(company) for heading in self.headings))


if __name__ == "__main__":
    unittest.main()
